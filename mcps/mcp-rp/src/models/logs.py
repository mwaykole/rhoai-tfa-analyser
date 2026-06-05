"""Pydantic models for ReportPortal Log entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    FATAL = "FATAL"


class LogEntry(BaseModel):
    id: StrOrInt = Field(..., description="Log entry ID")
    uuid: str | None = Field(default=None)
    item_id: StrOrInt = Field(default="", alias="itemId")
    launch_id: StrOrInt = Field(default="", alias="launchId")
    time: datetime | None = Field(default=None, alias="logTime")
    level: str = Field(default="INFO")
    message: str = Field(default="")
    binary_content: dict[str, Any] | None = Field(default=None, alias="binaryContent")

    class Config:
        use_enum_values = True
        populate_by_name = True
