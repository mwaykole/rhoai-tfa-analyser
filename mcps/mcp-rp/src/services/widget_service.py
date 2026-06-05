"""Service layer for ReportPortal Widget operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WidgetService:
    """Encapsulates all widget-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_widget_names(self) -> dict[str, Any]:
        """List all widget names in the project."""
        response = await self._client.get("widget/names")
        logger.info("listed_widget_names")
        return response

    async def get_widget(self, widget_id: str) -> dict[str, Any]:
        """Get a specific widget by ID."""
        response = await self._client.get(f"widget/{widget_id}")
        logger.info("fetched_widget", widget_id=widget_id)
        return response

    async def create_widget(
        self,
        name: str,
        widget_type: str,
        content_parameters: dict[str, Any],
        filter_ids: list[int] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new widget.

        Args:
            name: Widget name
            widget_type: Widget type (e.g. statisticTrend, launchStatistics)
            content_parameters: Widget-specific content configuration
            filter_ids: IDs of filters to use as data source
            description: Optional description
        """
        data: dict[str, Any] = {
            "name": name,
            "widgetType": widget_type,
            "contentParameters": content_parameters,
        }
        if filter_ids:
            data["filterIds"] = filter_ids
        if description:
            data["description"] = description

        response = await self._client.post("widget", data=data)
        logger.info("created_widget", name=name, type=widget_type)
        return response

    async def update_widget(
        self,
        widget_id: str,
        name: str | None = None,
        widget_type: str | None = None,
        content_parameters: dict[str, Any] | None = None,
        filter_ids: list[int] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing widget.

        Args:
            widget_id: Widget ID
            name: Updated name
            widget_type: Updated widget type
            content_parameters: Updated content config
            filter_ids: Updated filter IDs
            description: Updated description
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if widget_type is not None:
            data["widgetType"] = widget_type
        if content_parameters is not None:
            data["contentParameters"] = content_parameters
        if filter_ids is not None:
            data["filterIds"] = filter_ids
        if description is not None:
            data["description"] = description

        response = await self._client.put(f"widget/{widget_id}", data=data)
        logger.info("updated_widget", widget_id=widget_id)
        return response

    async def get_widget_preview(
        self,
        widget_type: str,
        content_parameters: dict[str, Any],
        filter_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Get a preview of widget data without creating it.

        Args:
            widget_type: Widget type
            content_parameters: Widget content configuration
            filter_ids: Filter IDs for data source
        """
        data: dict[str, Any] = {
            "widgetType": widget_type,
            "contentParameters": content_parameters,
        }
        if filter_ids:
            data["filterIds"] = filter_ids

        response = await self._client.post("widget/preview", data=data)
        logger.info("fetched_widget_preview", type=widget_type)
        return response
