from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LeakedKeyDrillRequest(BaseModel):
    compromised_key_id: str = Field(min_length=1)
    project_id: str | None = None
    incident_start: str = Field(min_length=1)
    incident_end: str = Field(min_length=1)
    grace_hours: int = Field(ge=0, le=24)
    search_query: str = Field(min_length=1)


class BlastRadiusSummary(BaseModel):
    total_matches: int
    build_events: int
    release_operations: int
    raw_items: list[dict[str, Any]]


class DeveloperDiagnostics(BaseModel):
    severity: str
    lines: list[str]
    recommendations: list[str]


class LeakedKeyDrillResult(BaseModel):
    compromised_key_id: str
    temp_key_id: str
    temp_key_preview: str
    blast_radius: BlastRadiusSummary
    diagnostics: list[str]
    recommendations: list[str]
