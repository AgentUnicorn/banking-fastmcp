import logging
import os

from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("mcp.rs.google")
JWKS_PATH = os.environ.get("JWKS_PATH", "jwks.json")


async def jwks(request: Request) -> JSONResponse:
    """
    Serve the JWKS (JSON Web Key Set) for token verification
    """
    import json

    # Use JWKS_PATH from environment or default location

    jwks_path = (
        JWKS_PATH
        if os.path.isabs(JWKS_PATH)
        else os.path.join(os.path.dirname(__file__), JWKS_PATH)
    )

    try:
        with open(jwks_path, "r") as f:
            jwks_data = json.load(f)
        return JSONResponse(jwks_data)
    except FileNotFoundError:
        logger.error("jwks.json file not found at %s", jwks_path)
        return JSONResponse({"error": "JWKS not found"}, status_code=404)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in jwks.json")
        return JSONResponse({"error": "Invalid JWKS format"}, status_code=500)
