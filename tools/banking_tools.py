import logging
from typing import Any

from fastmcp import Context

from database.manager import BankingDatabase
from services.auth import AuthService

logger = logging.getLogger("mcp.tools.banking")

db = BankingDatabase()


async def get_account_info(
    ctx: Context, toolCallId: str | None = None
) -> dict[str, Any]:
    """
    Retrieve the currently authenticated user's banking account information.

    This function uses the authenticated user's email (via `AuthService.get_current_user_email()`)
    to fetch their account record from the database.

    Returns:
        dict: A dictionary containing:
            - "account_number" (int): The user's account number.
            - "account_name" (str): The name associated with the account.
            - "balance" (str): Current account balance, formatted with commas.
            - "currency" (str): The currency of the account.
        If the account is not found or an error occurs, returns {"error": <message>}.

    Example:
        {
            "account_number": 123456789,
            "account_name": "John Doe",
            "balance": "12,000,000",
            "currency": "VND"
        }
    """
    try:
        email = AuthService.get_current_user_email()
        logger.info("Fetching account info for: %s", email)

        account = db.get_account_by_email(email)
        if not account:
            return {"error": "Account associate with this email is not found"}

        return {
            "account_number": account.account_number,
            "account_name": account.account_name,
            "balance": f"{account.balance:,.0f}",
            "currency": account.currency,
        }
    except ValueError as e:
        logger.error("Authentication error: %s", str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Unexpected error in get_account_info: %s", str(e), exc_info=True)
        return {"error": f"System error: {str(e)}"}


async def get_transactions(limit: int = 10):
    """
    Retrieve recent transactions for the authenticated user's account.

    Args:
        limit (int, optional): The maximum number of transactions to return. Defaults to 10.

    Returns:
        dict: Contains:
            - "email" (str): The user's email.
            - "account_number" (int): The account number.
            - "total_transactions" (int): Number of transactions returned.
            - "transactions" (list): Each item includes:
                - "type" (str): Transaction type (e.g., 'deposit', 'withdrawal').
                - "amount" (float): Transaction amount.
                - "description" (str): Transaction description.
                - "recipient" (int): Recipient account number if applicable.
        If an error occurs, returns {"error": <message>}.

    Example:
        {
            "email": "user@example.com",
            "account_number": 987654321,
            "total_transactions": 2,
            "transactions": [
                {"type": "transfer", "amount": 500000, "description": "Rent", "recipient": 11223344},
                {"type": "deposit", "amount": 1500000, "description": "Salary", "recipient": null}
            ]
        }
    """
    try:
        email = AuthService.get_current_user_email()
        logger.info("Fetching transactions for: %s", email)

        account = db.get_account_by_email(email)
        if not account:
            return {"error": f"No account found for email: {email}", "email": email}

        transactions = db.get_transactions(account.account_number, limit)
        return {
            "email": email,
            "account_number": account.account_number,
            "total_transactions": len(transactions),
            "transactions": [
                {
                    "type": t.type,
                    "amount": t.amount,
                    "description": t.description,
                    "recipient": t.to_account_id,
                }
                for t in transactions
            ],
        }
    except ValueError as e:
        logger.error("Authentication error: %s", str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Unexpected error in get_account_info: %s", str(e), exc_info=True)
        return {"error": f"System error: {str(e)}"}


async def transfer_money(
    to_account_number: int,
    amount: float,
    description: str,
):
    """
    Transfer money from the authenticated user's account to another account.

    Args:
        to_account_number (int): The destination account number.
        amount (float): The amount to transfer.
        description (str): The transaction description (e.g., "Rent payment").

    Returns:
        dict: Contains:
            - "status" (str): "success" or "failed".
            - "message" (str): Description of the result.
            - On success, also includes:
                - "from_email" (str)
                - "from_account" (int)
                - "to_account" (int)
                - "amount" (str): Formatted amount with currency.
                - "description" (str)
        On failure, returns {"status": "failed", "message": <error>}.

    Example:
        {
            "status": "success",
            "message": "Chuyển khoản thành công!",
            "from_email": "user@example.com",
            "from_account": 11112222,
            "to_account": 33334444,
            "amount": "500,000 VND",
            "description": "Lunch payment"
        }
    """
    try:
        email = AuthService.get_current_user_email()
        logger.info(
            "Transfer request from: %s to account: %s", email, to_account_number
        )

        # Get sender's account
        account = db.get_account_by_email(email)
        if not account:
            return {
                "status": "failed",
                "message": f"Không tìm thấy tài khoản cho email: {email}",
            }

        # Check balance
        if account.balance < amount:
            return {
                "status": "failed",
                "message": "Số dư không đủ để thực hiện giao dịch!",
            }

        # Perform transfer
        success = db.transfer_money(
            account.account_number, to_account_number, amount, description
        )

        if success:
            logger.info(
                "Transfer successful: %s -> %s, amount: %s",
                account.account_number,
                to_account_number,
                amount,
            )
            return {
                "status": "success",
                "message": "Chuyển khoản thành công!",
                "from_email": email,
                "from_account": account.account_number,
                "to_account": to_account_number,
                "amount": f"{amount:,.0f} VND",
                "description": description,
            }
        else:
            return {"status": "failed", "message": "Giao dịch thất bại!"}

    except ValueError as e:
        logger.error("Transfer validation error: %s", str(e))
        return {"status": "failed", "message": str(e)}
    except Exception as e:
        logger.error("Transfer system error: %s", str(e), exc_info=True)
        return {"status": "failed", "message": f"Lỗi hệ thống: {str(e)}"}


async def add_saved_account(
    account_number: int,
    account_name: str,
    bank_name: str,
):
    """
    Save a recipient account to the authenticated user's saved recipients list.

    Args:
        account_number (int): The recipient's account number.
        account_name (str): The recipient's account holder name.
        bank_name (str): The recipient's bank name.

    Returns:
        dict: Contains:
            - "status" (str): "success" or "failed".
            - "message" (str): Description of the operation.
            - On success:
                - "owner_email" (str)
                - "recipient" (dict):
                    - "account_number" (int)
                    - "account_name" (str)
                    - "bank_name" (str)

    Example:
        {
            "status": "success",
            "message": "Đã thêm người nhận mới!",
            "owner_email": "user@example.com",
            "recipient": {
                "account_number": 55556666,
                "account_name": "Nguyen Van A",
                "bank_name": "Vietcombank"
            }
        }
    """
    try:
        email = AuthService.get_current_user_email()
        logger.info("Adding saved recipient for: %s", email)

        # Get owner's account
        account = db.get_account_by_email(email)
        if not account:
            return {
                "status": "failed",
                "message": f"Không tìm thấy tài khoản cho email: {email}",
            }

        # Find bank
        bank = db.find_bank_by_name(bank_name)
        if not bank:
            return {
                "status": "failed",
                "message": f"Không tìm thấy ngân hàng: {bank_name}",
            }

        existed = db.get_saved_recipient(account.id, account_number)
        if existed:
            return {
                "status": "failed",
                "message": f"Không tìm thấy ngân hàng: {bank_name}",
            }

        # Add recipient
        recipient = db.add_saved_recipient(
            account.id, account_number, account_name, bank.id
        )

        logger.info("Saved recipient added: %s for user: %s", account_number, email)
        return {
            "status": "success",
            "message": "Đã thêm người nhận mới!",
            "owner_email": email,
            "recipient": {
                "account_number": recipient.account_number,
                "account_name": recipient.account_name,
                "bank_name": bank.name,
            },
        }

    except ValueError as e:
        logger.error("Validation error adding recipient: %s", str(e))
        return {"status": "failed", "message": str(e)}
    except Exception as e:
        logger.error("System error adding recipient: %s", str(e), exc_info=True)
        return {"status": "failed", "message": f"Lỗi hệ thống: {str(e)}"}


async def list_saved_account():
    """
    List all saved recipient accounts associated with the authenticated user's account.

    Returns:
        dict: Contains:
            - "email" (str): The user's email.
            - "total_recipients" (int): Number of saved recipients.
            - "recipients" (list): Each recipient includes:
                - "account_number" (int)
                - "account_name" (str)
                - "bank_name" (str)
        If an error occurs, returns {"error": <message>}.

    Example:
        {
            "email": "user@example.com",
            "total_recipients": 2,
            "recipients": [
                {"account_number": 55556666, "account_name": "Nguyen Van A", "bank_name": "Vietcombank"},
                {"account_number": 77778888, "account_name": "Tran Thi B", "bank_name": "Techcombank"}
            ]
        }
    """
    try:
        email = AuthService.get_current_user_email()
        logger.info("Listing saved recipients for: %s", email)

        account = db.get_account_by_email(email)
        if not account:
            return {
                "error": f"Không tìm thấy tài khoản cho email: {email}",
                "email": email,
            }

        recipients = db.get_saved_recipients(account.id)
        return {
            "email": email,
            "total_recipients": len(recipients),
            "recipients": [
                {
                    "account_number": r.account_number,
                    "account_name": r.account_name,
                    "bank_name": r.bank_name,
                }
                for r in recipients
            ],
        }

    except ValueError as e:
        logger.error("Authentication error: %s", str(e))
        return {"error": str(e)}
    except Exception as e:
        logger.error("Unexpected error listing recipients: %s", str(e), exc_info=True)
        return {"error": f"System error: {str(e)}"}
