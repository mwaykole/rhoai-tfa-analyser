"""Shared Pydantic models and types for ReportPortal entities."""

from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field


def coerce_to_str(v: Any) -> str:
    """Coerce value to string (handles int IDs from RP 5.x)."""
    return str(v) if v is not None else ""


StrOrInt = Annotated[str, BeforeValidator(coerce_to_str)]


class PagedResponse(BaseModel):
    """Paged response from ReportPortal API."""

    content: list[dict[str, Any]] = Field(default_factory=list)
    page: dict[str, int] = Field(default_factory=dict)

    @property
    def total_elements(self) -> int:
        return self.page.get("totalElements", 0)

    @property
    def total_pages(self) -> int:
        return self.page.get("totalPages", 0)

    @property
    def current_page(self) -> int:
        return self.page.get("number", 0)

    @property
    def page_size(self) -> int:
        return self.page.get("size", 0)
