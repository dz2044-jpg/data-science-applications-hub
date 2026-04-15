from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.datasets import (
    ApiDatasetColaResults,
    ApiDatasetSchemaResults,
    ApiListDatasetsResults,
)
from app.service.dataset_cola import get_dataset_cola
from app.service.dataset_schema import get_dataset_schema
from app.service.datasets import list_datasets

router = APIRouter()


@router.get("/api/datasets", response_model=ApiListDatasetsResults)
def get_datasets() -> ApiListDatasetsResults:
    return list_datasets()


@router.get("/api/datasets/{dataset_name}/schema", response_model=ApiDatasetSchemaResults)
def get_dataset_schema_route(dataset_name: str) -> ApiDatasetSchemaResults:
    try:
        return get_dataset_schema(dataset_name=dataset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/datasets/{dataset_name}/cola", response_model=ApiDatasetColaResults)
def get_dataset_cola_route(dataset_name: str) -> ApiDatasetColaResults:
    try:
        return get_dataset_cola(dataset_name=dataset_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
