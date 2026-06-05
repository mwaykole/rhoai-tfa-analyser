"""Service layer for ReportPortal Project operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ProjectService:
    """Encapsulates all project-related API operations.

    Uses global (non-project-scoped) endpoints via the /v1/ prefix convention.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_projects(
        self,
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> dict[str, Any]:
        """List all projects.

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
        response = await self._client.get("v1/project/list", params=params)
        logger.info("listed_projects", page=page)
        return response

    async def get_project(self, project_name: str) -> dict[str, Any]:
        """Get project details by name."""
        response = await self._client.get(f"v1/project/{project_name}")
        logger.info("fetched_project", project=project_name)
        return response

    async def create_project(
        self,
        project_name: str,
        entry_type: str = "INTERNAL",
    ) -> dict[str, Any]:
        """Create a new project.

        Args:
            project_name: Unique project name
            entry_type: INTERNAL or UPSA
        """
        data: dict[str, Any] = {
            "projectName": project_name,
            "entryType": entry_type,
        }
        response = await self._client.post("v1/project", data=data)
        logger.info("created_project", project=project_name)
        return response

    async def update_project(
        self,
        project_name: str,
        configuration: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update project configuration.

        Args:
            project_name: Project name
            configuration: Updated configuration dict
        """
        data: dict[str, Any] = {}
        if configuration:
            data["configuration"] = configuration

        response = await self._client.put(
            f"v1/project/{project_name}", data=data
        )
        logger.info("updated_project", project=project_name)
        return response

    async def delete_project(self, project_name: str) -> dict[str, Any]:
        """Delete a project by name."""
        response = await self._client.delete(f"v1/project/{project_name}")
        logger.info("deleted_project", project=project_name)
        return response

    async def assign_user(
        self,
        project_name: str,
        user_name: str,
        project_role: str = "MEMBER",
    ) -> dict[str, Any]:
        """Assign a user to a project.

        Args:
            project_name: Project name
            user_name: User login name
            project_role: Role (MEMBER, PROJECT_MANAGER, OPERATOR, CUSTOMER)
        """
        data: dict[str, Any] = {
            "userNames": {user_name: project_role},
        }
        response = await self._client.put(
            f"v1/project/{project_name}/assign", data=data
        )
        logger.info(
            "assigned_user",
            project=project_name,
            user=user_name,
            role=project_role,
        )
        return response

    async def unassign_user(
        self,
        project_name: str,
        user_name: str,
    ) -> dict[str, Any]:
        """Remove a user from a project.

        Args:
            project_name: Project name
            user_name: User login name
        """
        data: dict[str, Any] = {
            "userNames": [user_name],
        }
        response = await self._client.put(
            f"v1/project/{project_name}/unassign", data=data
        )
        logger.info(
            "unassigned_user", project=project_name, user=user_name
        )
        return response

    async def get_project_names(self) -> dict[str, Any]:
        """Get all project names (lightweight)."""
        response = await self._client.get("v1/project/names")
        logger.info("fetched_project_names")
        return response
