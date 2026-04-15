from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest

from app.models.dataset_config import (
    ApiBinaryFeatureAeModuleConfig,
    ApiCreateDatasetConfigRequest,
    ModuleId,
    PerformanceType,
)
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureSignificance,
)
from app.modules.binary_feature_ae.service.binary_calc import (
    apply_filters,
    calculate_binary_feature_ae,
    prepare_rule_df,
)
from app.service.dataset_config import create_dataset_config, save_uploaded_file


def _sample_binary_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule": "R1",
                "RuleName": "Rule One",
                "first_date": "2024-01-01",
                "category": "Cancer",
                "hit_count": 100,
                "hit_rate": 0.12,
                "claim_count": 20,
                "mec_sum": 18,
                "ae_ratio": 1.4,
                "ci_lower_95": 1.2,
                "ci_upper_95": 1.6,
                "ci_lower_90": 1.22,
                "ci_upper_90": 1.58,
                "ci_lower_80": 1.25,
                "ci_upper_80": 1.55,
                "cola_cancer_pct": 0.60,
                "cola_heart_pct": 0.20,
                "cola_nervous_system_pct": 0.05,
                "cola_non_natural_pct": 0.03,
                "cola_other_medical_pct": 0.04,
                "cola_respiratory_pct": 0.05,
                "cola_others_pct": 0.03,
            },
            {
                "rule": "R2",
                "RuleName": "Rule Two",
                "first_date": "2024-02-01",
                "category": "Cardio",
                "hit_count": 10,
                "hit_rate": 0.02,
                "claim_count": 6,
                "mec_sum": 8,
                "ae_ratio": 0.7,
                "ci_lower_95": 0.5,
                "ci_upper_95": 0.8,
                "ci_lower_90": 0.52,
                "ci_upper_90": 0.82,
                "ci_lower_80": 0.56,
                "ci_upper_80": 0.88,
                "cola_cancer_pct": 0.10,
                "cola_heart_pct": 0.55,
                "cola_nervous_system_pct": 0.05,
                "cola_non_natural_pct": 0.05,
                "cola_other_medical_pct": 0.10,
                "cola_respiratory_pct": 0.10,
                "cola_others_pct": 0.05,
            },
            {
                "rule": "R3",
                "RuleName": "Rule Three",
                "first_date": "2024-03-01",
                "category": "Cancer",
                "hit_count": 5,
                "hit_rate": 0.01,
                "claim_count": 3,
                "mec_sum": 4,
                "ae_ratio": 1.05,
                "ci_lower_95": 0.8,
                "ci_upper_95": 1.3,
                "ci_lower_90": 0.9,
                "ci_upper_90": 1.2,
                "ci_lower_80": 1.01,
                "ci_upper_80": 1.1,
                "cola_cancer_pct": 0.15,
                "cola_heart_pct": 0.15,
                "cola_nervous_system_pct": 0.20,
                "cola_non_natural_pct": 0.20,
                "cola_other_medical_pct": 0.10,
                "cola_respiratory_pct": 0.10,
                "cola_others_pct": 0.10,
            },
        ]
    )


def test_prepare_rule_df_requires_all_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_rule_df(pd.DataFrame({"rule": ["R1"]}))


def test_prepare_rule_df_normalizes_and_derives_metrics() -> None:
    prepared = prepare_rule_df(_sample_binary_df())

    top = prepared.iloc[0]
    assert top["rule"] == "R1"
    assert top["significance_class_95"] == "Elevated"
    assert top["significance_class_90"] == "Elevated"
    assert top["significance_class_80"] == "Elevated"
    assert top["confidence_band"] == "Elevated 95%"
    assert top["dominant_cola"] == "Cancer"
    assert top["dominant_cola_pct"] == pytest.approx(60.0)
    assert top["cola_cancer_pct_display"] == pytest.approx(60.0)
    assert top["impact_score"] > prepared.iloc[1]["impact_score"]

    mid = prepared.loc[prepared["rule"] == "R3"].iloc[0]
    assert mid["significance_class_95"] == "Uncertain"
    assert mid["significance_class_80"] == "Elevated"
    assert mid["confidence_band"] == "Elevated 80%"

    low = prepared.loc[prepared["rule"] == "R2"].iloc[0]
    assert low["significance_class_95"] == "Below Expected"
    assert low["confidence_band"] == "Below Expected 95%"


def test_apply_filters_matches_legacy_filter_behavior() -> None:
    prepared = prepare_rule_df(_sample_binary_df())
    working = prepared.copy()
    working["significance_class"] = working["significance_class_95"]

    filtered = apply_filters(
        working,
        categories=["Cancer"],
        significance_values=["Elevated"],
        search_text="rule one",
        min_hit_count=50,
        min_claim_count=10,
    )

    assert filtered["rule"].tolist() == ["R1"]


def test_calculate_binary_feature_ae_from_saved_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(tmp_path))

    source_df = _sample_binary_df().rename(
        columns={"cola_non_natural_pct": "cola_non-natural_pct"}
    )
    csv_bytes = source_df.to_csv(index=False).encode("utf-8")

    request = ApiCreateDatasetConfigRequest(
        dataset_name="binary-demo",
        performance_type=PerformanceType.BINARY_FEATURE_AE,
        file_path="binary.csv",
        module_id=ModuleId.BINARY_FEATURE_AE,
        module_config=ApiBinaryFeatureAeModuleConfig(
            rule="rule",
            RuleName="RuleName",
            first_date="first_date",
            category="category",
            hit_count="hit_count",
            hit_rate="hit_rate",
            claim_count="claim_count",
            mec_sum="mec_sum",
            ae_ratio="ae_ratio",
            ci_lower_95="ci_lower_95",
            ci_upper_95="ci_upper_95",
            ci_lower_90="ci_lower_90",
            ci_upper_90="ci_upper_90",
            ci_lower_80="ci_lower_80",
            ci_upper_80="ci_upper_80",
            cola_cancer_pct="cola_cancer_pct",
            cola_heart_pct="cola_heart_pct",
            cola_nervous_system_pct="cola_nervous_system_pct",
            cola_non_natural_pct="cola_non-natural_pct",
            cola_other_medical_pct="cola_other_medical_pct",
            cola_respiratory_pct="cola_respiratory_pct",
            cola_others_pct="cola_others_pct",
        ),
    )
    config = create_dataset_config(request)
    save_uploaded_file(config.id, BytesIO(csv_bytes), "binary.csv")

    response = calculate_binary_feature_ae(
        params=ApiBinaryFeatureCalculateRequest(
            config_id=config.id,
            categories=["Cancer"],
            significance_values=[
                ApiBinaryFeatureSignificance.ELEVATED,
                ApiBinaryFeatureSignificance.UNCERTAIN,
            ],
            min_hit_count=0,
            min_claim_count=0,
        )
    )

    assert response.dataset_name == "binary-demo"
    assert response.available_categories == ["Cancer", "Cardio"]
    assert response.kpis.visible_rule_count == 2
    assert {row.rule for row in response.rows} == {"R1", "R3"}
    assert response.rows[0].ci_lower == response.rows[0].ci_lower_95
