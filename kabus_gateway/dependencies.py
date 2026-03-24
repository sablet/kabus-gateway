from fastapi import Request

from kabus_gateway.client import KabusClient


def get_client(request: Request) -> KabusClient:
    return request.app.state.client  # type: ignore[no-any-return]
