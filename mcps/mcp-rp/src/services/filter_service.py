"""Service layer for ReportPortal UserFilter operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class FilterService:
    """Encapsulates all user-filter-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_filters(
        self,
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> dict[str, Any]:
        """List all user filters in the project.

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
        response = await self._client.get("filter", params=params)
        logger.info("listed_filters", page=page)
        return response

    async def get_filter(self, filter_id: str) -> dict[str, Any]:
        """Get a specific filter by ID."""
        response = await self._client.get(f"filter/{filter_id}")
        logger.info("fetched_filter", filter_id=filter_id)
        return response

    async def create_filter(
        self,
        name: str,
        target_type: str,
        conditions: list[dict[str, str]],
        orders: list[dict[str, Any]],
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create a new user filter.

        Args:
            name: Filter name
            target_type: Entity type to filter (launch, testItem, etc.)
            conditions: List of filter conditions with filteringField, condition, value
            orders: Sort orders with sortingColumn and isAsc
            description: Optional description
        """
        data: dict[str, Any] = {
            "name": name,
            "type": target_type,
            "conditions": conditions,
            "orders": orders,
        }
        if description:
            data["description"] = description

        response = await self._client.post("filter", data=data)
        logger.info("created_filter", name=name)
        return response

    async def update_filter(
        self,
        filter_id: str,
        name: str | None = None,
        conditions: list[dict[str, str]] | None = None,
        orders: list[dict[str, Any]] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing filter.

        Args:
            filter_id: Filter ID
            name: Updated name
            conditions: Updated conditions
            orders: Updated sort orders
            description: Updated description
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if conditions is not None:
            data["conditions"] = conditions
        if orders is not None:
            data["orders"] = orders
        if description is not None:
            data["description"] = description

        response = await self._client.put(f"filter/{filter_id}", data=data)
        logger.info("updated_filter", filter_id=filter_id)
        return response

    async def delete_filter(self, filter_id: str) -> dict[str, Any]:
        """Delete a filter by ID."""
        response = await self._client.delete(f"filter/{filter_id}")
        logger.info("deleted_filter", filter_id=filter_id)
        return response
