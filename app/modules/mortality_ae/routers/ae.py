from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.ae import (
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateParameters,
    ApiAeUnivariateResults,
    ApiAeVariableLabelsParameters,
    ApiAeVariableLabelsResults,
)
from app.models.datasets import ApiDatasetSchemaResults
from app.models.insights import (
    ApiAeInsightsFromConfigRequest,
    ApiAeInsightsResults,
)
from app.service.ae_insights import perform_ae_insights_from_config
from app.service.ae_univariate import (
    perform_ae_univariate,
    perform_ae_univariate_from_config,
    perform_ae_univariate_from_upload,
)
from app.service.ae_variable_labels import perform_ae_variable_labels
from app.service.dataset_schema import get_dataset_schema_from_bytes

router = APIRouter()


@router.post("/api/ae/univariate", response_model=ApiAeUnivariateResults)
def ae_univariate(params: ApiAeUnivariateParameters) -> ApiAeUnivariateResults:
    try:
        return perform_ae_univariate(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/ae/upload-schema", response_model=ApiDatasetSchemaResults)
async def ae_upload_schema(
    file: UploadFile = File(...),
) -> ApiDatasetSchemaResults:
    try:
        file_bytes = await file.read()
        return get_dataset_schema_from_bytes(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/ae/univariate-from-config", response_model=ApiAeUnivariateResults)
def ae_univariate_from_config(
    params: ApiAeUnivariateFromConfigParameters,
) -> ApiAeUnivariateResults:
    try:
        return perform_ae_univariate_from_config(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/ae/univariate-from-csv", response_model=ApiAeUnivariateResults)
async def ae_univariate_from_csv(
    file: UploadFile = File(...),
    params: str = Form(...),
) -> ApiAeUnivariateResults:
    try:
        import json

        file_bytes = await file.read()
        params_dict = json.loads(params)
        params_obj = ApiAeUnivariateParameters(**params_dict)
        return perform_ae_univariate_from_upload(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
            params=params_obj,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/ae/variable-labels", response_model=ApiAeVariableLabelsResults)
def ae_variable_labels(
    params: ApiAeVariableLabelsParameters,
) -> ApiAeVariableLabelsResults:
    try:
        return perform_ae_variable_labels(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/ae/insights/from-config", response_model=ApiAeInsightsResults)
def ae_insights_from_config(
    params: ApiAeInsightsFromConfigRequest,
) -> ApiAeInsightsResults:
    try:
        return perform_ae_insights_from_config(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

