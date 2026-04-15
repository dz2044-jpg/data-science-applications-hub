from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.chart import ApiChartTable


class ApiMonitorFromCsvParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_column: str = "date"
    value_column: str = "deaths"
    group_column: str | None = None

    date_format: str | None = None
    min_date: dt.date | None = None
    max_date: dt.date | None = None

    rolling_window_days: int = Field(default=7, ge=1, le=365)
    baseline_window_days: int = Field(default=28, ge=2, le=3650)
    zscore_threshold: float = Field(default=2.0, ge=0.0, le=20.0)


class ApiMonitorFromDatasetParameters(ApiMonitorFromCsvParameters):
    dataset_name: str


class ApiDatasetSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: int
    days: int
    series: list[str]


class ApiAnomalyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    time_s: int
    series: str
    value: float
    zscore: float


class ApiMonitorFromCsvResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: ApiDatasetSummary
    chart_data: dict[str, ApiChartTable]
    anomalies: list[ApiAnomalyEvent]
