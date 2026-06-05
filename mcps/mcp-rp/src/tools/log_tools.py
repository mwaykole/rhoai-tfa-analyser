"""MCP tool definitions for ReportPortal Log operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.log_service import LogService


def register_log_tools(mcp: FastMCP, service: LogService) -> None:
    """Register all log-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Log service
    """

    @mcp.tool()
    async def rp_list_logs(
        item_id: str | None = None,
        launch_id: str | None = None,
        level: str | None = None,
        page: int = 1,
        size: int = 50,
        sort: str = "logTime,asc",
    ) -> str:
        """List log entries from ReportPortal with optional filters.

        Args:
            item_id: Filter by test item ID
            launch_id: Filter by launch ID
            level: Filter by log level - ERROR, WARN, INFO, DEBUG, TRACE, FATAL
            page: Page number (1-based, default 1)
            size: Items per page (default 50)
            sort: Sort field and direction (default logTime,asc)
        """
        result = await service.list_logs(
            item_id=item_id, launch_id=launch_id, level=level,
            page=page, size=size, sort=sort,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_log(log_id: str) -> str:
        """Get a specific log entry by its numeric ID.

        Args:
            log_id: The numeric log entry ID
        """
        result = await service.get_log_by_id(log_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_log_by_uuid(log_uuid: str) -> str:
        """Get a specific log entry by its UUID.

        Args:
            log_uuid: The log entry UUID
        """
        result = await service.get_log_by_uuid(log_uuid)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_log(
        item_uuid: str,
        launch_uuid: str,
        time: str,
        message: str,
        level: str = "INFO",
    ) -> str:
        """Create a log entry for a test item.

        Args:
            item_uuid: UUID of the parent test item
            launch_uuid: UUID of the parent launch
            time: Log timestamp as ISO 8601 string or epoch milliseconds
            message: Log message text
            level: Log level - ERROR, WARN, INFO, DEBUG, TRACE, FATAL (default INFO)
        """
        result = await service.create_log(
            item_uuid=item_uuid, launch_uuid=launch_uuid,
            time=time, message=message, level=level,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_nested_step_logs(
        parent_id: str,
        page: int = 1,
        size: int = 50,
    ) -> str:
        """Get logs for nested steps under a parent test item.

        Args:
            parent_id: Parent test item ID
            page: Page number (1-based, default 1)
            size: Items per page (default 50)
        """
        result = await service.get_nested_step_logs(
            parent_id=parent_id, page=page, size=size,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_search_logs(
        item_id: str,
        search_mode: str = "CURRENT_LAUNCH",
    ) -> str:
        """Search for similar log entries across launches based on a test item's logs.

        Args:
            item_id: Test item ID to search similar logs for
            search_mode: Search scope - CURRENT_LAUNCH or LAUNCH_NAME (default CURRENT_LAUNCH)
        """
        result = await service.search_logs(
            item_id=item_id, search_mode=search_mode,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_log(log_id: str) -> str:
        """Delete a log entry by its numeric ID.

        Args:
            log_id: The numeric log entry ID to delete
        """
        result = await service.delete_log(log_id)
        return json.dumps(result, default=str)
