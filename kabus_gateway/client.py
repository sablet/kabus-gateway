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


def _get_error_code(resp: httpx.Response) -> int | None:
    if resp.status_code < 400:
        return None
    try:
        return resp.json().get("Code")
    except Exception:
        return None


class KabusClient:
    def __init__(self, base_url: str, token_manager: TokenManager) -> None:
        self._base_url = base_url
        self._token_manager = token_manager
        self._http = httpx.AsyncClient(base_url=base_url, timeout=15.0)

    async def request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        token = await self._token_manager.get_token()
        headers = dict(kwargs.pop("headers", None) or {})  # type: ignore[arg-type]
        headers["X-API-KEY"] = token
        kwargs["headers"] = headers

        resp = await self._http.request(method, path, **kwargs)

        code = _get_error_code(resp)

        if code in _TOKEN_EXPIRED_CODES:
            logger.warning("Token expired (Code=%s), refreshing and retrying: %s %s", code, method, path)
            new_token = await self._token_manager.refresh_token()
            headers["X-API-KEY"] = new_token
            resp = await self._http.request(method, path, **kwargs)

        if code in _REGISTER_FULL_CODES:
            logger.warning("Register limit exceeded, unregistering all and retrying: %s %s", method, path)
            await self._unregister_all(headers["X-API-KEY"])
            resp = await self._http.request(method, path, **kwargs)

        return resp

    async def _unregister_all(self, token: str) -> None:
        resp = await self._http.request(
            "PUT", "/unregister/all", headers={"X-API-KEY": token},
        )
        if resp.status_code == 200:
            logger.info("Unregistered all symbols successfully")
        else:
            logger.error("Failed to unregister all symbols: %s %s", resp.status_code, resp.text)

    async def aclose(self) -> None:
        await self._http.aclose()
