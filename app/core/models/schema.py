from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ApiCoreColumnKind(StrEnum):
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    DATE = "date"


class ApiCoreDatasetColumnInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ApiCoreColumnKind

    unique_values: list[str] | None = None
    unique_count: int | None = None

    numeric_min: float | None = None
    numeric_max: float | None = None

    date_min: str | None = None
    date_max: str | None = None


class ApiCoreDatasetSchemaResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str
    columns: list[ApiCoreDatasetColumnInfo]
    max_unique_values: int

