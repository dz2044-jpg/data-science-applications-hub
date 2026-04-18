from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.mortality_ae.models.ae import ApiAeAtomicVariable


class ApiAeInsightDrill(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_variable: ApiAeAtomicVariable
    split_variable: ApiAeAtomicVariable | None = None


class ApiAeInsightResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: list[str]
    segment_label: str
    segment_filters: dict[str, str]
    sample_size: int
    exposure_count: float
    actual_count: float
    expected_count: float
    variance_count: float
    ae_count: float | None
    actual_amount: float
    expected_amount: float
    variance_amount: float
    ae_amount: float | None
    drill: ApiAeInsightDrill


class ApiAeInsightsFromConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str
    max_results_per_metric: int = Field(default=25, ge=1, le=100)


class ApiAeInsightsResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str
    count_insights: list[ApiAeInsightResult]
    amount_insights: list[ApiAeInsightResult]
