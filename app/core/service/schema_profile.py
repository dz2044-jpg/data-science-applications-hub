from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from app.core.models.schema import (
    ApiCoreColumnKind,
    ApiCoreDatasetColumnInfo,
    ApiCoreDatasetSchemaResults,
)
from app.service.dataframe_loader import (
    read_dataframe_from_bytes,
    read_dataframe_from_path,
)


def max_unique_values() -> int:
    raw = (os.getenv("AEMONITOR_MAX_UNIQUE_VALUES") or "").strip()
    if not raw:
        return 100
    try:
        value = int(raw)
    except ValueError:
        return 100
    return max(0, min(value, 5000))


def coerce_numeric(s: pd.Series) -> tuple[pd.Series, float]:
    coerced = pd.to_numeric(s, errors="coerce")
    non_null = int(s.notna().sum())
    if non_null == 0:
        return coerced, 0.0
    ratio = float(coerced.notna().sum()) / float(non_null)
    return coerced, ratio


def coerce_datetime(s: pd.Series) -> tuple[pd.Series, float]:
    non_null = s.dropna().astype(str).str.strip()
    sample = non_null.head(50)
    if len(sample) == 0:
        dt = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns, UTC]")
        return dt, 0.0

    has_separators = bool(sample.str.contains(r"[-/:T]", regex=True).any())
    has_digits_date = bool(sample.map(lambda x: bool(re.fullmatch(r"\d{8}", x))).any())
    if not (has_separators or has_digits_date):
        dt = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns, UTC]")
        return dt, 0.0

    dt = pd.to_datetime(s, errors="coerce", utc=True)
    non_null_count = int(s.notna().sum())
    if non_null_count == 0:
        return dt, 0.0
    ratio = float(dt.notna().sum()) / float(non_null_count)
    return dt, ratio


def build_core_dataset_schema(
    *, df: pd.DataFrame, dataset_name: str
) -> ApiCoreDatasetSchemaResults:
    max_uniques = max_unique_values()
    columns: list[ApiCoreDatasetColumnInfo] = []

    for name in df.columns.tolist():
        s = df[name]

        sample_size = min(2000, len(s))
        s_sample = s.head(sample_size) if len(s) > sample_size else s

        coerced, numeric_ratio = coerce_numeric(s_sample)
        numeric_unique = int(coerced.dropna().nunique(dropna=True))
        is_numeric = numeric_ratio >= 0.95

        if is_numeric and numeric_unique < 8:
            is_numeric = False

        if not is_numeric:
            is_string_like = pd.api.types.is_object_dtype(s.dtype) or pd.api.types.is_string_dtype(
                s.dtype
            )
            if is_string_like:
                dt, dt_ratio = coerce_datetime(s_sample)
                is_date = dt_ratio >= 0.95 and bool(dt.notna().any())
                if is_date:
                    dt_non_null = dt[dt.notna()]
                    dt_min = dt_non_null.min()
                    dt_max = dt_non_null.max()
                    columns.append(
                        ApiCoreDatasetColumnInfo(
                            name=str(name),
                            kind=ApiCoreColumnKind.DATE,
                            date_min=str(dt_min.isoformat()) if dt_min is not None else None,
                            date_max=str(dt_max.isoformat()) if dt_max is not None else None,
                        )
                    )
                    continue

        column_for_uniques = s if not is_numeric else s_sample
        non_null = column_for_uniques.dropna().astype(str)
        unique_count = int(non_null.nunique(dropna=True))
        unique_values: list[str] | None = None
        if max_uniques > 0:
            unique_values = (
                non_null.drop_duplicates().head(max_uniques).astype(str).tolist()
            )

        if not is_numeric:
            columns.append(
                ApiCoreDatasetColumnInfo(
                    name=str(name),
                    kind=ApiCoreColumnKind.CATEGORICAL,
                    unique_values=unique_values,
                    unique_count=unique_count,
                )
            )
            continue

        numeric = coerced[np.isfinite(coerced.to_numpy(dtype=float))]
        numeric_min = float(numeric.min()) if len(numeric) else None
        numeric_max = float(numeric.max()) if len(numeric) else None
        columns.append(
            ApiCoreDatasetColumnInfo(
                name=str(name),
                kind=ApiCoreColumnKind.NUMERIC,
                numeric_min=numeric_min,
                numeric_max=numeric_max,
            )
        )

    return ApiCoreDatasetSchemaResults(
        dataset_name=dataset_name,
        columns=columns,
        max_unique_values=max_uniques,
    )


def get_core_schema_from_bytes(
    *, file_bytes: bytes, filename: str
) -> ApiCoreDatasetSchemaResults:
    df = read_dataframe_from_bytes(
        file_bytes=file_bytes,
        filename=filename,
        nrows=6000,
        random_sample=True,
    )
    return build_core_dataset_schema(df=df, dataset_name=filename)


def get_core_schema_from_path(
    *, file_path: Path, dataset_name: str
) -> ApiCoreDatasetSchemaResults:
    df = read_dataframe_from_path(
        file_path=file_path,
        nrows=6000,
        random_sample=True,
    )
    return build_core_dataset_schema(df=df, dataset_name=dataset_name)

