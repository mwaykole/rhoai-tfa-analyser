"""MCP tool definitions for ReportPortal UserFilter operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.filter_service import FilterService


def register_filter_tools(mcp: FastMCP, service: FilterService) -> None:
    """Register all filter-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Filter service
    """

    @mcp.tool()
    async def rp_list_filters(
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> str:
        """List all user filters in the project.

        Args:
            page: Page number (1-based, default 1)
            size: Items per page (default 20)
            sort: Sort field and direction (default name,asc)
        """
        result = await service.list_filters(
            page=page, size=size, sort=sort,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_filter(filter_id: str) -> str:
        """Get a specific user filter by its ID.

        Args:
            filter_id: The numeric filter ID
        """
        result = await service.get_filter(filter_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_filter(
        name: str,
        target_type: str,
        conditions: str,
        orders: str,
        description: str | None = None,
    ) -> str:
        """Create a new user filter.

        Args:
            name: Filter name
            target_type: Entity type to filter - launch, testItem, log
            conditions: JSON string of condition list, e.g.
                        '[{"filteringField":"status","condition":"eq","value":"FAILED"}]'
            orders: JSON string of sort orders, e.g.
                    '[{"sortingColumn":"startTime","isAsc":false}]'
            description: Optional description
        """
        conds = json.loads(conditions)
        ords = json.loads(orders)
        result = await service.create_filter(
            name=name, target_type=target_type,
            conditions=conds, orders=ords, description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_filter(
        filter_id: str,
        name: str | None = None,
        conditions: str | None = None,
        orders: str | None = None,
        description: str | None = None,
    ) -> str:
        """Update an existing user filter.

        Args:
            filter_id: The numeric filter ID
            name: Updated name
            conditions: JSON string of updated conditions
            orders: JSON string of updated sort orders
            description: Updated description
        """
        conds = json.loads(conditions) if conditions else None
        ords = json.loads(orders) if orders else None
        result = await service.update_filter(
            filter_id=filter_id, name=name,
            conditions=conds, orders=ords, description=description,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_filter(filter_id: str) -> str:
        """Delete a user filter by its ID.

        Args:
            filter_id: The numeric filter ID to delete
        """
        result = await service.delete_filter(filter_id)
        return json.dumps(result, default=str)
