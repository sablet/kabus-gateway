import os

import uvicorn
from dotenv import load_dotenv

from kabus_gateway.app import create_app

app = create_app()

if __name__ == "__main__":
    load_dotenv()
    host = os.environ.get("GATEWAY_HOST", "0.0.0.0")
    port = int(os.environ.get("GATEWAY_PORT", "18088"))
    uvicorn.run(app, host=host, port=port)
