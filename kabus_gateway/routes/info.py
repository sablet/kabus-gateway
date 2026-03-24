from fastapi import APIRouter, Request, Response

from kabus_gateway.dependencies import get_client

router = APIRouter()


@router.get("/board/{symbol}")
async def board(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/board/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/symbol/{symbol}")
async def symbol_info(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/symbol/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/orders")
async def orders(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/orders", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/positions")
async def positions(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/positions", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/symbolname/future")
async def symbolname_future(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/symbolname/future", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/symbolname/option")
async def symbolname_option(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/symbolname/option", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/symbolname/minioptionweekly")
async def symbolname_minioptionweekly(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/symbolname/minioptionweekly", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/ranking")
async def ranking(request: Request) -> Response:
    client = get_client(request)
    params = dict(request.query_params)
    resp = await client.request("GET", "/ranking", params=params)
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/exchange/{symbol}")
async def exchange(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/exchange/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/regulations/{symbol}")
async def regulations(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/regulations/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/primaryexchange/{symbol}")
async def primaryexchange(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/primaryexchange/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/apisoftlimit")
async def apisoftlimit(request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", "/apisoftlimit")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")


@router.get("/margin/marginpremium/{symbol}")
async def marginpremium(symbol: str, request: Request) -> Response:
    client = get_client(request)
    resp = await client.request("GET", f"/margin/marginpremium/{symbol}")
    return Response(content=resp.content, status_code=resp.status_code, media_type="application/json")
