from __future__ import annotations

import logging
import os

import dotenv
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server.auth import JWTVerifier
from fastmcp.server.auth.providers.google import GoogleProvider
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from tools.banking_tools import (
    add_saved_account,
    get_account_info,
    get_transactions,
    list_saved_account,
    transfer_money,
)

# from tools.util_tools import get_time, get_user_info

logger = logging.getLogger("mcp.rs.google")

logging.basicConfig(level=logging.INFO)

logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("fastmcp.server.auth").setLevel(logging.DEBUG)

dotenv.load_dotenv()

BASE_URL = os.environ.get("RS_BASE_URL", "http://localhost:8005")
HOST = os.environ.get("RS_HOST", "0.0.0.0")
PORT = os.environ.get("RS_PORT", "8005")
MCP_PATH = os.environ.get("MCP_PATH", "/mcp")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REDIRECT_PATH = os.environ.get("GOOGLE_REDIRECT_PATH", "/auth/callback")
REQUIRED_SCOPES = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile".split()
ALLOWED_CLIENT_REDIRECTS = ["http://localhost:*"]
RESOURCE = f"{BASE_URL}{MCP_PATH}"
JWKS_PATH = os.environ.get("JWKS_PATH", "jwks.json")


google_auth = GoogleProvider(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    base_url=BASE_URL,
    redirect_path=REDIRECT_PATH,
    required_scopes=REQUIRED_SCOPES,
    allowed_client_redirect_uris=ALLOWED_CLIENT_REDIRECTS,
)

verifier = JWTVerifier(
    jwks_uri=f"{BASE_URL}/.well-known/jwks.json", issuer=BASE_URL, audience=BASE_URL
)

logger.info("JWT Verifier initialized")
logger.info("JWKS URI: %s", f"{BASE_URL}/.well-known/jwks.json")
logger.info("Issuer: %s", BASE_URL)
logger.info("Audience: %s", BASE_URL)

mcp = FastMCP(
    name="Banking FastMCP server",
    instructions="You are a banking MCP server which assist users to interact with their account",
    auth=google_auth,
)


@mcp.custom_route("/healthz", methods=["GET"])
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


@mcp.custom_route("/.well-known/jwks.json", methods=["GET"])
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
        "jwks_uri": f"{BASE_URL}/.well-known/jwks.json",
        "issuer": BASE_URL,
        "audience": BASE_URL,
    }

    logger.info("Debug auth request: %s", debug_info)

    return JSONResponse(debug_info)


# Util tools
# mcp.tool(name="get_time", description="Return current time")(get_time)
# mcp.tool(
#     name="get_user_info", description="Return authenticate user info include email"
# )(get_user_info)

# Banking tools
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

if __name__ == "__main__":
    # if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    #     logger.error(
    #         "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is not set. ",
    #         "Put them in your shell env or a .env file before starting the server.",
    #     )
    #     raise SystemExit(1)
    #
    # logger.info("RS base URL: %s", BASE_URL)
    # logger.info("MCP endpoint path: %s", MCP_PATH)
    # logger.info("Redirect path (Google): %s", REDIRECT_PATH)
    # logger.info("Required scopes: %s", " ".join(REQUIRED_SCOPES))
    # logger.info("Allowed DCR client redirects: %s", ALLOWED_CLIENT_REDIRECTS)
    # logger.info("Resource (audience): %s", RESOURCE)

    # mcp.run(transport="streamable-http", host=HOST, port=int(PORT), path=MCP_PATH)

    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware

    class AuthDebugMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Log all incoming requests

            # Check for Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header:
                logger.info(
                    "Authorization header present: %s", auth_header[:50] + "..."
                )
            else:
                logger.warning("No Authorization header found")

            try:
                response = await call_next(request)
                logger.info("Response status: %s", response.status_code)
                return response
            except Exception as e:
                logger.error("Error processing request: %s", str(e), exc_info=True)
                raise

    mcp_app = mcp.http_app(path=MCP_PATH, transport="streamable-http")
    app = FastAPI(lifespan=mcp_app.lifespan)
    app.add_middleware(AuthDebugMiddleware)

    origins = ["http://localhost", "http://localhost:8005"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # List of allowed origins
        allow_credentials=True,  # Allow cookies and authorization headers
        allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
        allow_headers=["*"],  # Allow all headers
        expose_headers=["*"],
    )

    app.mount("/", mcp_app)
    uvicorn.run(app, host=HOST, port=int(PORT))
