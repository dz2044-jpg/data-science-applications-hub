from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from typing import TypeAlias


class ApiSeriesFormat(StrEnum):
    NUMBER = "number"
    PERCENT = "percent"


class ApiChartColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    format: ApiSeriesFormat = ApiSeriesFormat.NUMBER


ApiChartCell: TypeAlias = int | float | None


class ApiChartTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    columns: list[ApiChartColumn]
    rows: list[list[ApiChartCell]]
