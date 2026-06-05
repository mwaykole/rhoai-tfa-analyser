"""Service layer for ReportPortal Dashboard operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Encapsulates all dashboard-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_dashboards(
        self,
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> dict[str, Any]:
        """List all dashboards in the project.

        Args:
            page: Page number (1-based)
            size: Items per page
            sort: Sort field and direction
        """
        params: dict[str, Any] = {
            "page.page": page,
            "page.size": size,
            "page.sort": sort,
        }
        response = await self._client.get("dashboard", params=params)
        logger.info("listed_dashboards", page=page)
        return response

    async def get_dashboard(self, dashboard_id: str) -> dict[str, Any]:
        """Get a specific dashboard by ID."""
        response = await self._client.get(f"dashboard/{dashboard_id}")
        logger.info("fetched_dashboard", dashboard_id=dashboard_id)
        return response

    async def create_dashboard(
        self,
        name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new dashboard.

        Args:
            name: Dashboard name
            description: Optional description
        """
        data: dict[str, Any] = {"name": name}
        if description:
            data["description"] = description

        response = await self._client.post("dashboard", data=data)
        logger.info("created_dashboard", name=name)
        return response

    async def update_dashboard(
        self,
        dashboard_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update dashboard metadata.

        Args:
            dashboard_id: Dashboard ID
            name: Updated name
            description: Updated description
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description

        response = await self._client.put(
            f"dashboard/{dashboard_id}", data=data
        )
        logger.info("updated_dashboard", dashboard_id=dashboard_id)
        return response

    async def delete_dashboard(self, dashboard_id: str) -> dict[str, Any]:
        """Delete a dashboard by ID."""
        response = await self._client.delete(f"dashboard/{dashboard_id}")
        logger.info("deleted_dashboard", dashboard_id=dashboard_id)
        return response

    async def add_widget_to_dashboard(
        self,
        dashboard_id: str,
        widget_id: str,
        widget_name: str,
        widget_type: str,
        widget_size: dict[str, int] | None = None,
        widget_position: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Add a widget to a dashboard.

        Args:
            dashboard_id: Dashboard ID
            widget_id: Widget ID to add
            widget_name: Display name for the widget
            widget_type: Widget type identifier
            widget_size: Width/height dict
            widget_position: x/y position dict
        """
        data: dict[str, Any] = {
            "widgetName": widget_name,
            "widgetType": widget_type,
        }
        if widget_size:
            data["widgetSize"] = widget_size
        if widget_position:
            data["widgetPosition"] = widget_position

        response = await self._client.put(
            f"dashboard/{dashboard_id}/{widget_id}", data=data
        )
        logger.info(
            "added_widget_to_dashboard",
            dashboard_id=dashboard_id,
            widget_id=widget_id,
        )
        return response

    async def remove_widget_from_dashboard(
        self,
        dashboard_id: str,
        widget_id: str,
    ) -> dict[str, Any]:
        """Remove a widget from a dashboard.

        Args:
            dashboard_id: Dashboard ID
            widget_id: Widget ID to remove
        """
        response = await self._client.delete(
            f"dashboard/{dashboard_id}/{widget_id}"
        )
        logger.info(
            "removed_widget_from_dashboard",
            dashboard_id=dashboard_id,
            widget_id=widget_id,
        )
        return response
