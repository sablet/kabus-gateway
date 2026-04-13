import httpx

from kabus_gateway.auth import TokenManager


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

        if resp.status_code == 401:
            new_token = await self._token_manager.refresh_token()
            headers["X-API-KEY"] = new_token
            resp = await self._http.request(method, path, **kwargs)

        return resp

    async def aclose(self) -> None:
        await self._http.aclose()
