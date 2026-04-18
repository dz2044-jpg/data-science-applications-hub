from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.modules.mortality_ae.models.ae import (
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateParameters,
    ApiAeUnivariateResults,
)
from app.modules.mortality_ae.models.insights import (
    ApiAeInsightsFromConfigRequest,
    ApiAeInsightsResults,
)
from app.modules.mortality_ae.models.schema import ApiDatasetSchemaResults
from app.modules.mortality_ae.service.ae_insights import (
    perform_ae_insights_from_config,
)
from app.modules.mortality_ae.service.ae_univariate import (
    perform_ae_univariate_from_config,
    perform_ae_univariate_from_upload,
)
from app.modules.mortality_ae.service.dataset_schema import (
    get_dataset_schema_from_bytes,
)

router = APIRouter()


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


@router.post("/api/ae/insights/from-config", response_model=ApiAeInsightsResults)
def ae_insights_from_config(
    params: ApiAeInsightsFromConfigRequest,
) -> ApiAeInsightsResults:
    try:
        return perform_ae_insights_from_config(params=params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
