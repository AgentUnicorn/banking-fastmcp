from starlette.requests import Request
from starlette.responses import JSONResponse


async def healthz(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            # "base_url": BASE_URL,
            # "mcp_path": MCP_PATH,
            # "resource": RESOURCE,
            # "scopes": REQUIRED_SCOPES,
        }
    )
