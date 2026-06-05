"""Service layer for ReportPortal TestItem operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TestItemService:
    """Encapsulates all test-item-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_test_items(
        self,
        launch_id: str | None = None,
        parent_id: str | None = None,
        status: str | None = None,
        item_type: str | None = None,
        name: str | None = None,
        page: int = 1,
        size: int = 50,
        sort: str = "startTime,asc",
    ) -> dict[str, Any]:
        """List test items with optional filters.

        Args:
            launch_id: Filter by launch ID
            parent_id: Filter by parent item ID
            status: Filter by status (PASSED, FAILED, etc.)
            item_type: Filter by type (SUITE, TEST, STEP, etc.)
            name: Filter by name (contains match)
            page: Page number (1-based)
            size: Items per page
            sort: Sort field and direction
        """
        params: dict[str, Any] = {
            "page.page": page,
            "page.size": size,
            "page.sort": sort,
        }
        if launch_id:
            params["filter.eq.launchId"] = launch_id
        if parent_id:
            params["filter.eq.parentId"] = parent_id
        if status:
            params["filter.eq.status"] = status
        if item_type:
            params["filter.eq.type"] = item_type
        if name:
            params["filter.cnt.name"] = name

        response = await self._client.get("item", params=params)
        logger.info("listed_test_items", launch_id=launch_id, page=page)
        return response

    async def get_test_item_by_id(self, item_id: str) -> dict[str, Any]:
        """Get a specific test item by its numeric ID."""
        response = await self._client.get(f"item/{item_id}")
        logger.info("fetched_test_item", item_id=item_id)
        return response

    async def get_test_item_by_uuid(self, item_uuid: str) -> dict[str, Any]:
        """Get a specific test item by its UUID."""
        response = await self._client.get(f"item/uuid/{item_uuid}")
        logger.info("fetched_test_item_by_uuid", uuid=item_uuid)
        return response

    async def create_test_item(
        self,
        name: str,
        start_time: str,
        item_type: str,
        launch_uuid: str,
        parent_item_uuid: str | None = None,
        description: str | None = None,
        attributes: list[dict[str, str]] | None = None,
        has_stats: bool = True,
    ) -> dict[str, Any]:
        """Create a new test item (suite, test, or step).

        Args:
            name: Test item name
            start_time: ISO 8601 or epoch milliseconds
            item_type: SUITE, TEST, STEP, etc.
            launch_uuid: UUID of the parent launch
            parent_item_uuid: UUID of the parent item (for child items)
            description: Optional description
            attributes: Key-value attribute pairs
            has_stats: Whether the item should collect statistics
        """
        data: dict[str, Any] = {
            "name": name,
            "startTime": start_time,
            "type": item_type,
            "launchUuid": launch_uuid,
            "hasStats": has_stats,
        }
        if description:
            data["description"] = description
        if attributes:
            data["attributes"] = attributes

        endpoint = f"item/{parent_item_uuid}" if parent_item_uuid else "item"
        response = await self._client.post(endpoint, data=data)
        logger.info("created_test_item", name=name, type=item_type)
        return response

    async def finish_test_item(
        self,
        item_uuid: str,
        end_time: str,
        status: str,
        description: str | None = None,
        issue: dict[str, Any] | None = None,
        attributes: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Finish a test item.

        Args:
            item_uuid: UUID of the item to finish
            end_time: ISO 8601 or epoch milliseconds
            status: Final status (PASSED, FAILED, SKIPPED, etc.)
            description: Updated description
            issue: Issue details for failed items
            attributes: Updated attributes
        """
        data: dict[str, Any] = {
            "endTime": end_time,
            "status": status,
        }
        if description:
            data["description"] = description
        if issue:
            data["issue"] = issue
        if attributes:
            data["attributes"] = attributes

        response = await self._client.put(f"item/{item_uuid}", data=data)
        logger.info("finished_test_item", uuid=item_uuid, status=status)
        return response

    async def update_test_item(
        self,
        item_id: str,
        description: str | None = None,
        attributes: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Update test item metadata."""
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if attributes is not None:
            data["attributes"] = attributes

        response = await self._client.put(f"item/{item_id}/update", data=data)
        logger.info("updated_test_item", item_id=item_id)
        return response

    async def delete_test_item(self, item_id: str) -> dict[str, Any]:
        """Delete a test item by ID."""
        response = await self._client.delete(f"item/{item_id}")
        logger.info("deleted_test_item", item_id=item_id)
        return response

    async def get_test_item_history(
        self,
        item_id: str,
        history_depth: int = 10,
        filter_id: int | None = None,
    ) -> dict[str, Any]:
        """Get execution history for a test item.

        Args:
            item_id: Test item ID
            history_depth: Number of historical launches to check
            filter_id: Optional filter to narrow launches
        """
        params: dict[str, Any] = {
            "historyDepth": history_depth,
            "filter.eq.id": item_id,
        }
        if filter_id:
            params["filterId"] = filter_id

        response = await self._client.get("item/history", params=params)
        logger.info("fetched_test_item_history", item_id=item_id)
        return response

    async def update_issues(
        self,
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Bulk-update issues on test items.

        Args:
            issues: List of dicts with testItemId and issue fields
        """
        data = {"issues": issues}
        response = await self._client.put("item", data=data)
        logger.info("updated_issues", count=len(issues))
        return response

    async def link_external_issue(
        self,
        test_item_ids: list[int],
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Link external bug-tracker issues to test items.

        Args:
            test_item_ids: Test item IDs to link
            issues: External issue details (url, btsUrl, btsProject, ticketId)
        """
        data = {
            "testItemIds": test_item_ids,
            "issues": issues,
        }
        response = await self._client.put("item/issue/link", data=data)
        logger.info("linked_external_issues", item_count=len(test_item_ids))
        return response

    async def unlink_external_issue(
        self,
        test_item_ids: list[int],
        ticket_ids: list[str],
    ) -> dict[str, Any]:
        """Unlink external bug-tracker issues from test items.

        Args:
            test_item_ids: Test item IDs to unlink
            ticket_ids: Ticket IDs to remove
        """
        data = {
            "testItemIds": test_item_ids,
            "ticketIds": ticket_ids,
        }
        response = await self._client.put("item/issue/unlink", data=data)
        logger.info("unlinked_external_issues", item_count=len(test_item_ids))
        return response
