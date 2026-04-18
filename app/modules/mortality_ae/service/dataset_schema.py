from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.core.models.schema import (
    ApiCoreColumnKind,
    ApiCoreDatasetSchemaResults,
)
from app.core.service.schema_profile import (
    build_core_dataset_schema,
    get_core_schema_from_bytes,
    max_unique_values,
)
from app.core.service.dataframe_loader import (
    read_dataframe_from_bytes,
    read_dataframe_from_path,
)
from app.core.service.dataset_config import get_dataset_config_with_file
from app.modules.mortality_ae.models.schema import (
    ApiColumnKind,
    ApiColumnMappingSuggestions,
    ApiDatasetColumnInfo,
    ApiDatasetSchemaResults,
)

MEC_COLUMN = "MEC"
MAC_COLUMN = "MAC"
MAN_COLUMN = "MAN"
MEN_COLUMN = "MEN"
MOC_COLUMN = "MOC"
COLA_M1_COLUMN = "COLA_M1"
COLA_M2_COLUMN = "COLA_M2"


def _detect_column_candidates(df: pd.DataFrame) -> ApiColumnMappingSuggestions:
    cols_lower = {str(c).lower(): str(c) for c in df.columns.tolist()}
    numeric_cols: list[str] = []

    policy_candidates = []
    policy_patterns = [
        "policy_number",
        "policynumber",
        "policy_num",
        "policynum",
        "application_number",
        "applicationnumber",
        "application_num",
        "applicationnum",
        "app_number",
        "appnumber",
        "app_num",
        "appnum",
        "policy_id",
        "policyid",
        "application_id",
        "applicationid",
        "app_id",
        "appid",
        "record_id",
        "recordid",
        "id",
    ]
    for pattern in policy_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in policy_candidates:
            policy_candidates.append(cols_lower[pattern])

    face_amount_candidates = []
    face_patterns = [
        "face",
        "face_amount",
        "faceamount",
        "face_amt",
        "faceamt",
        "sum_assured",
        "sumassured",
        "coverage",
        "coverage_amount",
        "coverageamount",
    ]
    for pattern in face_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in face_amount_candidates:
            face_amount_candidates.append(cols_lower[pattern])

    mac_candidates = []
    mac_patterns = [
        "mac",
        "actual_count",
        "actualcount",
        "actual_deaths",
        "actualdeaths",
        "deaths",
        "death_count",
    ]
    for pattern in mac_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in mac_candidates:
            mac_candidates.append(cols_lower[pattern])

    mec_candidates = []
    mec_patterns = [
        "mec",
        "expected_count",
        "expectedcount",
        "expected_deaths",
        "expecteddeaths",
    ]
    for pattern in mec_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in mec_candidates:
            mec_candidates.append(cols_lower[pattern])

    man_candidates = []
    man_patterns = [
        "man",
        "maf",
        "actual_amount",
        "actualamount",
        "actual_face",
        "actualface",
        "death_amount",
        "deathamount",
    ]
    for pattern in man_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in man_candidates:
            man_candidates.append(cols_lower[pattern])

    men_candidates = []
    men_patterns = [
        "men",
        "mef",
        "expected_amount",
        "expectedamount",
        "expected_face",
        "expectedface",
    ]
    for pattern in men_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in men_candidates:
            men_candidates.append(cols_lower[pattern])

    moc_candidates = []
    moc_patterns = [
        "moc",
        "exposure",
        "exposure_count",
        "exposurecount",
        "lives",
        "policy_count",
        "policycount",
    ]
    for pattern in moc_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in moc_candidates:
            moc_candidates.append(cols_lower[pattern])

    cola_m1_candidates = []
    cola_patterns = [
        "cola_m1",
        "cola_m2",
        "cola",
        "cause",
        "cause_of_death",
        "causeofdeath",
        "death_cause",
        "deathcause",
        "cod",
    ]
    for pattern in cola_patterns:
        if pattern in cols_lower and cols_lower[pattern] not in cola_m1_candidates:
            cola_m1_candidates.append(cols_lower[pattern])

    if (
        not mac_candidates
        or not mec_candidates
        or not man_candidates
        or not men_candidates
        or not moc_candidates
    ):
        for col in df.columns:
            col_str = str(col)
            if pd.api.types.is_numeric_dtype(df[col].dtype):
                numeric_cols.append(col_str)

    all_cols = [str(c) for c in df.columns.tolist()]

    if not policy_candidates:
        policy_candidates = all_cols
    if not face_amount_candidates:
        face_amount_candidates = numeric_cols if numeric_cols else all_cols
    if not man_candidates:
        man_candidates = numeric_cols if numeric_cols else all_cols
    if not men_candidates:
        men_candidates = numeric_cols if numeric_cols else all_cols
    if not moc_candidates:
        moc_candidates = numeric_cols if numeric_cols else all_cols
    if not cola_m1_candidates:
        cola_m1_candidates = all_cols

    return ApiColumnMappingSuggestions(
        policy_number_candidates=policy_candidates,
        face_amount_candidates=face_amount_candidates,
        mac_candidates=mac_candidates,
        mec_candidates=mec_candidates,
        man_candidates=man_candidates,
        men_candidates=men_candidates,
        moc_candidates=moc_candidates,
        cola_m1_candidates=cola_m1_candidates,
    )


def _to_mortality_columns(
    *, core_schema: ApiCoreDatasetSchemaResults, df: pd.DataFrame
) -> list[ApiDatasetColumnInfo]:
    mortality_numeric_names = {MEC_COLUMN, MAC_COLUMN, MAN_COLUMN, MEN_COLUMN}
    columns: list[ApiDatasetColumnInfo] = []

    for column in core_schema.columns:
        if column.name in mortality_numeric_names:
            numeric = pd.to_numeric(df[column.name], errors="coerce")
            finite = numeric[pd.notna(numeric)]
            numeric_min = float(finite.min()) if len(finite) else None
            numeric_max = float(finite.max()) if len(finite) else None
            columns.append(
                ApiDatasetColumnInfo(
                    name=column.name,
                    kind=ApiColumnKind.NUMERIC,
                    numeric_min=numeric_min,
                    numeric_max=numeric_max,
                )
            )
            continue

        if column.kind == ApiCoreColumnKind.NUMERIC:
            columns.append(
                ApiDatasetColumnInfo(
                    name=column.name,
                    kind=ApiColumnKind.NUMERIC,
                    numeric_min=column.numeric_min,
                    numeric_max=column.numeric_max,
                )
            )
            continue

        if column.kind == ApiCoreColumnKind.DATE:
            columns.append(
                ApiDatasetColumnInfo(
                    name=column.name,
                    kind=ApiColumnKind.DATE,
                    date_min=column.date_min,
                    date_max=column.date_max,
                )
            )
            continue

        columns.append(
            ApiDatasetColumnInfo(
                name=column.name,
                kind=ApiColumnKind.CATEGORICAL,
                unique_values=column.unique_values,
                unique_count=column.unique_count,
            )
        )

    return columns


def _build_dataset_schema(*, df: pd.DataFrame, dataset_name: str) -> ApiDatasetSchemaResults:
    core_schema = build_core_dataset_schema(df=df, dataset_name=dataset_name)
    column_suggestions = _detect_column_candidates(df)

    if not column_suggestions.mac_candidates or not column_suggestions.mec_candidates:
        raise ValueError(
            "Could not detect mortality count columns. Expected MAC/MEC or a "
            "recognized actual/expected count alias."
        )

    mec_column = MEC_COLUMN if MEC_COLUMN in df.columns else column_suggestions.mec_candidates[0]
    mac_column = MAC_COLUMN if MAC_COLUMN in df.columns else column_suggestions.mac_candidates[0]

    return ApiDatasetSchemaResults(
        dataset_name=dataset_name,
        columns=_to_mortality_columns(core_schema=core_schema, df=df),
        mec_column=mec_column,
        mac_column=mac_column,
        max_unique_values=max_unique_values(),
        column_suggestions=column_suggestions,
    )


def get_dataset_schema_from_bytes(*, file_bytes: bytes, filename: str) -> ApiDatasetSchemaResults:
    df = read_dataframe_from_bytes(
        file_bytes=file_bytes,
        filename=filename,
        nrows=6000,
        random_sample=True,
    )
    return _build_dataset_schema(df=df, dataset_name=filename)


def get_dataset_schema_from_path(*, file_path: Path, dataset_name: str) -> ApiDatasetSchemaResults:
    df = read_dataframe_from_path(
        file_path=file_path,
        nrows=6000,
        random_sample=True,
    )
    return _build_dataset_schema(df=df, dataset_name=dataset_name)


def get_generic_dataset_schema_from_bytes(*, file_bytes: bytes, filename: str) -> ApiCoreDatasetSchemaResults:
    return get_core_schema_from_bytes(file_bytes=file_bytes, filename=filename)


def get_dataset_config_schema(*, config_id: str) -> ApiDatasetSchemaResults:
    config, file_path = get_dataset_config_with_file(config_id)
    return get_dataset_schema_from_path(
        file_path=file_path,
        dataset_name=config.dataset_name,
    )
