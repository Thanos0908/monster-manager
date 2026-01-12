from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ProblemDetails(BaseModel):
    """
    Standard error payload:
      {
        "detail": "Validation failed.",
        "errors": { "field.path": ["message 1", "message 2"] }
      }
    """
    detail: str = Field(..., min_length=1)
    errors: Optional[Dict[str, List[str]]] = None

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }


class PageMeta(BaseModel):
    """Pagination metadata for list endpoints."""
    total: int = Field(ge=0)
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=200, default=20)
    sort: Optional[str] = Field(default=None, max_length=200)  # e.g., "-challenge_rating,name"

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }

    @field_validator("sort")
    @classmethod
    def _blank_sort_to_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return v.strip() or None