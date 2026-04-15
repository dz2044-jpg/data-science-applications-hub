from __future__ import annotations

import datetime as dt

import pandas as pd

from app.calc.monitor import compute_monitor_tables


def test_compute_monitor_tables_detects_spike_anomaly() -> None:
    df = pd.DataFrame(
        {
            "date": [
                dt.datetime(2025, 1, 1),
                dt.datetime(2025, 1, 2),
                dt.datetime(2025, 1, 3),
                dt.datetime(2025, 1, 4),
                dt.datetime(2025, 1, 5),
            ],
            "series": ["deaths"] * 5,
            "value": [10.0, 10.0, 10.0, 10.0, 100.0],
        }
    )

    chart_data, anomalies, series = compute_monitor_tables(
        df=df,
        rolling_window_days=2,
        baseline_window_days=3,
        zscore_threshold=2.0,
    )

    assert set(chart_data.keys()) == {
        "deaths",
        "deaths_rolling_mean",
        "deaths_zscore",
    }
    assert series == ["deaths"]
    assert len(anomalies) == 1
    assert anomalies[0].series == "deaths"

