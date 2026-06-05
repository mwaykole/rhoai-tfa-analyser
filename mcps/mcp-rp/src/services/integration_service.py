"""Service layer for ReportPortal Integration operations."""

from typing import Any

from src.clients.base import BaseHTTPClient
from src.utils.logging import get_logger

logger = get_logger(__name__)


class IntegrationService:
    """Encapsulates all integration-related API operations.

    Supports both global and project-scoped integrations.

    Args:
        client: HTTP client for ReportPortal API calls
    """

    def __init__(self, client: BaseHTTPClient):
        self._client = client

    async def list_global_integrations(self) -> dict[str, Any]:
        """List all global integrations."""
        response = await self._client.get("v1/integration/global/all")
        logger.info("listed_global_integrations")
        return response

    async def list_project_integrations(
        self,
        project_name: str,
    ) -> dict[str, Any]:
        """List integrations for a specific project.

        Args:
            project_name: Project name
        """
        response = await self._client.get(
            f"v1/integration/project/{project_name}/all"
        )
        logger.info("listed_project_integrations", project=project_name)
        return response

    async def get_integration(
        self, integration_id: str
    ) -> dict[str, Any]:
        """Get integration details by ID.

        Args:
            integration_id: Integration ID
        """
        response = await self._client.get(
            f"v1/integration/{integration_id}"
        )
        logger.info("fetched_integration", integration_id=integration_id)
        return response

    async def create_global_integration(
        self,
        plugin_name: str,
        name: str,
        parameters: dict[str, Any],
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a global integration.

        Args:
            plugin_name: Plugin type name (e.g. jira, email, etc.)
            name: Display name
            parameters: Integration-specific parameters
            enabled: Whether the integration is active
        """
        data: dict[str, Any] = {
            "name": name,
            "integrationParameters": parameters,
            "enabled": enabled,
        }
        response = await self._client.post(
            f"v1/integration/{plugin_name}", data=data
        )
        logger.info("created_global_integration", plugin=plugin_name, name=name)
        return response

    async def create_project_integration(
        self,
        project_name: str,
        plugin_name: str,
        name: str,
        parameters: dict[str, Any],
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Create a project-scoped integration.

        Args:
            project_name: Project name
            plugin_name: Plugin type name
            name: Display name
            parameters: Integration-specific parameters
            enabled: Whether the integration is active
        """
        data: dict[str, Any] = {
            "name": name,
            "integrationParameters": parameters,
            "enabled": enabled,
        }
        response = await self._client.post(
            f"v1/integration/{project_name}/{plugin_name}", data=data
        )
        logger.info(
            "created_project_integration",
            project=project_name,
            plugin=plugin_name,
        )
        return response

    async def update_integration(
        self,
        integration_id: str,
        name: str | None = None,
        parameters: dict[str, Any] | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        """Update an existing integration.

        Args:
            integration_id: Integration ID
            name: Updated name
            parameters: Updated parameters
            enabled: Updated enabled state
        """
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if parameters is not None:
            data["integrationParameters"] = parameters
        if enabled is not None:
            data["enabled"] = enabled

        response = await self._client.put(
            f"v1/integration/{integration_id}", data=data
        )
        logger.info("updated_integration", integration_id=integration_id)
        return response

    async def delete_integration(
        self, integration_id: str
    ) -> dict[str, Any]:
        """Delete an integration by ID.

        Args:
            integration_id: Integration ID
        """
        response = await self._client.delete(
            f"v1/integration/{integration_id}"
        )
        logger.info("deleted_integration", integration_id=integration_id)
        return response

    async def test_connection(
        self, integration_id: str
    ) -> dict[str, Any]:
        """Test connectivity for an integration.

        Args:
            integration_id: Integration ID
        """
        response = await self._client.get(
            f"v1/integration/{integration_id}/connection/test"
        )
        logger.info("tested_integration_connection", integration_id=integration_id)
        return response
