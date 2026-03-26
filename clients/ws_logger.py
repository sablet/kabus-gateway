"""WebSocket に接続し、受信データを JSONL ログに追記する確認用スクリプト."""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import os

import websockets
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

JST = ZoneInfo("Asia/Tokyo")
GATEWAY_URL = os.environ["GATEWAY_URL"]
WS_URL = GATEWAY_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws"
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "output" / "ws"


def log_path(now: datetime) -> Path:
    return LOG_DIR / f"ws_{now.strftime('%Y%m%d')}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WebSocket logger")
    parser.add_argument(
        "--suppress-unchanged",
        action="store_true",
        help="価格変動がないメッセージのコンソール出力を抑制（ログ記録は常に行う）",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    print(f"ws_logger connecting to {WS_URL} ...")
    if args.suppress_unchanged:
        print("suppress-unchanged: ON (価格変動時のみコンソール表示)")

    # symbol -> 直近の CurrentPrice
    last_price: dict[str, object] = {}

    async for ws in websockets.connect(WS_URL):
        print("connected. waiting for messages...")
        try:
            async for raw in ws:
                now = datetime.now(JST)
                try:
                    body = json.loads(raw)
                except json.JSONDecodeError:
                    body = raw

                record = {"ts": now.isoformat(), "body": body}
                path = log_path(now)
                with path.open("a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                symbol = body.get("Symbol", "") if isinstance(body, dict) else ""
                name = body.get("SymbolName", "") if isinstance(body, dict) else ""
                price = body.get("CurrentPrice") if isinstance(body, dict) else None

                if args.suppress_unchanged:
                    prev = last_price.get(symbol)
                    last_price[symbol] = price
                    if prev == price:
                        continue

                print(f"[{now.strftime('%H:%M:%S')}] {symbol} {name} {price}")
        except websockets.ConnectionClosed:
            print("disconnected, reconnecting...")
            continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)
