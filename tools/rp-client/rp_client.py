#!/usr/bin/env python3
"""ReportPortal v5.x REST API client.

Used as fallback when the ReportPortal MCP server is not available
(e.g., inside containers). In local/Cursor mode, prefer the MCP tools.

Environment variables:
    RP_URL        - ReportPortal server URL
    RP_PROJECT    - Project name
    RP_USERNAME   - Username (for basic auth)
    RP_PASSWORD   - Password (for basic auth)
    RP_TOKEN      - API bearer token (preferred over username/password)
"""

import os
import sys
import urllib3
from typing import Any

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RPClient:
    """Synchronous ReportPortal v5 API client."""

    def __init__(
        self,
        url: str | None = None,
        project: str | None = None,
        token: str | None = None,
        verify_ssl: bool = False,
    ):
        self.url = (url or os.environ.get("RP_URL", "")).rstrip("/")
        self.project = project or os.environ.get("RP_PROJECT", "")
        self.token = token or os.environ.get("RP_TOKEN", "")
        self.verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.verify = verify_ssl
        if self.token:
            self._session.headers["Authorization"] = f"Bearer {self.token}"

    @property
    def _api_base(self) -> str:
        return f"{self.url}/api/v1/{self.project}"

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        resp = self._session.get(f"{self._api_base}{path}", params=params)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, json_data: Any) -> dict[str, Any]:
        resp = self._session.put(f"{self._api_base}{path}", json=json_data)
        resp.raise_for_status()
        return resp.json()

    def get_launch(self, launch_id: int) -> dict[str, Any]:
        """Get launch details by numeric ID."""
        return self._get(f"/launch/{launch_id}")

    def get_test_items(
        self,
        launch_id: int,
        status: str | None = None,
        item_type: str | None = None,
        parent_id: int | None = None,
        page: int = 1,
        size: int = 300,
    ) -> dict[str, Any]:
        """Get test items for a launch."""
        params: dict[str, Any] = {
            "filter.eq.launchId": launch_id,
            "page.page": page,
            "page.size": size,
            "page.sort": "startTime,asc",
        }
        if status:
            params["filter.eq.status"] = status
        if item_type:
            params["filter.eq.type"] = item_type
        if parent_id:
            params["filter.eq.parentId"] = parent_id
        return self._get("/item", params)

    def get_logs(
        self,
        item_id: int,
        level: str | None = None,
        page: int = 1,
        size: int = 50,
    ) -> dict[str, Any]:
        """Get logs for a test item."""
        params: dict[str, Any] = {
            "filter.eq.item": item_id,
            "page.page": page,
            "page.size": size,
            "page.sort": "logTime,asc",
        }
        if level:
            params["filter.eq.level"] = level
        return self._get("/log", params)

    def update_defect_types(self, issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk update defect types on test items."""
        return self._put("/item", {"issues": issues})

    def get_failed_items_with_logs(
        self, launch_id: int, parent_id: int | None = None, max_logs: int = 20
    ) -> list[dict[str, Any]]:
        """Get failed test items enriched with error logs."""
        result = self.get_test_items(launch_id, status="FAILED", parent_id=parent_id)
        items = result.get("content", [])

        for item in items:
            log_result = self.get_logs(item["id"], level="ERROR", size=max_logs)
            error_logs = log_result.get("content", [])
            if not error_logs:
                log_result = self.get_logs(item["id"], size=max_logs)
                error_logs = log_result.get("content", [])
            item["logs"] = error_logs

        return items
