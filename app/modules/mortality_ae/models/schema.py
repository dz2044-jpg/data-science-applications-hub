from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ApiColumnKind(StrEnum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATE = "date"


class ApiDatasetColumnInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ApiColumnKind

    unique_values: list[str] | None = None
    unique_count: int | None = None

    numeric_min: float | None = None
    numeric_max: float | None = None

    date_min: str | None = None
    date_max: str | None = None


class ApiColumnMappingSuggestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_number_candidates: list[str]
    face_amount_candidates: list[str]
    mac_candidates: list[str]
    mec_candidates: list[str]
    man_candidates: list[str]
    men_candidates: list[str]
    moc_candidates: list[str]
    cola_m1_candidates: list[str]


class ApiDatasetSchemaResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    columns: list[ApiDatasetColumnInfo]
    mec_column: str
    mac_column: str
    max_unique_values: int
    column_suggestions: ApiColumnMappingSuggestions | None = None
