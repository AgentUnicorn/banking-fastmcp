from typing import Any


async def get_time() -> dict[str, Any]:
    import datetime as _dt

    now = _dt.datetime.now(_dt.timezone.utc)
    return {
        "current_time": now.isoformat() + "Z",
        "timestamp": now.timestamp(),
        "timezone": "UTC",
    }


async def get_user_info() -> dict[str, Any]:
    """
    Return information about the authenticated Google user
    (from the validated access token / user info)
    """
    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    if token is None:
        return {}

    return {
        "google_id": token.claims.get("sub"),
        "email": token.claims.get("email"),
        "name": token.claims.get("name"),
        "picture": token.claims.get("picture"),
        "locale": token.claims.get("locale"),
    }
