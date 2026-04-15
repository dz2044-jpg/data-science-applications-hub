from __future__ import annotations

import datetime as dt

from fastapi import UploadFile

from app.calc.monitor import compute_monitor_tables
from app.models.monitor import (
    ApiDatasetSummary,
    ApiMonitorFromCsvParameters,
    ApiMonitorFromCsvResults,
    ApiMonitorFromDatasetParameters,
)
from app.retrieve.datasets import read_dataset_bytes
from app.retrieve.data_upload import read_mortality_csv_upload
from app.utils.paths import get_data_dir


def _clamp_dates(
    *,
    min_date: dt.date | None,
    max_date: dt.date | None,
) -> tuple[dt.date | None, dt.date | None]:
    if min_date is not None and max_date is not None and max_date < min_date:
        raise ValueError("max_date must be >= min_date")
    return min_date, max_date


def perform_monitor_from_csv_bytes(
    *,
    csv_bytes: bytes,
    params: ApiMonitorFromCsvParameters,
) -> ApiMonitorFromCsvResults:
    min_date, max_date = _clamp_dates(min_date=params.min_date, max_date=params.max_date)

    df = read_mortality_csv_upload(
        csv_bytes=csv_bytes,
        date_column=params.date_column,
        value_column=params.value_column,
        group_column=params.group_column,
        date_format=params.date_format,
    )

    if min_date is not None:
        df = df[df["date"] >= dt.datetime.combine(min_date, dt.time.min)]
    if max_date is not None:
        df = df[df["date"] <= dt.datetime.combine(max_date, dt.time.min)]

    if df.empty:
        return ApiMonitorFromCsvResults(
            summary=ApiDatasetSummary(rows=0, days=0, series=[]),
            chart_data={},
            anomalies=[],
        )

    chart_data, anomalies, series = compute_monitor_tables(
        df=df,
        rolling_window_days=params.rolling_window_days,
        baseline_window_days=params.baseline_window_days,
        zscore_threshold=params.zscore_threshold,
    )

    unique_days = df["date"].nunique()
    summary = ApiDatasetSummary(rows=int(len(df)), days=int(unique_days), series=series)
    return ApiMonitorFromCsvResults(
        summary=summary,
        chart_data=chart_data,
        anomalies=anomalies,
    )


async def perform_monitor_from_csv(
    *,
    file: UploadFile,
    params: ApiMonitorFromCsvParameters,
) -> ApiMonitorFromCsvResults:
    csv_bytes = await file.read()
    return perform_monitor_from_csv_bytes(csv_bytes=csv_bytes, params=params)


def perform_monitor_from_dataset(
    *,
    params: ApiMonitorFromDatasetParameters,
) -> ApiMonitorFromCsvResults:
    file_bytes = read_dataset_bytes(
        data_dir=get_data_dir(),
        dataset_name=params.dataset_name,
    )
    csv_params = ApiMonitorFromCsvParameters.model_validate(
        params.model_dump(exclude={"dataset_name"})
    )
    return perform_monitor_from_csv_bytes(csv_bytes=file_bytes, params=csv_params)
