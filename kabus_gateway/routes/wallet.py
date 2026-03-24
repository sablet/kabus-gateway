from fastapi import APIRouter, Request, Response

from kabus_gateway.dependencies import get_client

router = APIRouter()


@router.get("/wallet/cash")
async def wallet_cash(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", "/wallet/cash")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/cash/{symbol}")
async def wallet_cash_symbol(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/wallet/cash/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/margin")
async def wallet_margin(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", "/wallet/margin")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/margin/{symbol}")
async def wallet_margin_symbol(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/wallet/margin/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/future")
async def wallet_future(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", "/wallet/future")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/future/{symbol}")
async def wallet_future_symbol(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/wallet/future/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/option")
async def wallet_option(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", "/wallet/option")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/wallet/option/{symbol}")
async def wallet_option_symbol(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/wallet/option/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
