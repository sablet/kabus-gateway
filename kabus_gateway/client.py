import asyncio
import logging

import httpx

from kabus_gateway.auth import TokenManager

logger = logging.getLogger(__name__)

# トークン失効・認証エラー（リフレッシュで回復可能）
_TOKEN_EXPIRED_CODES = {
    4001007,  # ログイン認証エラー
    4001009,  # APIキー不一致
    4001017,  # ログイン認証エラー（kabuS未ログイン）
}

# 銘柄登録上限超過（全解除で回復可能）
_REGISTER_FULL_CODES = {
    4001018,  # 銘柄が登録できませんでした
    4001019,  # 一部の銘柄が登録できませんでした
    4002006,  # レジスト数エラー
}

# レート制限: 情報系10件/秒、発注系5件/秒。20%バッファで余裕を持たせる。
_INFO_INTERVAL = 0.12  # 10件/秒 → 120ms間隔 (≈8.3件/秒)
_ORDER_INTERVAL = 0.25  # 5件/秒 → 250ms間隔 (4件/秒)

_RETRY_429_MAX = 3
_RETRY_429_BASE_SEC = 1.0


def _get_error_code(resp: httpx.Response) -> int | None:
    if resp.status_code < 400:
        return None
    try:
        return resp.json().get("Code")
    except Exception:
        return None


class _AsyncRateLimiter:
    """呼び出し間隔を min_interval 秒以上に保つ非同期レートリミッター."""

    __slots__ = ("_min_interval", "_last", "_lock")

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            loop = asyncio.get_event_loop()
            gap = self._min_interval - (loop.time() - self._last)
            if gap > 0:
                await asyncio.sleep(gap)
            self._last = asyncio.get_event_loop().time()


class KabusClient:
    def __init__(self, base_url: str, token_manager: TokenManager) -> None:
        self._base_url = base_url
        self._token_manager = token_manager
        self._http = httpx.AsyncClient(base_url=base_url, timeout=15.0)
        self._info_limiter = _AsyncRateLimiter(_INFO_INTERVAL)
        self._order_limiter = _AsyncRateLimiter(_ORDER_INTERVAL)

    async def request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        token = await self._token_manager.get_token()
        headers = dict(kwargs.pop("headers", None) or {})  # type: ignore[arg-type]
        headers["X-API-KEY"] = token
        kwargs["headers"] = headers

        resp = await self._send(method, path, **kwargs)

        code = _get_error_code(resp)

        if code in _TOKEN_EXPIRED_CODES:
            logger.warning("Token expired (Code=%s), refreshing and retrying: %s %s", code, method, path)
            new_token = await self._token_manager.refresh_token()
            headers["X-API-KEY"] = new_token
            resp = await self._send(method, path, **kwargs)

        if code in _REGISTER_FULL_CODES:
            logger.warning("Register limit exceeded, unregistering all and retrying: %s %s", method, path)
            await self._unregister_all(headers["X-API-KEY"])
            resp = await self._send(method, path, **kwargs)

        return resp

    async def _send(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        limiter = self._order_limiter if method == "POST" else self._info_limiter
        await limiter.acquire()
        resp = await self._http.request(method, path, **kwargs)
        if resp.status_code == 429:
            resp = await self._retry_429(method, path, **kwargs)
        return resp

    async def _retry_429(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        for attempt in range(_RETRY_429_MAX):
            wait = _RETRY_429_BASE_SEC * (2 ** attempt)
            logger.warning("%s %s 429 rate-limited, retry in %.1fs (%d/%d)", method, path, wait, attempt + 1, _RETRY_429_MAX)
            await asyncio.sleep(wait)
            limiter = self._order_limiter if method == "POST" else self._info_limiter
            await limiter.acquire()
            resp = await self._http.request(method, path, **kwargs)
            if resp.status_code != 429:
                return resp
        return resp  # 最終試行の結果をそのまま返す

    async def _unregister_all(self, token: str) -> None:
        await self._info_limiter.acquire()
        resp = await self._http.request(
            "PUT", "/unregister/all", headers={"X-API-KEY": token},
        )
        if resp.status_code == 200:
            logger.info("Unregistered all symbols successfully")
        else:
            logger.error("Failed to unregister all symbols: %s %s", resp.status_code, resp.text)

    async def aclose(self) -> None:
        await self._http.aclose()
