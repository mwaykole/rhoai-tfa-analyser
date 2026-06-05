"""Service layer for ReportPortal User operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Encapsulates all user-related API operations.

    Uses global (non-project-scoped) endpoints via the /v1/ prefix convention.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def get_current_user(self) -> dict[str, Any]:
        """Get the currently authenticated user's profile."""
        response = await self._client.get("v1/user")
        logger.info("fetched_current_user")
        return response

    async def get_user(self, user_name: str) -> dict[str, Any]:
        """Get user details by login name.

        Args:
            user_name: User login name
        """
        response = await self._client.get(f"v1/user/{user_name}")
        logger.info("fetched_user", user=user_name)
        return response

    async def search_users(
        self,
        term: str,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """Search users by name or email.

        Args:
            term: Search term
            page: Page number (1-based)
            size: Items per page
        """
        params: dict[str, Any] = {
            "term": term,
            "page.page": page,
            "page.size": size,
        }
        response = await self._client.get("v1/user/search", params=params)
        logger.info("searched_users", term=term)
        return response

    async def list_api_keys(self, user_id: str) -> dict[str, Any]:
        """List API keys for a user.

        Args:
            user_id: Numeric user ID
        """
        response = await self._client.get(f"v1/users/{user_id}/api-keys")
        logger.info("listed_api_keys", user_id=user_id)
        return response

    async def create_api_key(
        self,
        user_id: str,
        name: str,
    ) -> dict[str, Any]:
        """Create a new API key for a user.

        Args:
            user_id: Numeric user ID
            name: Display name for the key
        """
        data: dict[str, Any] = {"name": name}
        response = await self._client.post(
            f"v1/users/{user_id}/api-keys", data=data
        )
        logger.info("created_api_key", user_id=user_id, name=name)
        return response

    async def delete_api_key(
        self,
        user_id: str,
        key_id: str,
    ) -> dict[str, Any]:
        """Delete an API key.

        Args:
            user_id: Numeric user ID
            key_id: API key ID to delete
        """
        response = await self._client.delete(
            f"v1/users/{user_id}/api-keys/{key_id}"
        )
        logger.info("deleted_api_key", user_id=user_id, key_id=key_id)
        return response
