import logging
from typing import Any, List

from fastmcp import Context

from database.manager import db

logger = logging.getLogger("mcp.resources.banking")


async def list_banks(ctx: Context) -> dict[str, Any]:
    try:
        banks = db.list_banks()
        return {"success": "True", "banks": banks}
    except Exception as e:
        logger.error("Unexpected error in get_account_info: %s", str(e), exc_info=True)
        return {"error": f"System error: {str(e)}"}
