"""MCP tool definitions for ReportPortal TestItem operations."""

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.test_item_service import TestItemService


def register_test_item_tools(mcp: FastMCP, service: TestItemService) -> None:
    """Register all test-item-related MCP tools.

    Args:
        mcp: FastMCP server instance
        service: TestItem service
    """

    @mcp.tool()
    async def rp_list_test_items(
        launch_id: str | None = None,
        parent_id: str | None = None,
        status: str | None = None,
        item_type: str | None = None,
        name: str | None = None,
        page: int = 1,
        size: int = 50,
        sort: str = "startTime,asc",
    ) -> str:
        """List test items from ReportPortal with optional filters.

        Args:
            launch_id: Filter by launch ID
            parent_id: Filter by parent test item ID
            status: Filter by status - PASSED, FAILED, SKIPPED, INTERRUPTED, CANCELLED
            item_type: Filter by type - SUITE, TEST, STEP, BEFORE_CLASS, AFTER_METHOD, etc.
            name: Filter by name (contains match)
            page: Page number (1-based, default 1)
            size: Items per page (default 50)
            sort: Sort field and direction (default startTime,asc)
        """
        result = await service.list_test_items(
            launch_id=launch_id, parent_id=parent_id, status=status,
            item_type=item_type, name=name, page=page, size=size, sort=sort,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_test_item(item_id: str) -> str:
        """Get a specific test item by its numeric ID.

        Args:
            item_id: The numeric test item ID
        """
        result = await service.get_test_item_by_id(item_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_test_item_by_uuid(item_uuid: str) -> str:
        """Get a specific test item by its UUID.

        Args:
            item_uuid: The test item UUID
        """
        result = await service.get_test_item_by_uuid(item_uuid)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_create_test_item(
        name: str,
        start_time: str,
        item_type: str,
        launch_uuid: str,
        parent_item_uuid: str | None = None,
        description: str | None = None,
        attributes: str | None = None,
        has_stats: bool = True,
    ) -> str:
        """Create a new test item (suite, test, or step) within a launch.

        Args:
            name: Test item name
            start_time: Start time as ISO 8601 string or epoch milliseconds
            item_type: Item type - SUITE, TEST, STEP, BEFORE_CLASS, AFTER_METHOD, etc.
            launch_uuid: UUID of the parent launch
            parent_item_uuid: UUID of parent item (for child items like tests within a suite)
            description: Optional description
            attributes: JSON string of attribute list, e.g. '[{"key":"tag","value":"smoke"}]'
            has_stats: Whether the item should collect statistics (default true)
        """
        attrs = _parse_json_list(attributes)
        result = await service.create_test_item(
            name=name, start_time=start_time, item_type=item_type,
            launch_uuid=launch_uuid, parent_item_uuid=parent_item_uuid,
            description=description, attributes=attrs, has_stats=has_stats,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_finish_test_item(
        item_uuid: str,
        end_time: str,
        status: str,
        description: str | None = None,
        issue: str | None = None,
        attributes: str | None = None,
    ) -> str:
        """Finish a running test item and set its final status.

        Args:
            item_uuid: UUID of the test item to finish
            end_time: End time as ISO 8601 string or epoch milliseconds
            status: Final status - PASSED, FAILED, SKIPPED, INTERRUPTED, CANCELLED
            description: Optional updated description
            issue: JSON string of issue details, e.g. '{"issueType":"pb001","comment":"Bug found"}'
            attributes: JSON string of updated attribute list
        """
        issue_data = json.loads(issue) if issue else None
        attrs = _parse_json_list(attributes)
        result = await service.finish_test_item(
            item_uuid=item_uuid, end_time=end_time, status=status,
            description=description, issue=issue_data, attributes=attrs,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_test_item(
        item_id: str,
        description: str | None = None,
        attributes: str | None = None,
    ) -> str:
        """Update test item metadata (description, attributes).

        Args:
            item_id: The numeric test item ID
            description: Updated description
            attributes: JSON string of updated attribute list
        """
        attrs = _parse_json_list(attributes)
        result = await service.update_test_item(
            item_id=item_id, description=description, attributes=attrs,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_delete_test_item(item_id: str) -> str:
        """Delete a test item by its numeric ID.

        Args:
            item_id: The numeric test item ID to delete
        """
        result = await service.delete_test_item(item_id)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_get_test_item_history(
        item_id: str,
        history_depth: int = 10,
        filter_id: int | None = None,
    ) -> str:
        """Get execution history for a test item across multiple launches.

        Args:
            item_id: The test item ID
            history_depth: Number of historical launches to check (default 10)
            filter_id: Optional filter ID to narrow the launches
        """
        result = await service.get_test_item_history(
            item_id=item_id, history_depth=history_depth,
            filter_id=filter_id,
        )
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_update_test_item_issues(issues: str) -> str:
        """Bulk-update defect types and comments on test items.

        Args:
            issues: JSON string of issue updates list. Each element:
                     '[ {"testItemId": 123, "issue": {"issueType":"pb001","comment":"Product bug"}} ]'
        """
        issues_data = json.loads(issues)
        result = await service.update_issues(issues_data)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_link_external_issue(
        test_item_ids: str,
        issues: str,
    ) -> str:
        """Link external bug-tracker tickets to test items.

        Args:
            test_item_ids: Comma-separated numeric test item IDs (e.g. "1,2,3")
            issues: JSON string of external issues list, e.g.
                    '[{"url":"https://jira.example.com/PROJ-123","btsUrl":"https://jira.example.com","btsProject":"PROJ","ticketId":"PROJ-123"}]'
        """
        ids = [int(x.strip()) for x in test_item_ids.split(",")]
        issues_data = json.loads(issues)
        result = await service.link_external_issue(ids, issues_data)
        return json.dumps(result, default=str)

    @mcp.tool()
    async def rp_unlink_external_issue(
        test_item_ids: str,
        ticket_ids: str,
    ) -> str:
        """Unlink external bug-tracker tickets from test items.

        Args:
            test_item_ids: Comma-separated numeric test item IDs (e.g. "1,2,3")
            ticket_ids: Comma-separated ticket IDs to remove (e.g. "PROJ-123,PROJ-456")
        """
        ids = [int(x.strip()) for x in test_item_ids.split(",")]
        tickets = [t.strip() for t in ticket_ids.split(",")]
        result = await service.unlink_external_issue(ids, tickets)
        return json.dumps(result, default=str)


def _parse_json_list(value: str | None) -> list[dict[str, Any]] | None:
    if not value:
        return None
    return json.loads(value)
