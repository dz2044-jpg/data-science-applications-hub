from __future__ import annotations

import numpy as np
import pandas as pd

from app.models.chart import ApiChartColumn, ApiChartTable, ApiSeriesFormat
from app.models.monitor import ApiAnomalyEvent


def _pivot_daily(df: pd.DataFrame) -> pd.DataFrame:
    pivot = df.pivot_table(
        index="date",
        columns="series",
        values="value",
        aggfunc="sum",
    ).sort_index()
    pivot.index = pd.to_datetime(pivot.index).normalize()

    full_index = pd.date_range(
        start=pivot.index.min(),
        end=pivot.index.max(),
        freq="D",
    )
    return pivot.reindex(full_index)


def _to_unix_seconds(index: pd.DatetimeIndex) -> np.ndarray:
    nanos = index.view("int64")
    return (nanos // 1_000_000_000).astype(np.int64)


def _to_chart_table(
    *,
    time_s: np.ndarray,
    values: pd.DataFrame,
    series_format: ApiSeriesFormat,
) -> ApiChartTable:
    columns = [ApiChartColumn(name="time_s", format=ApiSeriesFormat.NUMBER)]
    columns.extend(
        ApiChartColumn(name=str(name), format=series_format)
        for name in values.columns.tolist()
    )

    value_matrix = values.to_numpy(dtype=float)
    value_matrix = np.where(np.isfinite(value_matrix), value_matrix, np.nan)

    rows: list[list[int | float | None]] = []
    for row_time, row_values in zip(time_s.tolist(), value_matrix.tolist(), strict=True):
        rows.append(
            [int(row_time)]
            + [
                None if (v is None or np.isnan(v)) else float(v)
                for v in row_values
            ]
        )

    return ApiChartTable(columns=columns, rows=rows)


def compute_monitor_tables(
    *,
    df: pd.DataFrame,
    rolling_window_days: int,
    baseline_window_days: int,
    zscore_threshold: float,
) -> tuple[dict[str, ApiChartTable], list[ApiAnomalyEvent], list[str]]:
    pivot = _pivot_daily(df)
    series_names = [str(s) for s in pivot.columns.tolist()]
    time_s = _to_unix_seconds(pivot.index)

    raw_chart = _to_chart_table(
        time_s=time_s,
        values=pivot,
        series_format=ApiSeriesFormat.NUMBER,
    )

    rolling_mean = pivot.rolling(
        window=rolling_window_days,
        min_periods=1,
    ).mean()
    rolling_chart = _to_chart_table(
        time_s=time_s,
        values=rolling_mean,
        series_format=ApiSeriesFormat.NUMBER,
    )

    baseline_source = pivot.shift(1)
    baseline_mean = baseline_source.rolling(
        window=baseline_window_days,
        min_periods=baseline_window_days,
    ).mean()
    baseline_std = baseline_source.rolling(
        window=baseline_window_days,
        min_periods=baseline_window_days,
    ).std(ddof=0)

    baseline_std = baseline_std.mask(baseline_std == 0.0, 1e-9)
    zscore = (pivot - baseline_mean) / baseline_std
    zscore = zscore.mask(~np.isfinite(zscore))

    zscore_chart = _to_chart_table(
        time_s=time_s,
        values=zscore,
        series_format=ApiSeriesFormat.NUMBER,
    )

    anomalies: list[ApiAnomalyEvent] = []
    if zscore_threshold > 0:
        hits = (zscore.abs() >= zscore_threshold) & zscore.notna()
        for row_idx, col_idx in zip(*np.where(hits.to_numpy()), strict=True):
            series_col = zscore.columns[col_idx]
            time_value = int(time_s[row_idx])
            value = float(pivot.iloc[row_idx, col_idx])
            z = float(zscore.iloc[row_idx, col_idx])
            anomalies.append(
                ApiAnomalyEvent(
                    time_s=time_value,
                    series=str(series_col),
                    value=value,
                    zscore=z,
                )
            )

    chart_data = {
        "deaths": raw_chart,
        "deaths_rolling_mean": rolling_chart,
        "deaths_zscore": zscore_chart,
    }
    return chart_data, anomalies, series_names
