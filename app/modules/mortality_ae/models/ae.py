from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.modules.mortality_ae.models.chart import ApiChartTable


class ApiNumericBinning(StrEnum):
    UNIFORM = "uniform"
    QUINTILE = "quintile"
    CUSTOM = "custom"


class ApiAeXVariableNumeric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["numeric"] = "numeric"
    name: str
    binning: ApiNumericBinning = ApiNumericBinning.QUINTILE
    bin_count: int | None = Field(default=5, ge=2, le=20)
    custom_edges: list[float] | None = None


class ApiAeXVariableDate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["date"] = "date"
    name: str
    binning: ApiNumericBinning = ApiNumericBinning.QUINTILE
    bin_count: int | None = Field(default=5, ge=2, le=20)
    custom_edges: list[str] | None = None


class ApiCategoricalGroupDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    values: list[str]
    x_position: float | None = None


class ApiAeXVariableCategorical(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["categorical"] = "categorical"
    name: str
    grouping: Literal["all_unique", "custom"] = "all_unique"
    groups: list[ApiCategoricalGroupDefinition] | None = None
    remaining_name: str = "Remaining"
    remaining_position: float | None = None


ApiAeAtomicVariable = ApiAeXVariableNumeric | ApiAeXVariableDate | ApiAeXVariableCategorical


class ApiAeCrossGroupDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    a_any: bool = False
    a_values: list[str] = Field(default_factory=list)
    b_any: bool = False
    b_values: list[str] = Field(default_factory=list)
    x_position: float | None = None


class ApiAeXVariableCross(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["cross"] = "cross"
    a_variable: ApiAeAtomicVariable
    b_variable: ApiAeAtomicVariable
    groups: list[ApiAeCrossGroupDefinition] | None = None
    remaining_name: str = "Remaining"
    remaining_position: float | None = None


ApiAeXVariable = ApiAeAtomicVariable | ApiAeXVariableCross


class ApiAePolynomialFitParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: int = Field(default=1, ge=1, le=3)
    weighted: bool = False


class ApiAePolynomialFitResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    degree: int
    weighted: bool
    coefficients: list[float]
    r2: float | None = None
    fit_table: ApiChartTable


class ApiColumnMapping(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_number_column: str | None = None
    face_amount_column: str | None = None
    mac_column: str | None = None
    mec_column: str | None = None
    man_column: str | None = None
    men_column: str | None = None
    moc_column: str | None = None
    cola_m1_column: str | None = None


class ApiAeExclusions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exclude_cola_m1: list[str] = Field(default_factory=list)
    exclude_cola_m2_by_m1: dict[str, list[str]] = Field(default_factory=dict)


class ApiAeUnivariateParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_name: str = ""
    x_variable: ApiAeXVariable
    split_variable: ApiAeXVariable | None = None
    application_id_column: str | None = None
    column_mapping: ApiColumnMapping | None = None
    exclusions: ApiAeExclusions | None = None
    poly_fit: ApiAePolynomialFitParameters | None = None


class ApiAeUnivariateFromConfigParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config_id: str
    x_variable: ApiAeXVariable
    split_variable: ApiAeXVariable | None = None
    application_id_column: str | None = None
    exclusions: ApiAeExclusions | None = None
    poly_fit: ApiAePolynomialFitParameters | None = None


class ApiAeUnivariateRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    variable_group: str
    avg_x: float | None = None
    x_coord: float | None = None
    sample_size: int
    deaths: float
    expected_count: float = 0.0
    actual_amount: float = 0.0
    expected_amount: float = 0.0
    exposure_count: float = 0.0
    total_face_amount: float = 0.0
    ae: float | None
    ae_amount: float | None = None
    ae_ci_lower: float | None = None
    ae_ci_upper: float | None = None
    ae_amount_ci_lower: float | None = None
    ae_amount_ci_upper: float | None = None


class ApiAeColaM1StackedRow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_group: str
    total_deaths: float
    deaths_by_m1: dict[str, float]
    total_amount: float
    amounts_by_m1: dict[str, float]


class ApiAeColaM1StackedResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    causes: list[str]
    rows: list[ApiAeColaM1StackedRow]
    total_deaths: float
    total_amount: float


class ApiAeUnivariateSplitResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    split_group: str
    rows: list[ApiAeUnivariateRow]
    poly_fit: ApiAePolynomialFitResults | None = None
    cola_m1_stacked: ApiAeColaM1StackedResults | None = None


class ApiAeUnivariateResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rows: list[ApiAeUnivariateRow]
    split_results: list[ApiAeUnivariateSplitResults] | None = None
    poly_fit: ApiAePolynomialFitResults | None = None
    cola_m1_stacked: ApiAeColaM1StackedResults | None = None
