"""Pydantic models for ReportPortal Dashboard and Widget entities."""

from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class Widget(BaseModel):
    id: StrOrInt = Field(..., description="Widget ID")
    name: str = Field(..., description="Widget name")
    widget_type: str = Field(default="", alias="widgetType")
    description: str | None = Field(default=None)
    content_parameters: dict[str, Any] = Field(
        default_factory=dict, alias="contentParameters"
    )
    filter_ids: list[int] = Field(default_factory=list, alias="filterIds")
    widget_options: dict[str, Any] = Field(
        default_factory=dict, alias="widgetOptions"
    )
    widget_size: dict[str, int] = Field(
        default_factory=dict, alias="widgetSize"
    )
    widget_position: dict[str, int] = Field(
        default_factory=dict, alias="widgetPosition"
    )

    class Config:
        populate_by_name = True


class Dashboard(BaseModel):
    id: StrOrInt = Field(..., description="Dashboard ID")
    name: str = Field(..., description="Dashboard name")
    description: str | None = Field(default=None)
    owner: str | None = Field(default=None)
    widgets: list[dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
