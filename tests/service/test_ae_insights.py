from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.core.models.dataset_config import (
    ApiMortalityAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ModuleId,
    PerformanceType,
)
from app.core.service.dataset_config import create_dataset_config, save_uploaded_file
from app.modules.mortality_ae.models.insights import ApiAeInsightsFromConfigRequest
from app.modules.mortality_ae.service.ae_insights import (
    _InsightDimension,
    _build_drill,
    _compute_quantile_edges,
    perform_ae_insights_from_config,
)


def _create_saved_config(
    *, tmp_path: Path, dataset_name: str = "insights-demo"
) -> str:
    rows: list[dict[str, object]] = []
    for idx in range(8000):
        sex = "F" if idx % 4 == 0 else "M"
        channel = "Direct" if idx < 4800 else "Agency"
        rows.append(
            {
                "application_number": f"A-{idx:05d}",
                "record_id": f"RID-{idx:05d}",
                "MEC": 1.0,
                "MAC": 5.0 if sex == "F" else 0.5,
                "MAN": 50000.0 if sex == "F" else 5000.0,
                "MEN": 10000.0,
                "MOC": 1.0,
                "sex": sex,
                "channel": channel,
                "age": 20 + idx,
                "tiny_numeric": idx % 3,
            }
        )

    csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode("utf-8")
    request = ApiCreateDatasetConfigRequest(
        dataset_name=dataset_name,
        performance_type=PerformanceType.MORTALITY_AE,
        file_path="insights.csv",
        module_id=ModuleId.MORTALITY_AE,
        module_config=ApiMortalityAeModuleConfig(
            policy_number_column="application_number",
            face_amount_column=None,
            mac_column="MAC",
            mec_column="MEC",
            man_column="MAN",
            men_column="MEN",
            moc_column="MOC",
            cola_m1_column=None,
        ),
    )
    config = create_dataset_config(request)
    save_uploaded_file(config.id, BytesIO(csv_bytes), "insights.csv")
    return config.id


def test_compute_quantile_edges_collapses_duplicate_percentiles() -> None:
    series = pd.Series([0.0, 0.0, 0.0, 10.0, 20.0, 30.0], dtype=float)

    edges = _compute_quantile_edges(series)

    assert edges is not None
    assert edges == [0.0, 10.0, 20.0, 30.0]


def test_build_drill_prefers_numeric_x_and_higher_cardinality_otherwise() -> None:
    drill = _build_drill(
        [
            _InsightDimension(
                name="sex",
                alias="dim_0",
                kind="categorical",
                distinct_count=2,
            ),
            _InsightDimension(
                name="age",
                alias="dim_1",
                kind="numeric",
                distinct_count=60,
                edges=[20.0, 30.0],
            ),
        ]
    )

    assert drill.x_variable.name == "age"
    assert drill.split_variable is not None
    assert drill.split_variable.name == "sex"


def test_perform_ae_insights_from_config_returns_ranked_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    config_id = _create_saved_config(tmp_path=tmp_path)

    result = perform_ae_insights_from_config(
        params=ApiAeInsightsFromConfigRequest(
            config_id=config_id,
            max_results_per_metric=10,
        )
    )

    assert result.config_id == config_id
    assert result.count_insights
    assert result.amount_insights
    assert all(insight.sample_size >= 1500 for insight in result.count_insights)
    assert all(insight.sample_size >= 1500 for insight in result.amount_insights)

    top_count = result.count_insights[0]
    top_amount = result.amount_insights[0]

    dimension_names = {name for insight in result.count_insights for name in insight.dimensions}
    assert "sex" in dimension_names
    assert "record_id" not in dimension_names
    assert "MAC" not in dimension_names
    assert "tiny_numeric" not in dimension_names

    assert top_count.segment_label.startswith("sex: ")
    assert top_count.variance_count > 0
    assert top_count.drill.x_variable.name in {"age", "sex", "channel"}

    assert top_amount.variance_amount > 0
    assert top_amount.ae_amount is not None

    amount_two_dim = next(
        insight
        for insight in result.amount_insights
        if len(insight.dimensions) == 2 and "age" in insight.dimensions
    )
    assert amount_two_dim.drill.split_variable is not None
    assert amount_two_dim.drill.x_variable.name == "age"

    categorical_pair = next(
        insight for insight in result.count_insights if len(insight.dimensions) == 2
    )
    assert categorical_pair.drill.split_variable is not None


def test_perform_ae_insights_from_config_rejects_unknown_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    with pytest.raises(ValueError, match="not found"):
        perform_ae_insights_from_config(
            params=ApiAeInsightsFromConfigRequest(config_id="missing-config")
        )
