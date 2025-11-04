import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class AuthDebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check for Authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            logger.info("Authorization header present: %s", auth_header[:50] + "...")
        else:
            logger.warning("No Authorization header found")

        try:
            response = await call_next(request)
            logger.info("Response status: %s", response.status_code)
            return response
        except Exception as e:
            logger.error("Error processing request: %s", str(e), exc_info=True)
            raise
