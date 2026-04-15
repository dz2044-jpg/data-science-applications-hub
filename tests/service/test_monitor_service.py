from __future__ import annotations

from app.models.monitor import ApiMonitorFromCsvParameters
from app.service.monitor import perform_monitor_from_csv_bytes


def test_service_returns_empty_valid_results_when_no_data_after_clamp() -> None:
    csv_bytes = b"date,deaths\n2025-01-01,5\n"
    params = ApiMonitorFromCsvParameters(min_date="2026-01-01")

    results = perform_monitor_from_csv_bytes(csv_bytes=csv_bytes, params=params)
    assert results.summary.rows == 0
    assert results.chart_data == {}
    assert results.anomalies == []

