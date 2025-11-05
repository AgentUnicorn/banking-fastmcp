from __future__ import annotations

import json
import logging

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from configs.config import settings
from mcp_server import mcp
from middlewares.auth import AuthMiddleware

logger = logging.getLogger(__name__)


logging.basicConfig(level=logging.DEBUG)

logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("fastmcp.server.auth").setLevel(logging.DEBUG)


mcp_app = mcp.http_app(path=settings.MCP_PATH, transport="streamable-http")
app = FastAPI(lifespan=mcp_app.lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # List of allowed origins
    allow_credentials=True,  # Allow cookies and authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
    expose_headers=["mcp-session-id"],
)


@app.get("/.well-known/oauth-protected-resource/mcp")
async def oauth_protected_resource_metadata():
    return json.loads(settings.METADATA_JSON_RESPONSE)


app.add_middleware(AuthMiddleware)
app.mount("/", mcp_app)


def main():
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, log_level="info")


if __name__ == "__main__":
    main()
