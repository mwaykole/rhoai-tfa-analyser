"""MCP tool definitions for ReportPortal Dashboard operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.dashboard_service import DashboardService


def register_dashboard_tools(mcp: FastMCP, service: DashboardService) -> None:
    """Register all dashboard-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Dashboard service
    """

    @mcp.tool()
    async def rp_list_dashboards(
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> str:
        """List all dashboards in the project.

        Args:
            page: Page number (1-based, default 1)
            size: Items per page (default 20)
            sort: Sort field and direction (default name,asc)
        """
        result = await service.list_dashboards(
            page=page, size=size, sort=sort,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_dashboard(dashboard_id: str) -> str:
        """Get a specific dashboard by its ID, including its widgets.

        Args:
            dashboard_id: The numeric dashboard ID
        """
        result = await service.get_dashboard(dashboard_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_dashboard(
        name: str,
        description: str | None = None,
    ) -> str:
        """Create a new empty dashboard.

        Args:
            name: Dashboard name
            description: Optional dashboard description
        """
        result = await service.create_dashboard(
            name=name, description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_dashboard(
        dashboard_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update dashboard metadata (name, description).

        Args:
            dashboard_id: The numeric dashboard ID
            name: Updated name
            description: Updated description
        """
        result = await service.update_dashboard(
            dashboard_id=dashboard_id, name=name, description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_dashboard(dashboard_id: str) -> str:
        """Delete a dashboard by its ID.

        Args:
            dashboard_id: The numeric dashboard ID to delete
        """
        result = await service.delete_dashboard(dashboard_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_add_widget_to_dashboard(
        dashboard_id: str,
        widget_id: str,
        widget_name: str,
        widget_type: str,
        widget_size: str | None = None,
        widget_position: str | None = None,
    ) -> str:
        """Add a widget to a dashboard.

        Args:
            dashboard_id: The dashboard ID
            widget_id: The widget ID to add
            widget_name: Display name for the widget on this dashboard
            widget_type: Widget type identifier
            widget_size: JSON string of size, e.g. '{"width":6,"height":4}'
            widget_position: JSON string of position, e.g. '{"posX":0,"posY":0}'
        """
        size = json.loads(widget_size) if widget_size else None
        position = json.loads(widget_position) if widget_position else None
        result = await service.add_widget_to_dashboard(
            dashboard_id=dashboard_id, widget_id=widget_id,
            widget_name=widget_name, widget_type=widget_type,
            widget_size=size, widget_position=position,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_remove_widget_from_dashboard(
        dashboard_id: str,
        widget_id: str,
    ) -> str:
        """Remove a widget from a dashboard.

        Args:
            dashboard_id: The dashboard ID
            widget_id: The widget ID to remove
        """
        result = await service.remove_widget_from_dashboard(
            dashboard_id=dashboard_id, widget_id=widget_id,
        )
        return json.dumps(result, default=str)
