from __future__ import annotations

import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.models.dataset_config import (
    ApiColumnMapping,
    ApiCreateDatasetConfigRequest,
    ApiDatasetConfig,
    ApiListDatasetConfigsResults,
    PerformanceType,
)
from app.models.datasets import ApiDatasetSchemaResults
from app.service.dataset_config import (
    create_dataset_config,
    delete_dataset_config,
    get_config_file_path,
    get_dataset_config,
    list_dataset_configs,
    save_uploaded_file,
)
from app.service.dataset_schema import get_dataset_config_schema

router = APIRouter()


@router.get("/api/dataset-configs", response_model=ApiListDatasetConfigsResults)
def get_dataset_configs() -> ApiListDatasetConfigsResults:
    return list_dataset_configs()


@router.post("/api/dataset-configs", response_model=ApiDatasetConfig, status_code=201)
async def create_dataset_config_route(
    dataset_name: str = Form(...),
    performance_type: str = Form(...),
    column_mapping_json: str = Form(...),
    file: UploadFile = File(...),
) -> ApiDatasetConfig:
    try:
        column_mapping_dict = json.loads(column_mapping_json)
        column_mapping = ApiColumnMapping(**column_mapping_dict)

        request = ApiCreateDatasetConfigRequest(
            dataset_name=dataset_name,
            performance_type=PerformanceType(performance_type),
            file_path=file.filename or "uploaded_file",
            column_mapping=column_mapping,
        )

        config = create_dataset_config(request)
        save_uploaded_file(config.id, file.file, file.filename or "uploaded_file")
        return config
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid column_mapping JSON: {str(exc)}",
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


@router.get("/api/dataset-configs/{config_id}/file")
def get_dataset_config_file(config_id: str) -> FileResponse:
    file_path = get_config_file_path(config_id)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"File for config '{config_id}' not found",
        )

    ext = file_path.suffix.lower()
    media_type_map = {
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".parquet": "application/octet-stream",
    }
    media_type = media_type_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=media_type,
    )
