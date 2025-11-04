import logging

from fastapi import HTTPException
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext
from scalekit import ScalekitClient
from scalekit.common.scalekit import TokenValidationOptions

from configs.config import settings

logger = logging.getLogger(__name__)
scalekit_client = ScalekitClient(
    settings.SCALEKIT_ENVIRONMENT_URL,
    settings.SCALEKIT_CLIENT_ID,
    settings.SCALEKIT_CLIENT_SECRET,
)


class ToolCallMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()

        auth_header = headers.get("authorization", "")
        token = auth_header.split(" ")[1]

        validation_options = TokenValidationOptions(
            issuer=settings.SCALEKIT_ENVIRONMENT_URL,
            audience=[settings.SCALEKIT_AUDIENCE_NAME],
        )

        try:
            payload = scalekit_client.validate_token(token, options=validation_options)
            user_id = payload.get("sub")

            user_res, _ = scalekit_client.users.get_user(user_id)
            user_info = {
                "user_id": user_id,
                "email": user_res.user.email,
                "name": user_res.user.user_profile.name,
            }
            logger.info("TOOL CALL: %s", user_info)
            context.fastmcp_context.set_state("user", user_info)

        except Exception as e:
            logger.error("Error fetching user info: %s", e, exc_info=True)
            raise HTTPException(status_code=401, detail="Token validation failed")

        return await call_next(context)
