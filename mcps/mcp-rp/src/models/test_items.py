"""Pydantic models for ReportPortal TestItem entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class TestStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    INTERRUPTED = "INTERRUPTED"
    CANCELLED = "CANCELLED"


class TestItemType(str, Enum):
    SUITE = "SUITE"
    STORY = "STORY"
    TEST = "TEST"
    SCENARIO = "SCENARIO"
    STEP = "STEP"
    BEFORE_CLASS = "BEFORE_CLASS"
    BEFORE_GROUPS = "BEFORE_GROUPS"
    BEFORE_METHOD = "BEFORE_METHOD"
    BEFORE_SUITE = "BEFORE_SUITE"
    BEFORE_TEST = "BEFORE_TEST"
    AFTER_CLASS = "AFTER_CLASS"
    AFTER_GROUPS = "AFTER_GROUPS"
    AFTER_METHOD = "AFTER_METHOD"
    AFTER_SUITE = "AFTER_SUITE"
    AFTER_TEST = "AFTER_TEST"


class TestItem(BaseModel):
    id: StrOrInt = Field(..., description="Test item ID")
    uuid: str | None = Field(default=None)
    name: str = Field(..., description="Test item name")
    type: str = Field(..., description="Test item type")
    status: str = Field(..., description="Test status")
    launch_id: StrOrInt = Field(..., alias="launchId")
    parent_id: StrOrInt | None = Field(default=None, alias="parentId")
    path_names: dict[str, Any] | None = Field(default=None, alias="pathNames")
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    description: str | None = Field(default=None)
    attributes: list[dict[str, str]] = Field(default_factory=list)
    issue: dict[str, Any] | None = Field(default=None)
    has_logs: bool = Field(default=False, alias="hasLogs")
    has_stats: bool = Field(default=False, alias="hasStats")
    statistics: dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        populate_by_name = True


class IssueUpdate(BaseModel):
    """Payload for updating issue on a test item."""

    test_item_id: int = Field(..., alias="testItemId")
    issue: dict[str, Any] = Field(...)

    class Config:
        populate_by_name = True
