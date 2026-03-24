from fastapi import APIRouter, Request, Response

from kabus_gateway.dependencies import get_client

router = APIRouter()


@router.put("/register")
async def register(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("PUT", "/register", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.put("/unregister")
async def unregister(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("PUT", "/unregister", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.put("/unregister/all")
async def unregister_all(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("PUT", "/unregister/all")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
