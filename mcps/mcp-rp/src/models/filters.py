"""Pydantic models for ReportPortal UserFilter entities."""

from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class FilterCondition(BaseModel):
    filtering_field: str = Field(..., alias="filteringField")
    condition: str = Field(...)
    value: str = Field(...)

    class Config:
        populate_by_name = True


class FilterOrder(BaseModel):
    sorting_column: str = Field(..., alias="sortingColumn")
    is_asc: bool = Field(default=False, alias="isAsc")

    class Config:
        populate_by_name = True


class UserFilter(BaseModel):
    id: StrOrInt = Field(..., description="Filter ID")
    name: str = Field(..., description="Filter name")
    type: str = Field(default="launch")
    description: str | None = Field(default=None)
    owner: str | None = Field(default=None)
    conditions: list[dict[str, Any]] = Field(default_factory=list)
    orders: list[dict[str, Any]] = Field(default_factory=list)

    class Config:
        populate_by_name = True
