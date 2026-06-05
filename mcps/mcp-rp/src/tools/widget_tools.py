"""MCP tool definitions for ReportPortal Widget operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.widget_service import WidgetService


def register_widget_tools(mcp: FastMCP, service: WidgetService) -> None:
    """Register all widget-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Widget service
    """

    @mcp.tool()
    async def rp_list_widget_names() -> str:
        """List all widget names in the project."""
        result = await service.list_widget_names()
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_widget(widget_id: str) -> str:
        """Get a specific widget by its ID.

        Args:
            widget_id: The numeric widget ID
        """
        result = await service.get_widget(widget_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_widget(
        name: str,
        widget_type: str,
        content_parameters: str,
        filter_ids: str | None = None,
        description: str | None = None,
    ) -> str:
        """Create a new widget.

        Args:
            name: Widget name
            widget_type: Widget type (e.g. statisticTrend, launchStatistics, overallStatistics)
            content_parameters: JSON string of content configuration
            filter_ids: Comma-separated filter IDs as data source (e.g. "1,2")
            description: Optional description
        """
        params = json.loads(content_parameters)
        fids = [int(x.strip()) for x in filter_ids.split(",")] if filter_ids else None
        result = await service.create_widget(
            name=name, widget_type=widget_type,
            content_parameters=params, filter_ids=fids,
            description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_widget(
        widget_id: str,
        name: str | None = None,
        widget_type: str | None = None,
        content_parameters: str | None = None,
        filter_ids: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update an existing widget.

        Args:
            widget_id: The numeric widget ID
            name: Updated name
            widget_type: Updated widget type
            content_parameters: JSON string of updated content configuration
            filter_ids: Comma-separated updated filter IDs
            description: Updated description
        """
        params = json.loads(content_parameters) if content_parameters else None
        fids = (
            [int(x.strip()) for x in filter_ids.split(",")]
            if filter_ids else None
        )
        result = await service.update_widget(
            widget_id=widget_id, name=name, widget_type=widget_type,
            content_parameters=params, filter_ids=fids,
            description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_preview_widget(
        widget_type: str,
        content_parameters: str,
        filter_ids: str | None = None,
    ) -> str:
        """Preview widget data without creating it. Useful for testing configurations.

        Args:
            widget_type: Widget type
            content_parameters: JSON string of content configuration
            filter_ids: Comma-separated filter IDs as data source
        """
        params = json.loads(content_parameters)
        fids = [int(x.strip()) for x in filter_ids.split(",")] if filter_ids else None
        result = await service.get_widget_preview(
            widget_type=widget_type, content_parameters=params,
            filter_ids=fids,
        )
        return json.dumps(result, default=str)
