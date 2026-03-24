# kabus-gateway

kabu STATION API のローカルゲートウェイ。認証を透過的に処理し、クライアントはトークン管理不要でAPIを利用できる。

## アーキテクチャ

```
┌──────────────┐        ┌──────────────────────────────────────┐
│    Client    │        │          Windows Machine             │
│ (other host) │──HTTP──▶  kabus-gateway ──HTTP──▶ kabu STATION│
│              │◀───────│  :18088                  :18080      │
└──────────────┘        └──────────────────────────────────────┘
```

## セットアップ

```bash
uv sync
```

`.env` を作成:

```
KABUS_API_PASSWORD=your_password_here
```

オプション（デフォルト値あり）:

```
KABUS_BASE_URL=http://localhost:18080/kabusapi
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=18088
```

## 起動

```bash
uv run python main.py
```

## 動作確認

ゲートウェイ自体の起動確認（kabu STATION不要）:

```bash
curl http://localhost:18088/
# {"status":"ok"}
```

kabu STATION接続確認:

```bash
curl http://localhost:18088/apisoftlimit
```

## エンドポイント

kabu STATION API のパスをそのまま使用する。認証ヘッダは不要。

```bash
# 板情報
curl http://localhost:18088/board/9433@1

# 注文
curl -X POST http://localhost:18088/sendorder -H 'Content-Type: application/json' -d '{"Symbol":"9433","Exchange":1,...}'

# WebSocket（銘柄登録後にPUSHデータ受信）
curl -X PUT http://localhost:18088/register -H 'Content-Type: application/json' -d '{"Symbols":[{"Symbol":"9433","Exchange":1}]}'
wscat -c ws://localhost:18088/ws
```
