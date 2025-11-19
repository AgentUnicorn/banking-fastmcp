import logging

from fastmcp import FastMCP

from configs.config import settings
from middlewares.tool_call import ToolCallMiddleware
from resources.banking_resources import list_banks
from tools.banking_tools import (
    add_saved_account,
    get_account_info,
    get_transactions,
    list_saved_account,
    transfer_money,
)

logger = logging.getLogger(__name__)


mcp = FastMCP(
    name="Banking FastMCP server",
    instructions="You are a banking MCP server which assist users to interact with their account",
)
mcp.add_middleware(ToolCallMiddleware())

# Tools
mcp.tool(
    name="get_account_info",
    description=(
        "Retrieve the authenticated user's banking account details using their JWT token. "
        "Returns account number, account name, formatted balance, and currency type. "
        "If the account is not found or authentication fails, an error message is returned."
    ),
)(get_account_info)
mcp.tool(
    name="get_transactions",
    description=(
        "Retrieve recent transactions for the authenticated user's account. "
        "Returns a list of recent transfers including type, amount, description, and recipient account. "
        "Accepts an optional 'limit' parameter to control how many transactions to retrieve (default: 10). "
        "Authentication is handled automatically via JWT token."
    ),
)(get_transactions)
mcp.tool(
    name="transfer_money",
    description=(
        "Transfer money from the authenticated user's account to another account. "
        "Requires parameters: 'to_account_number' (int), 'amount' (float), and 'description' (str). "
        "Validates balance before transfer and returns a structured result including status, message, "
        "source and destination accounts, amount, and description. Authentication is automatic via JWT token."
    ),
)(transfer_money)
mcp.tool(
    name="add_saved_account",
    description=(
        "Add a new recipient to the authenticated user's saved recipients list. "
        "Requires recipient details: 'account_number', 'account_name', and 'bank_name'. "
        "Supports partial bank name matching (e.g., 'VCB' for Vietcombank). "
        "Returns confirmation with saved recipient details. Authentication is automatic via JWT token."
    ),
)(add_saved_account)
mcp.tool(
    name="list_saved_account",
    description=(
        "List all saved recipients associated with the authenticated user's account. "
        "Returns recipient account numbers, names, and bank names for quick reference before making transfers. "
        "Authentication is automatic via JWT token."
    ),
)(list_saved_account)

# Resources
mcp.resource(
    uri="resource://bank/list",
    name="List available banks",
    description="List all available banks in the database",
    mime_type="application/json",
)(list_banks)