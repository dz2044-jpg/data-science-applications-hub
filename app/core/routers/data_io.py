from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.models.schema import ApiCoreDatasetSchemaResults
from app.core.service.schema_profile import get_core_schema_from_bytes

router = APIRouter()


@router.post("/api/core/upload-schema", response_model=ApiCoreDatasetSchemaResults)
async def core_upload_schema(
    file: UploadFile = File(...),
) -> ApiCoreDatasetSchemaResults:
    try:
        file_bytes = await file.read()
        return get_core_schema_from_bytes(
            file_bytes=file_bytes,
            filename=file.filename or "upload.csv",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

