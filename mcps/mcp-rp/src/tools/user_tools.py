"""MCP tool definitions for ReportPortal User operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.user_service import UserService


def register_user_tools(mcp: FastMCP, service: UserService) -> None:
    """Register all user-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: User service
    """

    @mcp.tool()
    async def rp_get_current_user() -> str:
        """Get the profile of the currently authenticated user."""
        result = await service.get_current_user()
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_user(user_name: str) -> str:
        """Get user details by login name.

        Args:
            user_name: The user's login name
        """
        result = await service.get_user(user_name)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_search_users(
        term: str,
        page: int = 1,
        size: int = 20,
    ) -> str:
        """Search for users by name or email.

        Args:
            term: Search term (matches against name and email)
            page: Page number (1-based, default 1)
            size: Items per page (default 20)
        """
        result = await service.search_users(
            term=term, page=page, size=size,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_list_api_keys(user_id: str) -> str:
        """List API keys for a specific user.

        Args:
            user_id: The numeric user ID
        """
        result = await service.list_api_keys(user_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_api_key(
        user_id: str,
        name: str,
    ) -> str:
        """Create a new API key for a user. Save the key immediately - it cannot be retrieved later.

        Args:
            user_id: The numeric user ID
            name: Display name for the API key
        """
        result = await service.create_api_key(user_id=user_id, name=name)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_api_key(
        user_id: str,
        key_id: str,
    ) -> str:
        """Delete (revoke) an API key.

        Args:
            user_id: The numeric user ID
            key_id: The API key ID to delete
        """
        result = await service.delete_api_key(
            user_id=user_id, key_id=key_id,
        )
        return json.dumps(result, default=str)
