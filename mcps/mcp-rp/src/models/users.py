"""Pydantic models for ReportPortal User entities."""

from typing import Any

from pydantic import BaseModel, Field

from src.models.common import StrOrInt


class User(BaseModel):
    id: StrOrInt = Field(..., description="User ID")
    user_id: str = Field(default="", alias="userId")
    email: str = Field(default="")
    full_name: str = Field(default="", alias="fullName")
    account_type: str = Field(default="", alias="accountType")
    user_role: str = Field(default="", alias="userRole")
    assigned_projects: dict[str, Any] = Field(
        default_factory=dict, alias="assignedProjects"
    )

    class Config:
        populate_by_name = True
