from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.models.dataset_config import (
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
    ApiMortalityAeModuleConfig,
    ModuleId,
    PerformanceType,
)
from app.core.service.dataset_config import (
    create_dataset_config,
    delete_dataset_config,
    get_dataset_config,
    list_dataset_configs,
    save_uploaded_file,
)
from app.modules.mortality_ae.models.schema import ApiDatasetSchemaResults
from app.modules.mortality_ae.service.dataset_schema import get_dataset_config_schema

router = APIRouter()


@router.get("/api/dataset-configs", response_model=ApiListDatasetConfigsResults)
def get_dataset_configs() -> ApiListDatasetConfigsResults:
    return list_dataset_configs()


@router.post("/api/dataset-configs", response_model=ApiDatasetConfig, status_code=201)
async def create_dataset_config_route(
    dataset_name: str = Form(...),
    performance_type: str = Form(...),
    module_id: str = Form(...),
    module_config_json: str = Form(...),
    file: UploadFile = File(...),
) -> ApiDatasetConfig:
    try:
        parsed_module_id = ModuleId(module_id)
        module_config_dict = json.loads(module_config_json)
        if parsed_module_id == ModuleId.BINARY_FEATURE_AE:
            module_config = ApiBinaryFeatureAeModuleConfig(**module_config_dict)
        else:
            module_config = ApiMortalityAeModuleConfig(**module_config_dict)

        filename = Path(file.filename or "uploaded_file").name or "uploaded_file"
        request = ApiCreateDatasetConfigRequest(
            dataset_name=dataset_name,
            performance_type=PerformanceType(performance_type),
            module_id=parsed_module_id,
            file_path=filename,
            module_config=module_config,
        )

        config = create_dataset_config(request)
        save_uploaded_file(config.id, file.file, filename)
        return config
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid module_config JSON: {str(exc)}",
        ) from exc


@router.get("/api/dataset-configs/{config_id}", response_model=ApiDatasetConfig)
def get_dataset_config_route(config_id: str) -> ApiDatasetConfig:
    config = get_dataset_config(config_id)
    if config is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset config '{config_id}' not found",
        )
    return config


@router.get(
    "/api/dataset-configs/{config_id}/schema",
    response_model=ApiDatasetSchemaResults,
)
def get_dataset_config_schema_route(config_id: str) -> ApiDatasetSchemaResults:
    try:
        return get_dataset_config_schema(config_id=config_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/dataset-configs/{config_id}", status_code=204)
def delete_dataset_config_route(config_id: str) -> None:
    deleted = delete_dataset_config(config_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset config '{config_id}' not found",
        )
