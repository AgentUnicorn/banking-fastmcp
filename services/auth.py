import logging
from typing import Optional

from fastmcp.server.dependencies import get_access_token, get_context

logger = logging.getLogger("mcp.auth.service")


class AuthService:
    """
    Authentication service for extracting user information from JWT tokens.

    This service provides methods to retrieve authenticated user information
    from the access token provided in MCP requests.
    """

    @staticmethod
    def get_current_user_email() -> str:
        """
        Get the email address of the currently authenticated user from JWT token.

        This method extracts the email claim from the validated JWT access token.
        The token is automatically validated by the JWTVerifier before this method is called.

        Returns:
            str: The authenticated user's email address

        Raises:
            ValueError: If no token is present or email claim is missing

        Example:
            >>> email = AuthService.get_current_user_email()
            >>> print(email)
            'user@example.com'
        """
        context = get_context()
        user = context.get_state("user")

        email = user.get("email")

        if not email:
            logger.error("Email not exist in context")
            raise ValueError("Email not found in access token. Token may be invalid.")

        logger.info("Authenticated user: %s", email)
        return email

    @staticmethod
    def get_current_user_info() -> dict:
        """
        Get complete user information from the JWT token.

        Returns:
            dict: User information containing:
                - email (str): User's email address
                - sub (str): User's unique identifier (subject)
                - name (str): User's full name (if available)
                - picture (str): User's profile picture URL (if available)
                - locale (str): User's locale/language preference (if available)

        Raises:
            ValueError: If no token is present
        """
        context = get_context()
        user = context.get_state("user")

        user_info = {
            "email": user.get("email"),
            "name": user.get("name"),
        }

        logger.info("Retrieved user info for: %s", user_info.get("email"))
        return user_info

    @staticmethod
    def get_account_id_from_email(email: str) -> Optional[int]:
        """
        Get the account ID associated with an email address.

        Args:
            email: User's email address

        Returns:
            Optional[int]: Account ID if found, None otherwise
        """
        from database.manager import BankingDatabase

        db = BankingDatabase()
        account = db.get_account_by_email(email)

        if account:
            return account.id

        logger.warning("No account found for email: %s", email)
        return None
