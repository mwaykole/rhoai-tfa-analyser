"""Service layer for ReportPortal Launch operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LaunchService:
    """Encapsulates all launch-related API operations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_launches(
        self,
        page: int = 1,
        size: int = 20,
        sort: str = "startTime,desc",
        status: str | None = None,
        name: str | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        """List launches with optional filters.

        Args:
            page: Page number (1-based)
            size: Items per page
            sort: Sort field and direction
            status: Filter by status (PASSED, FAILED, etc.)
            name: Filter by launch name
            mode: Filter by mode (DEFAULT, DEBUG)
        """
        params: dict[str, Any] = {
            "page.page": page,
            "page.size": size,
            "page.sort": sort,
        }
        if status:
            params["filter.eq.status"] = status
        if name:
            params["filter.cnt.name"] = name
        if mode:
            params["filter.eq.mode"] = mode

        response = await self._client.get("launch", params=params)
        logger.info("listed_launches", page=page, size=size)
        return response

    async def get_launch_by_id(self, launch_id: str) -> dict[str, Any]:
        """Get a specific launch by its numeric ID."""
        response = await self._client.get(f"launch/{launch_id}")
        logger.info("fetched_launch", launch_id=launch_id)
        return response

    async def get_launch_by_uuid(self, launch_uuid: str) -> dict[str, Any]:
        """Get a specific launch by its UUID."""
        response = await self._client.get(f"launch/uuid/{launch_uuid}")
        logger.info("fetched_launch_by_uuid", uuid=launch_uuid)
        return response

    async def create_launch(
        self,
        name: str,
        start_time: str,
        description: str | None = None,
        mode: str = "DEFAULT",
        attributes: list[dict[str, str]] | None = None,
        rerun: bool = False,
        rerun_of: str | None = None,
    ) -> dict[str, Any]:
        """Start a new launch.

        Args:
            name: Launch name
            start_time: ISO 8601 or epoch milliseconds
            description: Optional description
            mode: DEFAULT or DEBUG
            attributes: Key-value attribute pairs
            rerun: Whether this is a rerun
            rerun_of: UUID of the original launch (for reruns)
        """
        data: dict[str, Any] = {
            "name": name,
            "startTime": start_time,
            "mode": mode,
        }
        if description:
            data["description"] = description
        if attributes:
            data["attributes"] = attributes
        if rerun:
            data["rerun"] = True
        if rerun_of:
            data["rerunOf"] = rerun_of

        response = await self._client.post("launch", data=data)
        logger.info("created_launch", name=name)
        return response

    async def finish_launch(
        self,
        launch_uuid: str,
        end_time: str,
        status: str | None = None,
        description: str | None = None,
        attributes: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Finish a running launch.

        Args:
            launch_uuid: UUID of the launch to finish
            end_time: ISO 8601 or epoch milliseconds
            status: Final status (PASSED, FAILED, etc.)
            description: Optional updated description
            attributes: Optional updated attributes
        """
        data: dict[str, Any] = {"endTime": end_time}
        if status:
            data["status"] = status
        if description:
            data["description"] = description
        if attributes:
            data["attributes"] = attributes

        response = await self._client.put(
            f"launch/{launch_uuid}/finish", data=data
        )
        logger.info("finished_launch", uuid=launch_uuid)
        return response

    async def force_finish_launch(
        self,
        launch_id: str,
        end_time: str,
        status: str = "STOPPED",
    ) -> dict[str, Any]:
        """Force-finish a launch that is stuck."""
        data: dict[str, Any] = {"endTime": end_time, "status": status}
        response = await self._client.put(
            f"launch/{launch_id}/stop", data=data
        )
        logger.info("force_finished_launch", launch_id=launch_id)
        return response

    async def update_launch(
        self,
        launch_id: str,
        description: str | None = None,
        mode: str | None = None,
        attributes: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Update launch metadata."""
        data: dict[str, Any] = {}
        if description is not None:
            data["description"] = description
        if mode:
            data["mode"] = mode
        if attributes is not None:
            data["attributes"] = attributes

        response = await self._client.put(f"launch/{launch_id}/update", data=data)
        logger.info("updated_launch", launch_id=launch_id)
        return response

    async def delete_launch(self, launch_id: str) -> dict[str, Any]:
        """Delete a launch by ID."""
        response = await self._client.delete(f"launch/{launch_id}")
        logger.info("deleted_launch", launch_id=launch_id)
        return response

    async def merge_launches(
        self,
        launch_ids: list[int],
        merge_type: str,
        name: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
        attributes: list[dict[str, str]] | None = None,
        extend_suite_description: bool = True,
    ) -> dict[str, Any]:
        """Merge multiple launches into one.

        Args:
            launch_ids: IDs of launches to merge
            merge_type: BASIC or DEEP
            name: Name for merged launch
            start_time: Start time for merged launch
            end_time: End time for merged launch
            description: Optional description
            attributes: Optional attributes
            extend_suite_description: Whether to extend suite descriptions
        """
        data: dict[str, Any] = {
            "launches": launch_ids,
            "mergeType": merge_type,
            "name": name,
            "startTime": start_time,
            "endTime": end_time,
            "extendSuitesDescription": extend_suite_description,
        }
        if description:
            data["description"] = description
        if attributes:
            data["attributes"] = attributes

        response = await self._client.post("launch/merge", data=data)
        logger.info("merged_launches", count=len(launch_ids))
        return response

    async def compare_launches(
        self, launch_ids: list[int]
    ) -> dict[str, Any]:
        """Compare statistics across multiple launches."""
        params = {"ids": ",".join(str(i) for i in launch_ids)}
        response = await self._client.get("launch/compare", params=params)
        logger.info("compared_launches", count=len(launch_ids))
        return response
