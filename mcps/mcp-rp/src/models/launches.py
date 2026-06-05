"""Pydantic models for ReportPortal Launch entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class LaunchStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    INTERRUPTED = "INTERRUPTED"


class LaunchMode(str, Enum):
    DEFAULT = "DEFAULT"
    DEBUG = "DEBUG"


class Launch(BaseModel):
    id: StrOrInt = Field(..., description="Launch ID")
    uuid: str | None = Field(default=None, description="Launch UUID")
    name: str = Field(..., description="Launch name")
    number: int = Field(default=0, description="Launch number")
    status: str = Field(..., description="Launch status")
    start_time: datetime | None = Field(default=None, alias="startTime")
    end_time: datetime | None = Field(default=None, alias="endTime")
    description: str | None = Field(default=None)
    mode: str = Field(default="DEFAULT")
    attributes: list[dict[str, str]] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)
    rerun: bool = Field(default=False)

    class Config:
        use_enum_values = True
        populate_by_name = True
