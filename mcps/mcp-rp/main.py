"""MCP Server for ReportPortal -- entry point.

Wires configuration, HTTP client, services, and MCP tool registrations,
then starts the FastMCP server.
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from src.clients.reportportal import ReportPortalClient
from src.config.settings import create_settings
from src.services.dashboard_service import DashboardService
from src.services.filter_service import FilterService
from src.services.integration_service import IntegrationService
from src.services.launch_service import LaunchService
from src.services.log_service import LogService
from src.services.project_service import ProjectService
from src.services.test_item_service import TestItemService
from src.services.user_service import UserService
from src.services.widget_service import WidgetService
from src.tools.dashboard_tools import register_dashboard_tools
from src.tools.filter_tools import register_filter_tools
from src.tools.integration_tools import register_integration_tools
from src.tools.launch_tools import register_launch_tools
from src.tools.log_tools import register_log_tools
from src.tools.project_tools import register_project_tools
from src.tools.test_item_tools import register_test_item_tools
from src.tools.user_tools import register_user_tools
from src.tools.widget_tools import register_widget_tools
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

_client: ReportPortalClient | None = None


def _build_client(config_path: Path | None = None) -> ReportPortalClient:
    """Build and return a ReportPortalClient from settings."""
    settings = create_settings(config_path)

    setup_logging(
        level=settings.logging.level,
        log_format=settings.logging.format,
    )

    token, username, password = settings.get_rp_auth()
    return ReportPortalClient(
        url=settings.get_rp_url(),
        project=settings.get_rp_project(),
        token=token,
        username=username,
        password=password,
        verify_ssl=settings.reportportal.verify_ssl,
        max_concurrent=5,
    )


@asynccontextmanager
async def _lifespan(server: FastMCP):
    """Manage the HTTP client lifecycle around the MCP server."""
    global _client
    if _client is not None:
        await _client.connect()
        logger.info("reportportal_client_connected")
    try:
        yield
    finally:
        if _client is not None:
            await _client.disconnect()
            logger.info("reportportal_client_disconnected")


mcp = FastMCP(
    "ReportPortal MCP Server",
    lifespan=_lifespan,
)


def _register_tools(client: ReportPortalClient) -> None:
    """Wire services and register all MCP tools."""
    launch_svc = LaunchService(client)
    test_item_svc = TestItemService(client)
    log_svc = LogService(client)
    dashboard_svc = DashboardService(client)
    widget_svc = WidgetService(client)
    filter_svc = FilterService(client)
    project_svc = ProjectService(client)
    user_svc = UserService(client)
    integration_svc = IntegrationService(client)

    register_launch_tools(mcp, launch_svc)
    register_test_item_tools(mcp, test_item_svc)
    register_log_tools(mcp, log_svc)
    register_dashboard_tools(mcp, dashboard_svc)
    register_widget_tools(mcp, widget_svc)
    register_filter_tools(mcp, filter_svc)
    register_project_tools(mcp, project_svc)
    register_user_tools(mcp, user_svc)
    register_integration_tools(mcp, integration_svc)


def main() -> None:
    """Entry point: build client, register tools, and start the MCP server."""
    global _client

    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    try:
        _client = _build_client(config_path)
        _register_tools(_client)
    except Exception as e:
        logger.warning(f"Failed to build ReportPortal client (tools will not be registered): {e}")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
