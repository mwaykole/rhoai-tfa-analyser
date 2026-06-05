"""MCP tool definitions for ReportPortal Integration operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.integration_service import IntegrationService


def register_integration_tools(
    mcp: FastMCP, service: IntegrationService
) -> None:
    """Register all integration-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Integration service
    """

    @mcp.tool()
    async def rp_list_global_integrations() -> str:
        """List all globally configured integrations."""
        result = await service.list_global_integrations()
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_list_project_integrations(project_name: str) -> str:
        """List integrations configured for a specific project.

        Args:
            project_name: The project name
        """
        result = await service.list_project_integrations(project_name)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_integration(integration_id: str) -> str:
        """Get integration details by ID.

        Args:
            integration_id: The numeric integration ID
        """
        result = await service.get_integration(integration_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_global_integration(
        plugin_name: str,
        name: str,
        parameters: str,
        enabled: bool = True,
    ) -> str:
        """Create a new global integration.

        Args:
            plugin_name: Plugin type name (e.g. jira, rally, email, ldap, saml, etc.)
            name: Display name for the integration
            parameters: JSON string of integration parameters (plugin-specific)
            enabled: Whether the integration is active (default true)
        """
        params = json.loads(parameters)
        result = await service.create_global_integration(
            plugin_name=plugin_name, name=name,
            parameters=params, enabled=enabled,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_project_integration(
        project_name: str,
        plugin_name: str,
        name: str,
        parameters: str,
        enabled: bool = True,
    ) -> str:
        """Create a project-scoped integration.

        Args:
            project_name: The project name
            plugin_name: Plugin type name (e.g. jira, rally, email, etc.)
            name: Display name for the integration
            parameters: JSON string of integration parameters
            enabled: Whether the integration is active (default true)
        """
        params = json.loads(parameters)
        result = await service.create_project_integration(
            project_name=project_name, plugin_name=plugin_name,
            name=name, parameters=params, enabled=enabled,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_integration(
        integration_id: str,
        name: str | None = None,
        parameters: str | None = None,
        enabled: bool | None = None,
    ) -> str:
        """Update an existing integration.

        Args:
            integration_id: The numeric integration ID
            name: Updated display name
            parameters: JSON string of updated parameters
            enabled: Updated enabled state
        """
        params = json.loads(parameters) if parameters else None
        result = await service.update_integration(
            integration_id=integration_id, name=name,
            parameters=params, enabled=enabled,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_integration(integration_id: str) -> str:
        """Delete an integration by its ID.

        Args:
            integration_id: The numeric integration ID to delete
        """
        result = await service.delete_integration(integration_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_test_integration_connection(integration_id: str) -> str:
        """Test connectivity for an integration to verify it is properly configured.

        Args:
            integration_id: The numeric integration ID to test
        """
        result = await service.test_connection(integration_id)
        return json.dumps(result, default=str)
