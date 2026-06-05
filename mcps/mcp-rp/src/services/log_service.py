"""Service layer for ReportPortal Log operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LogService:
    """Encapsulates all log-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_logs(
        self,
        item_id: str | None = None,
        launch_id: str | None = None,
        level: str | None = None,
        page: int = 1,
        size: int = 50,
        sort: str = "logTime,asc",
    ) -> dict[str, Any]:
        """List logs with optional filters.

        Args:
            item_id: Filter by test item ID
            launch_id: Filter by launch ID
            level: Filter by log level (ERROR, WARN, INFO, etc.)
            page: Page number (1-based)
            size: Items per page
            sort: Sort field and direction
        """
        params: dict[str, Any] = {
            "page.page": page,
            "page.size": size,
            "page.sort": sort,
        }
        if item_id:
            params["filter.eq.item"] = item_id
        if launch_id:
            params["filter.eq.launch"] = launch_id
        if level:
            params["filter.eq.level"] = level

        response = await self._client.get("log", params=params)
        logger.info("listed_logs", item_id=item_id, page=page)
        return response

    async def get_log_by_id(self, log_id: str) -> dict[str, Any]:
        """Get a specific log entry by its numeric ID."""
        response = await self._client.get(f"log/{log_id}")
        logger.info("fetched_log", log_id=log_id)
        return response

    async def get_log_by_uuid(self, log_uuid: str) -> dict[str, Any]:
        """Get a specific log entry by its UUID."""
        response = await self._client.get(f"log/uuid/{log_uuid}")
        logger.info("fetched_log_by_uuid", uuid=log_uuid)
        return response

    async def create_log(
        self,
        item_uuid: str,
        launch_uuid: str,
        time: str,
        message: str,
        level: str = "INFO",
    ) -> dict[str, Any]:
        """Create a log entry for a test item.

        Args:
            item_uuid: UUID of the parent test item
            launch_uuid: UUID of the parent launch
            time: ISO 8601 or epoch milliseconds
            message: Log message text
            level: Log level (ERROR, WARN, INFO, DEBUG, TRACE, FATAL)
        """
        data: dict[str, Any] = {
            "itemUuid": item_uuid,
            "launchUuid": launch_uuid,
            "time": time,
            "message": message,
            "level": level,
        }
        response = await self._client.post("log", data=data)
        logger.info("created_log", item_uuid=item_uuid, level=level)
        return response

    async def get_nested_step_logs(
        self,
        parent_id: str,
        page: int = 1,
        size: int = 50,
    ) -> dict[str, Any]:
        """Get logs for nested steps under a parent item.

        Args:
            parent_id: Parent test item ID
            page: Page number
            size: Items per page
        """
        params: dict[str, Any] = {
            "page.page": page,
            "page.size": size,
        }
        response = await self._client.get(
            f"log/nested/{parent_id}", params=params
        )
        logger.info("fetched_nested_logs", parent_id=parent_id)
        return response

    async def search_logs(
        self,
        item_id: str,
        search_mode: str = "CURRENT_LAUNCH",
    ) -> dict[str, Any]:
        """Search for similar log entries across launches.

        Args:
            item_id: Test item ID to search from
            search_mode: CURRENT_LAUNCH or LAUNCH_NAME
        """
        data: dict[str, Any] = {"searchMode": search_mode}
        response = await self._client.post(
            f"log/search/{item_id}", data=data
        )
        logger.info("searched_logs", item_id=item_id, mode=search_mode)
        return response

    async def delete_log(self, log_id: str) -> dict[str, Any]:
        """Delete a log entry by ID."""
        response = await self._client.delete(f"log/{log_id}")
        logger.info("deleted_log", log_id=log_id)
        return response
