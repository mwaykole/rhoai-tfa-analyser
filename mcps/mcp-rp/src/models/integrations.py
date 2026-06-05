"""Pydantic models for ReportPortal Integration entities."""

from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class Integration(BaseModel):
    id: StrOrInt = Field(..., description="Integration ID")
    name: str = Field(default="")
    type: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)
    creator: str | None = Field(default=None)
    integration_parameters: dict[str, Any] = Field(
        default_factory=dict, alias="integrationParameters"
    )

    class Config:
        populate_by_name = True
