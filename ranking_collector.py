"""ranking API を平日 9:00-15:00 に毎分ポーリングし、JSONL ログに追記する."""

import asyncio
import json
import sys
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

JST = ZoneInfo("Asia/Tokyo")
GATEWAY_URL = "http://192.168.11.20:18088/ranking"
LOG_DIR = Path(__file__).parent / "output" / "ranking"
INTERVAL_SEC = 60

RANKING_TYPES: list[dict[str, str]] = [
    {"Type": "1", "ExchangeDivision": "T"},  # 値上がり率・東証全体
]

MARKET_OPEN = time(9, 0)
MARKET_CLOSE = time(15, 0)


def is_trading_hours(now: datetime) -> bool:
    """平日 9:00-15:00 (JST) かどうか."""
    if now.weekday() >= 5:  # 土日
        return False
    return MARKET_OPEN <= now.time() < MARKET_CLOSE


def log_path(now: datetime) -> Path:
    """日付ごとのログファイルパス."""
    return LOG_DIR / f"ranking_{now.strftime('%Y%m%d')}.jsonl"


async def fetch_and_log(client: httpx.AsyncClient, params: dict[str, str]) -> None:
    now = datetime.now(JST)
    try:
        resp = await client.get(GATEWAY_URL, params=params, timeout=10)
        record = {
            "ts": now.isoformat(),
            "status": resp.status_code,
            "params": params,
            "body": resp.json() if resp.status_code == 200 else resp.text,
        }
    except Exception as e:
        record = {
            "ts": now.isoformat(),
            "status": -1,
            "params": params,
            "error": str(e),
        }

    path = log_path(now)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    status = record.get("status")
    ranking_count = ""
    if status == 200 and isinstance(record.get("body"), dict):
        items = record["body"].get("Ranking") or []
        ranking_count = f" ({len(items)} items)"
    print(f"[{now.strftime('%H:%M:%S')}] Type={params.get('Type')} status={status}{ranking_count}")


async def main() -> None:
    print(f"ranking_collector started  url={GATEWAY_URL}")
    print(f"log_dir={LOG_DIR}")
    print(f"types={[p['Type'] for p in RANKING_TYPES]}  interval={INTERVAL_SEC}s")

    async with httpx.AsyncClient() as client:
        while True:
            now = datetime.now(JST)
            if is_trading_hours(now):
                tasks = [fetch_and_log(client, params) for params in RANKING_TYPES]
                await asyncio.gather(*tasks)
            else:
                # 取引時間外は10秒おきに時刻チェックのみ
                await asyncio.sleep(10)
                continue
            # 次の分の先頭まで待つ
            elapsed = (datetime.now(JST) - now).total_seconds()
            await asyncio.sleep(max(0, INTERVAL_SEC - elapsed))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nstopped.")
        sys.exit(0)
