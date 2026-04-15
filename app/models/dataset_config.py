from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ModuleId(StrEnum):
    """Analysis module identifiers supported by the hub."""

    MORTALITY_AE = "mortality_ae"
    BINARY_FEATURE_AE = "binary_feature_ae"


class PerformanceType(StrEnum):
    """Types of performance analyses supported by the system."""

    MORTALITY_AE = "Mortality A/E Analysis"
    BINARY_FEATURE_AE = "Binary Feature Mortality A/E"


class ApiMortalityAeModuleConfig(BaseModel):
    """Column mappings for Mortality A/E Analysis."""

    model_config = ConfigDict(extra="forbid")

    policy_number_column: str | None = None
    face_amount_column: str | None = None
    mac_column: str
    mec_column: str
    man_column: str
    men_column: str
    moc_column: str | None = None
    cola_m1_column: str | None = None


ApiColumnMapping = ApiMortalityAeModuleConfig


class ApiBinaryFeatureAeModuleConfig(BaseModel):
    """Column mappings for the Binary Feature Mortality A/E module."""

    model_config = ConfigDict(extra="forbid")

    rule: str
    RuleName: str
    first_date: str
    category: str
    hit_count: str
    hit_rate: str
    claim_count: str
    mec_sum: str
    ae_ratio: str
    ci_lower_95: str
    ci_upper_95: str
    ci_lower_90: str
    ci_upper_90: str
    ci_lower_80: str
    ci_upper_80: str
    cola_cancer_pct: str
    cola_heart_pct: str
    cola_nervous_system_pct: str
    cola_non_natural_pct: str
    cola_other_medical_pct: str
    cola_respiratory_pct: str
    cola_others_pct: str


ApiModuleConfig = ApiMortalityAeModuleConfig | ApiBinaryFeatureAeModuleConfig


_MODULE_TO_PERFORMANCE_TYPE: dict[ModuleId, PerformanceType] = {
    ModuleId.MORTALITY_AE: PerformanceType.MORTALITY_AE,
    ModuleId.BINARY_FEATURE_AE: PerformanceType.BINARY_FEATURE_AE,
}


def performance_type_for_module(module_id: ModuleId) -> PerformanceType:
    return _MODULE_TO_PERFORMANCE_TYPE[module_id]


def infer_module_id_for_performance_type(performance_type: PerformanceType) -> ModuleId:
    if performance_type == PerformanceType.BINARY_FEATURE_AE:
        return ModuleId.BINARY_FEATURE_AE
    return ModuleId.MORTALITY_AE


class ApiDatasetConfig(BaseModel):
    """A saved dataset configuration."""

    model_config = ConfigDict(extra="forbid")

    id: str
    dataset_name: str
    performance_type: PerformanceType
    file_path: str
    module_id: ModuleId = ModuleId.MORTALITY_AE
    module_config: ApiModuleConfig
    created_date: datetime

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        raw = dict(data)
        performance_type = raw.get("performance_type")

        if "module_id" not in raw:
            if performance_type is not None:
                raw["module_id"] = infer_module_id_for_performance_type(
                    PerformanceType(performance_type)
                )
            else:
                raw["module_id"] = ModuleId.MORTALITY_AE

        if "module_config" not in raw and "column_mapping" in raw:
            raw["module_config"] = raw["column_mapping"]

        raw.pop("column_mapping", None)

        if "performance_type" not in raw and "module_id" in raw:
            raw["performance_type"] = performance_type_for_module(ModuleId(raw["module_id"]))

        return raw

    @model_validator(mode="after")
    def _validate_module_config(self) -> "ApiDatasetConfig":
        if self.module_id == ModuleId.MORTALITY_AE and not isinstance(
            self.module_config, ApiMortalityAeModuleConfig
        ):
            raise ValueError("Mortality A/E configs require a mortality module_config")

        if self.module_id == ModuleId.BINARY_FEATURE_AE and not isinstance(
            self.module_config, ApiBinaryFeatureAeModuleConfig
        ):
            raise ValueError(
                "Binary Feature Mortality A/E configs require a binary feature module_config"
            )

        return self


class ApiCreateDatasetConfigRequest(BaseModel):
    """Request to create a new dataset configuration."""

    model_config = ConfigDict(extra="forbid")

    dataset_name: str = Field(min_length=1, max_length=200)
    performance_type: PerformanceType
    file_path: str
    module_id: ModuleId = ModuleId.MORTALITY_AE
    module_config: ApiModuleConfig

    @model_validator(mode="before")
    @classmethod
    def _migrate_legacy_payload(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        raw = dict(data)
        performance_type = raw.get("performance_type")

        if "module_id" not in raw:
            if performance_type is not None:
                raw["module_id"] = infer_module_id_for_performance_type(
                    PerformanceType(performance_type)
                )
            else:
                raw["module_id"] = ModuleId.MORTALITY_AE

        if "module_config" not in raw and "column_mapping" in raw:
            raw["module_config"] = raw["column_mapping"]

        raw.pop("column_mapping", None)

        if "performance_type" not in raw and "module_id" in raw:
            raw["performance_type"] = performance_type_for_module(ModuleId(raw["module_id"]))

        return raw

    @model_validator(mode="after")
    def _validate_module_config(self) -> "ApiCreateDatasetConfigRequest":
        if self.module_id == ModuleId.MORTALITY_AE and not isinstance(
            self.module_config, ApiMortalityAeModuleConfig
        ):
            raise ValueError("Mortality A/E configs require a mortality module_config")

        if self.module_id == ModuleId.BINARY_FEATURE_AE and not isinstance(
            self.module_config, ApiBinaryFeatureAeModuleConfig
        ):
            raise ValueError(
                "Binary Feature Mortality A/E configs require a binary feature module_config"
            )

        return self


class ApiListDatasetConfigsResults(BaseModel):
    """Response containing list of dataset configurations."""

    model_config = ConfigDict(extra="forbid")

    configs: list[ApiDatasetConfig]


def get_mortality_module_config(
    config: ApiDatasetConfig,
) -> ApiMortalityAeModuleConfig:
    if not isinstance(config.module_config, ApiMortalityAeModuleConfig):
        raise ValueError(
            f"Config '{config.id}' is for module '{config.module_id}', not mortality_ae"
        )
    return config.module_config


def get_binary_feature_module_config(
    config: ApiDatasetConfig,
) -> ApiBinaryFeatureAeModuleConfig:
    if not isinstance(config.module_config, ApiBinaryFeatureAeModuleConfig):
        raise ValueError(
            f"Config '{config.id}' is for module '{config.module_id}', not binary_feature_ae"
        )
    return config.module_config
