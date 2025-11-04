import logging
import os

from fastmcp import FastMCP
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.google import GoogleProvider
from starlette.requests import Request
from starlette.responses import JSONResponse

from configs.config import settings
from tools.banking_tools import (
    add_saved_account,
    get_account_info,
    get_transactions,
    list_saved_account,
    transfer_money,
)

logger = logging.getLogger(__name__)

google_auth = GoogleProvider(
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    base_url=settings.BASE_URL,
    redirect_path=settings.REDIRECT_PATH,
    required_scopes=settings.REQUIRED_SCOPES,
    allowed_client_redirect_uris=settings.ALLOWED_CLIENT_REDIRECTS,
)

verifier = JWTVerifier(
    jwks_uri=f"{settings.BASE_URL}/.well-known/jwks.json",
    issuer=settings.BASE_URL,
    audience=settings.BASE_URL,
)

mcp = FastMCP(
    name="Banking FastMCP server",
    instructions="You are a banking MCP server which assist users to interact with their account",
    auth=google_auth,
)

# Tools
mcp.tool(
    name="get_account_info",
    description="Get account information for the currently authenticated user. Returns account number, name, balance, and currency. Authentication is automatic via JWT token.",
)(get_account_info)
mcp.tool(
    name="get_transactions",
    description="Get transaction history for the authenticated user's account. Shows recent transfers with amounts and descriptions. Use limit parameter to control how many transactions to retrieve. Authentication is automatic.",
)(get_transactions)
mcp.tool(
    name="transfer_money",
    description="Transfer money from the authenticated user's account to a saved recipient. Automatically uses the sender's account from JWT token. Validates balance before transfer. Recipient must be in saved recipients list.",
)(transfer_money)
mcp.tool(
    name="add_saved_account",
    description="Add a new recipient to the authenticated user's saved accounts for future quick transfers. Requires recipient's account number, name, and bank name. Bank name can be partial (e.g., 'VCB' for Vietcombank). Authentication is automatic.",
)(add_saved_account)
mcp.tool(
    name="list_saved_account",
    description="List all saved recipients for the authenticated user. Shows recipient account numbers, names, and bank names. Useful before making transfers to see available recipients. Authentication is automatic.",
)(list_saved_account)
# mcp.tool(name="get_time", description="Return current time")(get_time)
# mcp.tool(
#     name="get_user_info", description="Return authenticate user info include email"
# )(get_user_info)

# Prompts

# Resources


# Custom Routes
@mcp.custom_route("/healthz", methods=["GET"])
async def healthz(request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "base_url": settings.BASE_URL,
            "mcp_path": settings.MCP_PATH,
            "resource": settings.RESOURCE,
            "scopes": settings.REQUIRED_SCOPES,
        }
    )


@mcp.custom_route("/.well-known/jwks.json", methods=["GET"])
async def jwks(request: Request) -> JSONResponse:
    """
    Serve the JWKS (JSON Web Key Set) for token verification
    """
    import json

    # Use JWKS_PATH from environment or default location
    jwks_path = (
        settings.JWKS_PATH
        if os.path.isabs(settings.JWKS_PATH)
        else os.path.join(os.path.dirname(__file__), settings.JWKS_PATH)
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


@mcp.custom_route("/debug/auth", methods=["GET"])
async def debug_auth(request: Request) -> JSONResponse:
    """
    Debug endpoint to check authentication headers and token
    """
    headers = dict(request.headers)
    auth_header = headers.get("authorization", "No Authorization header")

    debug_info = {
        "has_auth_header": "authorization" in headers,
        "auth_header": (
            auth_header[:50] + "..." if len(auth_header) > 50 else auth_header
        ),
        "jwks_uri": f"{settings.BASE_URL}/.well-known/jwks.json",
        "issuer": settings.BASE_URL,
        "audience": settings.BASE_URL,
    }

    logger.info("Debug auth request: %s", debug_info)

    return JSONResponse(debug_info)
