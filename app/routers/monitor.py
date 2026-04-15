from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.monitor import (
    ApiMonitorFromCsvParameters,
    ApiMonitorFromCsvResults,
    ApiMonitorFromDatasetParameters,
)
from app.service.monitor import perform_monitor_from_csv, perform_monitor_from_dataset

router = APIRouter()


@router.post("/api/monitor/from-csv", response_model=ApiMonitorFromCsvResults)
async def monitor_from_csv(
    file: UploadFile = File(...),
    params: str = Form("{}"),
) -> ApiMonitorFromCsvResults:
    try:
        parsed_params = ApiMonitorFromCsvParameters.model_validate_json(params)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid params JSON") from exc

    try:
        return await perform_monitor_from_csv(file=file, params=parsed_params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/monitor/from-dataset", response_model=ApiMonitorFromCsvResults)
def monitor_from_dataset(
    params: ApiMonitorFromDatasetParameters,
) -> ApiMonitorFromCsvResults:
    try:
        return perform_monitor_from_dataset(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
