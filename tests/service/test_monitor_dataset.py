from __future__ import annotations

from pathlib import Path

import pytest

from app.models.monitor import ApiMonitorFromDatasetParameters
from app.service import monitor as monitor_service


def test_monitor_from_dataset_reads_and_processes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "dataset.csv").write_text(
        "date,deaths\n2025-01-01,10\n2025-01-02,10\n2025-01-03,50\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(tmp_path))
    params = ApiMonitorFromDatasetParameters(
        dataset_name="dataset.csv",
        rolling_window_days=2,
        baseline_window_days=2,
        zscore_threshold=0.0,
    )

    results = monitor_service.perform_monitor_from_dataset(params=params)
    assert results.summary.rows > 0
    assert "deaths" in results.chart_data

