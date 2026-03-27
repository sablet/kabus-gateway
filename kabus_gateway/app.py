import logging
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

from kabus_gateway.auth import TokenManager
from kabus_gateway.client import KabusClient
from kabus_gateway.routes import info, orders, register, wallet, ws
from kabus_gateway.routes.ws import WsBroadcaster


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    load_dotenv()

    api_password = os.environ["KABUS_API_PASSWORD"]
    base_url = os.environ.get("KABUS_BASE_URL", "http://localhost:18080/kabusapi")

    http_client = httpx.AsyncClient()
    token_mgr = TokenManager(http_client, base_url, api_password)
    client = KabusClient(base_url, token_mgr)

    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/websocket"
    broadcaster = WsBroadcaster(ws_url)

    app.state.client = client
    app.state.broadcaster = broadcaster

    await broadcaster.start()

    yield

    await broadcaster.stop()
    await client.aclose()
    await http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(title="kabus-gateway", lifespan=lifespan)

    @app.get("/")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(info.router)
    app.include_router(wallet.router)
    app.include_router(orders.router)
    app.include_router(register.router)
    app.include_router(ws.router)
    return app
