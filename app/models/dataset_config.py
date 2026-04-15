from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PerformanceType(StrEnum):
    """Types of performance analyses supported by the system."""
    MORTALITY_AE = "Mortality A/E Analysis"


class ApiColumnMapping(BaseModel):
    """Column mappings for Mortality A/E Analysis."""
    model_config = ConfigDict(extra="forbid")
    
    # Optional fields
    policy_number_column: str | None = None
    face_amount_column: str | None = None
    
    # Required fields for Mortality A/E
    mac_column: str
    mec_column: str
    man_column: str
    men_column: str
    
    # Optional fields
    moc_column: str | None = None
    cola_m1_column: str | None = None


class ApiDatasetConfig(BaseModel):
    """A saved dataset configuration."""
    model_config = ConfigDict(extra="forbid")
    
    id: str
    dataset_name: str
    performance_type: PerformanceType
    file_path: str
    column_mapping: ApiColumnMapping
    created_date: datetime


class ApiCreateDatasetConfigRequest(BaseModel):
    """Request to create a new dataset configuration."""
    model_config = ConfigDict(extra="forbid")
    
    dataset_name: str = Field(min_length=1, max_length=200)
    performance_type: PerformanceType
    file_path: str
    column_mapping: ApiColumnMapping


class ApiListDatasetConfigsResults(BaseModel):
    """Response containing list of dataset configurations."""
    model_config = ConfigDict(extra="forbid")
    
    configs: list[ApiDatasetConfig]
