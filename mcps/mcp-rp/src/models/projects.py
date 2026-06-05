"""Pydantic models for ReportPortal Project entities."""

from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class ProjectConfiguration(BaseModel):
    entry_type: str | None = Field(default=None, alias="entryType")
    statistical_enabled: bool = Field(default=True, alias="statisticalEnabled")
    subtype: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class Project(BaseModel):
    id: StrOrInt = Field(..., description="Project ID")
    project_name: str = Field(..., alias="projectName")
    entry_type: str | None = Field(default=None, alias="entryType")
    configuration: dict[str, Any] = Field(default_factory=dict)
    users: list[dict[str, Any]] = Field(default_factory=list)
    creation_date: str | None = Field(default=None, alias="creationDate")

    class Config:
        populate_by_name = True
