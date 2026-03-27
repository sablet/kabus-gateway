import os

import uvicorn
from dotenv import load_dotenv

from kabus_gateway.app import LOG_FORMAT, create_app

app = create_app()

if __name__ == "__main__":
    load_dotenv()
    host = os.environ.get("GATEWAY_HOST", "0.0.0.0")
    port = int(os.environ.get("GATEWAY_PORT", "18088"))

    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = LOG_FORMAT
    log_config["formatters"]["access"]["fmt"] = (
        "%(asctime)s %(levelname)s %(name)s: %(client_addr)s - \"%(request_line)s\" %(status_code)s"
    )

    uvicorn.run(app, host=host, port=port, log_config=log_config)
