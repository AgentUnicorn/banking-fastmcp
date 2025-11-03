import logging
from typing import Any, Optional

from database.manager import BankingDatabase
from database.models import Transaction
from services.auth import AuthService

logger = logging.getLogger("mcp.tools.banking")

db = BankingDatabase()


async def get_account_info() -> dict[str, Any]:
    """
    Retrieve account information by email address.

    This function looks up a bank account using the account holder's email
    and returns their account details including balance and account number.

    Args:
        email: The email address associated with the account (e.g., "user@example.com")

    Returns:
        dict containing:
            - account_number (int): The account number
            - account_name (str): Account holder's full name
            - balance (str): Current balance formatted with thousand separators
            - currency (str): Currency code (e.g., "VND")
            - error (str): Error message if account not found

    Example:
        >>> await get_account_info("user@example.com")
        {
            "account_number": 1234567890,
            "account_name": "Nguyễn Văn A",
            "balance": "50,000,000",
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


async def get_transactions(account_number: int, limit: int = 10):
    """
    Get transaction history for a specific account.

    Retrieves both incoming and outgoing transactions for the specified account,
    sorted by date (most recent first).

    Args:
        account_number: The account number to get transactions for
        limit: Maximum number of transactions to return (default: 10, max: 100)

    Returns:
        dict containing:
            - account_number (int): The queried account number
            - total_transactions (int): Number of transactions returned
            - transactions (list): List of transaction objects with:
                - type (str): Transaction type (e.g., "transfer", "deposit")
                - amount (float): Transaction amount
                - description (str): Transaction note/description
                - recipient (int): Recipient account ID (for transfers)

    Example:
        >>> await get_transactions(1234567890, limit=5)
        {
            "account_number": 1234567890,
            "total_transactions": 5,
            "transactions": [
                {
                    "type": "transfer",
                    "amount": 100000.0,
                    "description": "Payment for lunch",
                    "recipient": 987654321
                }
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
    from_account_number: int,
    to_account_number: int,
    amount: float,
    description: str,
):
    """
    Transfer money from one account to another.

    This function performs a bank transfer between two accounts. The recipient
    must be in the sender's saved recipients list. The operation is atomic -
    it either completes fully or fails without any changes.

    IMPORTANT:
    - The recipient account must be added to saved recipients first
    - Sender must have sufficient balance
    - Amount must be positive

    Args:
        from_account_number: Sender's account number
        to_account_number: Recipient's account number (must be saved recipient)
        amount: Amount to transfer in VND (must be > 0)
        description: Transfer note/description (e.g., "Rent payment", "Gift")

    Returns:
        dict containing:
            - status (str): "success" or "failed"
            - message (str): Vietnamese message describing the result
            - from_account (int): Sender's account number (on success)
            - to_account (int): Recipient's account number (on success)
            - amount (str): Formatted amount with currency (on success)
            - description (str): Transaction description (on success)

    Example:
        >>> await transfer_money(1234567890, 9876543210, 500000, "Trả tiền cơm")
        {
            "status": "success",
            "message": "Chuyển khoản thành công!",
            "from_account": 1234567890,
            "to_account": 9876543210,
            "amount": "500,000 VND",
            "description": "Trả tiền cơm"
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
    owner_account_id: int,
    account_number: int,
    account_name: str,
    bank_name: str,
):
    """
    Add a new recipient to saved accounts for quick future transfers.

    This function saves a recipient's account information so they can be
    easily selected for future transfers without re-entering details.

    Args:
        owner_account_id: The ID of the account saving this recipient
        account_number: Recipient's account number
        account_name: Recipient's full name (as registered with their bank)
        bank_name: Recipient's bank name (can be partial, e.g., "Vietcombank" or "VCB")

    Returns:
        dict containing:
            - status (str): "success" or "failed"
            - message (str): Vietnamese message describing the result
            - recipient (dict): Saved recipient details (on success):
                - account_number (int): Recipient's account number
                - account_name (str): Recipient's name
                - bank_name (str): Full bank name

    Example:
        >>> await add_saved_account(1, 9876543210, "Trần Thị B", "Vietcombank")
        {
            "status": "success",
            "message": "Đã thêm người nhận mới!",
            "recipient": {
                "account_number": 9876543210,
                "account_name": "Trần Thị B",
                "bank_name": "Ngân hàng TMCP Ngoại Thương Việt Nam"
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


async def list_saved_account(email: str):
    """
    List all saved recipients for a user's account.

    Retrieves all recipients that have been saved for quick transfers.
    These are accounts that the user frequently transfers money to.

    Args:
        email: The email address of the account owner

    Returns:
        dict containing:
            - total_recipients (int): Number of saved recipients
            - recipients (list): List of saved recipient objects with:
                - account_number (int): Recipient's account number
                - account_name (str): Recipient's full name
                - bank_name (str): Recipient's bank name
            - message (str): Error message if account not found

    Example:
        >>> await list_saved_account("user@example.com")
        {
            "total_recipients": 2,
            "recipients": [
                {
                    "account_number": 9876543210,
                    "account_name": "Trần Thị B",
                    "bank_name": "Vietcombank"
                },
                {
                    "account_number": 1111222233,
                    "account_name": "Lê Văn C",
                    "bank_name": "Techcombank"
                }
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
