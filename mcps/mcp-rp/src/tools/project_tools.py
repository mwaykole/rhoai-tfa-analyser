"""MCP tool definitions for ReportPortal Project operations."""

import json

from mcp.server.fastmcp import FastMCP

from src.services.project_service import ProjectService


def register_project_tools(mcp: FastMCP, service: ProjectService) -> None:
    """Register all project-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: Project service
    """

    @mcp.tool()
    async def rp_list_projects(
        page: int = 1,
        size: int = 20,
        sort: str = "name,asc",
    ) -> str:
        """List all ReportPortal projects.

        Args:
            page: Page number (1-based, default 1)
            size: Items per page (default 20)
            sort: Sort field and direction (default name,asc)
        """
        result = await service.list_projects(
            page=page, size=size, sort=sort,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_project(project_name: str) -> str:
        """Get project details by name.

        Args:
            project_name: The project name
        """
        result = await service.get_project(project_name)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_project_names() -> str:
        """Get a lightweight list of all project names."""
        result = await service.get_project_names()
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_project(
        project_name: str,
        entry_type: str = "INTERNAL",
    ) -> str:
        """Create a new ReportPortal project.

        Args:
            project_name: Unique project name
            entry_type: Project type - INTERNAL or UPSA (default INTERNAL)
        """
        result = await service.create_project(
            project_name=project_name, entry_type=entry_type,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_project(
        project_name: str,
        configuration: str | None = None,
    ) -> str:
        """Update project configuration.

        Args:
            project_name: The project name
            configuration: JSON string of configuration updates
        """
        config = json.loads(configuration) if configuration else None
        result = await service.update_project(
            project_name=project_name, configuration=config,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_project(project_name: str) -> str:
        """Delete a project by name. This is irreversible.

        Args:
            project_name: The project name to delete
        """
        result = await service.delete_project(project_name)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_assign_user_to_project(
        project_name: str,
        user_name: str,
        project_role: str = "MEMBER",
    ) -> str:
        """Assign a user to a project with a specific role.

        Args:
            project_name: The project name
            user_name: User login name
            project_role: Role - MEMBER, PROJECT_MANAGER, OPERATOR, CUSTOMER (default MEMBER)
        """
        result = await service.assign_user(
            project_name=project_name, user_name=user_name,
            project_role=project_role,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_unassign_user_from_project(
        project_name: str,
        user_name: str,
    ) -> str:
        """Remove a user from a project.

        Args:
            project_name: The project name
            user_name: User login name to remove
        """
        result = await service.unassign_user(
            project_name=project_name, user_name=user_name,
        )
        return json.dumps(result, default=str)
