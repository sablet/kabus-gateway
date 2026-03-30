import asyncio
import logging

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class WsBroadcaster:
    def __init__(self, upstream_url: str) -> None:
        self._upstream_url = upstream_url
        self._clients: set[WebSocket] = set()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._relay_loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)
        try:
            while True:
                await ws.receive_text()
        except WebSocketDisconnect:
            self._clients.discard(ws)

    async def _relay_loop(self) -> None:
        _active = False
        _backoff = 1
        while True:
            try:
                async with websockets.connect(self._upstream_url) as upstream:
                    async for message in upstream:
                        if not _active:
                            logger.info("Upstream WebSocket connected: %s", self._upstream_url)
                            _active = True
                        _backoff = 1
                        dead: set[WebSocket] = set()
                        for client in self._clients:
                            try:
                                await client.send_text(message if isinstance(message, str) else message.decode())
                            except Exception:
                                dead.add(client)
                        self._clients -= dead
            except asyncio.CancelledError:
                raise
            except Exception:
                if _active:
                    logger.warning("Upstream WebSocket disconnected, reconnecting in background...")
                    _active = False
                await asyncio.sleep(_backoff)
                _backoff = min(_backoff * 2, 60)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    broadcaster: WsBroadcaster = ws.app.state.broadcaster
    await broadcaster.connect(ws)
