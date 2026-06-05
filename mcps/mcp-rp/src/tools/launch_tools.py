"""MCP tool definitions for ReportPortal Launch operations."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.launch_service import LaunchService


def register_launch_tools(mcp: FastMCP, service: LaunchService) -> None:
    """Register all launch-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Launch service
    """

    @mcp.tool()
    async def rp_list_launches(
        page: int = 1,
        size: int = 20,
        sort: str = "startTime,desc",
        status: str | None = None,
        name: str | None = None,
        mode: str | None = None,
    ) -> str:
        """List launches from ReportPortal with optional filters.

        Args:
            page: Page number (1-based, default 1)
            size: Items per page (default 20)
            sort: Sort field and direction (default startTime,desc)
            status: Filter by status - PASSED, FAILED, IN_PROGRESS, STOPPED, INTERRUPTED
            name: Filter by launch name (contains match)
            mode: Filter by mode - DEFAULT or DEBUG
        """
        result = await service.list_launches(
            page=page, size=size, sort=sort,
            status=status, name=name, mode=mode,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_launch(launch_id: str) -> str:
        """Get a specific launch by its numeric ID.

        Args:
            launch_id: The numeric launch ID
        """
        result = await service.get_launch_by_id(launch_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_launch_by_uuid(launch_uuid: str) -> str:
        """Get a specific launch by its UUID.

        Args:
            launch_uuid: The launch UUID
        """
        result = await service.get_launch_by_uuid(launch_uuid)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_launch(
        name: str,
        start_time: str,
        description: str | None = None,
        mode: str = "DEFAULT",
        attributes: str | None = None,
        rerun: bool = False,
        rerun_of: str | None = None,
    ) -> str:
        """Start a new launch in ReportPortal.

        Args:
            name: Launch name
            start_time: Start time as ISO 8601 string or epoch milliseconds
            description: Optional launch description
            mode: Launch mode - DEFAULT or DEBUG (default DEFAULT)
            attributes: JSON string of attribute list, e.g. '[{"key":"env","value":"staging"}]'
            rerun: Whether this is a rerun of an existing launch
            rerun_of: UUID of the original launch when rerun is true
        """
        attrs = _parse_json_list(attributes)
        result = await service.create_launch(
            name=name, start_time=start_time, description=description,
            mode=mode, attributes=attrs, rerun=rerun, rerun_of=rerun_of,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_finish_launch(
        launch_uuid: str,
        end_time: str,
        status: str | None = None,
        description: str | None = None,
        attributes: str | None = None,
    ) -> str:
        """Finish a running launch.

        Args:
            launch_uuid: UUID of the launch to finish
            end_time: End time as ISO 8601 string or epoch milliseconds
            status: Final status - PASSED, FAILED, STOPPED, INTERRUPTED
            description: Optional updated description
            attributes: JSON string of updated attribute list
        """
        attrs = _parse_json_list(attributes)
        result = await service.finish_launch(
            launch_uuid=launch_uuid, end_time=end_time,
            status=status, description=description, attributes=attrs,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_force_finish_launch(
        launch_id: str,
        end_time: str,
        status: str = "STOPPED",
    ) -> str:
        """Force-finish a launch that is stuck in IN_PROGRESS state.

        Args:
            launch_id: The numeric launch ID
            end_time: End time as ISO 8601 string or epoch milliseconds
            status: Status to set (default STOPPED)
        """
        result = await service.force_finish_launch(
            launch_id=launch_id, end_time=end_time, status=status,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_launch(
        launch_id: str,
        description: str | None = None,
        mode: str | None = None,
        attributes: str | None = None,
    ) -> str:
        """Update launch metadata (description, mode, attributes).

        Args:
            launch_id: The numeric launch ID
            description: Updated description
            mode: Updated mode - DEFAULT or DEBUG
            attributes: JSON string of updated attribute list
        """
        attrs = _parse_json_list(attributes)
        result = await service.update_launch(
            launch_id=launch_id, description=description,
            mode=mode, attributes=attrs,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_launch(launch_id: str) -> str:
        """Delete a launch by its numeric ID.

        Args:
            launch_id: The numeric launch ID to delete
        """
        result = await service.delete_launch(launch_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_merge_launches(
        launch_ids: str,
        merge_type: str,
        name: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        attributes: str | None = None,
        extend_suite_description: bool = True,
    ) -> str:
        """Merge multiple launches into a single launch.

        Args:
            launch_ids: Comma-separated numeric launch IDs to merge (e.g. "1,2,3")
            merge_type: Merge strategy - BASIC or DEEP
            name: Name for the merged launch
            start_time: Start time for merged launch
            end_time: End time for merged launch
            description: Optional description
            attributes: JSON string of attribute list
            extend_suite_description: Whether to extend suite descriptions (default true)
        """
        ids = [int(x.strip()) for x in launch_ids.split(",")]
        attrs = _parse_json_list(attributes)
        result = await service.merge_launches(
            launch_ids=ids, merge_type=merge_type, name=name,
            start_time=start_time, end_time=end_time,
            description=description, attributes=attrs,
            extend_suite_description=extend_suite_description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_compare_launches(launch_ids: str) -> str:
        """Compare statistics across multiple launches.

        Args:
            launch_ids: Comma-separated numeric launch IDs to compare (e.g. "1,2,3")
        """
        ids = [int(x.strip()) for x in launch_ids.split(",")]
        result = await service.compare_launches(ids)
        return json.dumps(result, default=str)


def _parse_json_list(value: str | None) -> list[dict[str, Any]] | None:
    if not value:
        return None
    return json.loads(value)
