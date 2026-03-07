from __future__ import annotations

from pydantic import BaseModel, Field


class SeedModelsResult(BaseModel):
    created: int = 0
    updated: int = 0
    disabled: int = 0
    warnings: list[str] = Field(default_factory=list)
