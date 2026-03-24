import asyncio

import httpx


class TokenManager:
    def __init__(self, client: httpx.AsyncClient, base_url: str, api_password: str) -> None:
        self._client = client
        self._base_url = base_url
        self._api_password = api_password
        self._token: str | None = None
        self._lock = asyncio.Lock()

    async def get_token(self) -> str:
        if self._token is None:
            await self._issue_token()
        return self._token  # type: ignore[return-value]

    async def refresh_token(self) -> str:
        async with self._lock:
            await self._issue_token()
            return self._token  # type: ignore[return-value]

    async def _issue_token(self) -> None:
        resp = await self._client.post(
            f"{self._base_url}/token",
            json={"APIPassword": self._api_password},
        )
        resp.raise_for_status()
        self._token = resp.json()["Token"]
