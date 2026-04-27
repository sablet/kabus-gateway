"""ranking API を平日 9:00-15:00 にポーリングし、JSONL ログに追記する.

9:00 以降、データが実際に提供開始されるまで短間隔でプローブし、
データ確認後に1分間隔のポーリングを開始する。
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import os

import httpx
import websockets
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

JST = ZoneInfo("Asia/Tokyo")
GATEWAY_URL = os.environ["GATEWAY_URL"]
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "output" / "ranking"
INTERVAL_SEC = 60
PROBE_INTERVAL_SEC = 10

DEFAULT_MARKETS = ["TP", "TS", "TG"]
VALID_MARKETS = ["ALL", "T", "TP", "TS", "TG", "M", "FK", "S"]

MARKET_OPEN = time(9, 0)
MARKET_CLOSE = time(15, 1)


def is_trading_hours(now: datetime) -> bool:
    """平日 9:00-15:00 (JST) かどうか."""
    if now.weekday() >= 5:  # 土日
        return False
    return MARKET_OPEN <= now.time() < MARKET_CLOSE


def log_path(now: datetime) -> Path:
    """日付ごとのログファイルパス."""
    return LOG_DIR / f"ranking_{now.strftime('%Y%m%d')}.jsonl"


async def fetch(client: httpx.AsyncClient, params: dict[str, str], now: datetime) -> dict:
    try:
        resp = await client.get(f"{GATEWAY_URL}/ranking", params=params, timeout=10)
        return {
            "ts": now.isoformat(),
            "status": resp.status_code,
            "params": params,
            "body": resp.json() if resp.status_code == 200 else resp.text,
        }
    except Exception as e:
        return {
            "ts": now.isoformat(),
            "status": -1,
            "params": params,
            "error": str(e),
        }


def write_record(record: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def format_status(record: dict) -> str:
    status = record.get("status")
    div = record.get("params", {}).get("ExchangeDivision", "")
    if status == 200 and isinstance(record.get("body"), dict):
        items = record["body"].get("Ranking") or []
        return f"{div}={len(items)}"
    return f"{div}=err({status})"


async def poll(client: httpx.AsyncClient, markets: list[str]) -> None:
    """指定市場の値上がり・値下がりを取得し、1レコードにまとめてログ."""
    now = datetime.now(JST)
    up_results = []
    down_results = []
    for market in markets:
        up_results.append(await fetch(client, {"Type": "1", "ExchangeDivision": market}, now))
        down_results.append(await fetch(client, {"Type": "2", "ExchangeDivision": market}, now))

    up_parts = [format_status(r) for r in up_results]
    down_parts = [format_status(r) for r in down_results]
    print(f"[{now.strftime('%H:%M:%S')}] up={' '.join(up_parts)} down={' '.join(down_parts)}")

    def to_map(results: list[dict]) -> dict:
        return {
            r["params"]["ExchangeDivision"]: r.get("body") if r["status"] == 200 else {"error": r.get("error", r.get("body"))}
            for r in results
        }

    merged = {
        "ts": now.isoformat(),
        "up": to_map(up_results),
        "down": to_map(down_results),
    }
    write_record(merged, log_path(now))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ranking API poller")
    parser.add_argument(
        "--markets",
        nargs="+",
        default=DEFAULT_MARKETS,
        choices=VALID_MARKETS,
        help=f"取得する市場 (default: {' '.join(DEFAULT_MARKETS)})",
    )
    return parser.parse_args()


async def ws_keepalive() -> None:
    """WebSocket 接続を維持し、状態変化をログに記録する."""
    connected = False
    while True:
        try:
            ws_url = GATEWAY_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
            async for ws in websockets.connect(ws_url):
                if not connected:
                    now = datetime.now(JST)
                    write_record({"ts": now.isoformat(), "ws": "connected"}, log_path(now))
                    print(f"[{now.strftime('%H:%M:%S')}] ws connected")
                    connected = True
                try:
                    async for _ in ws:
                        pass  # 受信データは破棄
                except websockets.ConnectionClosed:
                    now = datetime.now(JST)
                    write_record({"ts": now.isoformat(), "ws": "disconnected"}, log_path(now))
                    print(f"[{now.strftime('%H:%M:%S')}] ws disconnected, reconnecting...")
                    connected = False
        except Exception as e:
            now = datetime.now(JST)
            write_record({"ts": now.isoformat(), "ws": "error", "error": str(e)}, log_path(now))
            print(f"[{now.strftime('%H:%M:%S')}] ws error: {e}")
            connected = False
            await asyncio.sleep(5)


def has_ranking_data(record: dict) -> bool:
    """レスポンスに実データ（Ranking 配列が非空）が含まれるか."""
    if record.get("status") != 200:
        return False
    body = record.get("body")
    if not isinstance(body, dict):
        return False
    items = body.get("Ranking") or []
    return len(items) > 0


async def wait_for_data(client: httpx.AsyncClient, markets: list[str]) -> None:
    """9:00 以降、最初の市場でデータが返るまでプローブする."""
    probe_market = markets[0]
    params = {"Type": "1", "ExchangeDivision": probe_market}
    print(f"probing {probe_market} for data availability (every {PROBE_INTERVAL_SEC}s)...")

    while True:
        now = datetime.now(JST)
        if not is_trading_hours(now):
            return  # 取引時間外に戻ったら抜ける
        record = await fetch(client, params, now)
        if has_ranking_data(record):
            print(f"[{now.strftime('%H:%M:%S')}] data available, starting poll loop")
            return
        print(f"[{now.strftime('%H:%M:%S')}] {probe_market} no data yet (status={record.get('status')})")
        await asyncio.sleep(PROBE_INTERVAL_SEC)


async def poll_loop(markets: list[str]) -> None:
    """ranking API のポーリングループ.

    取引時間に入ったらまずデータ提供開始を待ち、確認後に1分ポーリングを開始する。
    """
    async with httpx.AsyncClient() as client:
        while True:
            now = datetime.now(JST)
            if not is_trading_hours(now):
                await asyncio.sleep(10)
                continue

            await wait_for_data(client, markets)

            while is_trading_hours(datetime.now(JST)):
                now = datetime.now(JST)
                await poll(client, markets)
                elapsed = (datetime.now(JST) - now).total_seconds()
                await asyncio.sleep(max(0, INTERVAL_SEC - elapsed))


async def main() -> None:
    args = parse_args()
    markets: list[str] = args.markets

    print(f"ranking_collector started  url={GATEWAY_URL}")
    print(f"log_dir={LOG_DIR}  markets={markets}  interval={INTERVAL_SEC}s")

    await asyncio.gather(
        ws_keepalive(),
        poll_loop(markets),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)
