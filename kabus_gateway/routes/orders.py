from fastapi import APIRouter, Request, Response

from kabus_gateway.dependencies import get_client

router = APIRouter()


@router.post("/sendorder")
async def send_order(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("POST", "/sendorder", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.post("/sendorder/future")
async def send_order_future(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("POST", "/sendorder/future", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.post("/sendorder/option")
async def send_order_option(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("POST", "/sendorder/option", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.put("/cancelorder")
async def cancel_order(request: Request) -> Response:
    client = get_client(request)
    body = await request.json()
    resp = await client.request("PUT", "/cancelorder", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
