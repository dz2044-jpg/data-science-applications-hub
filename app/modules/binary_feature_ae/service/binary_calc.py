from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.models.dataset_config import get_binary_feature_module_config
from app.core.service.dataframe_loader import read_dataframe_from_path
from app.core.service.dataset_config import get_dataset_config_with_file
from app.modules.binary_feature_ae.models.triage import (
    ApiBinaryFeatureCalculateRequest,
    ApiBinaryFeatureCalculateResponse,
    ApiBinaryFeatureKpis,
    ApiBinaryFeatureRow,
)

CANONICAL_FIELD_TO_LABEL: dict[str, str] = {
    "rule": "rule",
    "RuleName": "RuleName",
    "first_date": "first_date",
    "category": "category",
    "hit_count": "hit_count",
    "hit_rate": "hit_rate",
    "claim_count": "claim_count",
    "mec_sum": "mec_sum",
    "ae_ratio": "ae_ratio",
    "ci_lower_95": "ci_lower_95",
    "ci_upper_95": "ci_upper_95",
    "ci_lower_90": "ci_lower_90",
    "ci_upper_90": "ci_upper_90",
    "ci_lower_80": "ci_lower_80",
    "ci_upper_80": "ci_upper_80",
    "cola_cancer_pct": "cola_cancer_pct",
    "cola_heart_pct": "cola_heart_pct",
    "cola_nervous_system_pct": "cola_nervous_system_pct",
    "cola_non_natural_pct": "cola_non-natural_pct",
    "cola_other_medical_pct": "cola_other_medical_pct",
    "cola_respiratory_pct": "cola_respiratory_pct",
    "cola_others_pct": "cola_others_pct",
}

REQUIRED_COLS = [
    "rule",
    "RuleName",
    "first_date",
    "category",
    "hit_count",
    "hit_rate",
    "claim_count",
    "mec_sum",
    "ae_ratio",
    "ci_lower_95",
    "ci_upper_95",
    "ci_lower_90",
    "ci_upper_90",
    "ci_lower_80",
    "ci_upper_80",
    "cola_cancer_pct",
    "cola_heart_pct",
    "cola_nervous_system_pct",
    "cola_non_natural_pct",
    "cola_other_medical_pct",
    "cola_respiratory_pct",
    "cola_others_pct",
]

COLA_COLS = [
    "cola_cancer_pct",
    "cola_heart_pct",
    "cola_nervous_system_pct",
    "cola_non_natural_pct",
    "cola_other_medical_pct",
    "cola_respiratory_pct",
    "cola_others_pct",
]

COLA_LABEL_MAP = {
    "cola_cancer_pct": "Cancer",
    "cola_heart_pct": "Heart",
    "cola_nervous_system_pct": "Nervous System",
    "cola_non_natural_pct": "Non-natural",
    "cola_other_medical_pct": "Other Medical",
    "cola_respiratory_pct": "Respiratory",
    "cola_others_pct": "Others",
}

CI_LEVEL_MAP = {
    "95": ("ci_lower_95", "ci_upper_95"),
    "90": ("ci_lower_90", "ci_upper_90"),
    "80": ("ci_lower_80", "ci_upper_80"),
}

CONFIDENCE_BAND_ORDER = [
    "Elevated 95%",
    "Elevated 90%",
    "Elevated 80%",
    "Uncertain",
    "Below Expected 80%",
    "Below Expected 90%",
    "Below Expected 95%",
]


def prepare_rule_df(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        missing_labels = [CANONICAL_FIELD_TO_LABEL.get(name, name) for name in missing]
        raise ValueError(f"Missing required columns: {missing_labels}")

    dff = df.copy().reset_index(drop=True)
    dff["row_id"] = dff.index.astype(str)
    dff["rule"] = dff["rule"].astype(str)
    dff["RuleName"] = dff["RuleName"].fillna("").astype(str)
    dff["first_date"] = dff["first_date"].fillna("").astype(str)
    dff["category"] = dff["category"].fillna("Uncategorized").astype(str)

    ci_cols = [c for pair in CI_LEVEL_MAP.values() for c in pair]
    numeric_cols = [
        "hit_count",
        "hit_rate",
        "claim_count",
        "mec_sum",
        "ae_ratio",
    ] + ci_cols + COLA_COLS

    for col in numeric_cols:
        dff[col] = pd.to_numeric(dff[col], errors="coerce")
    dff[numeric_cols] = dff[numeric_cols].fillna(0)

    cola_max = dff[COLA_COLS].max().max()
    cola_multiplier = 100.0 if cola_max <= 1.5 else 1.0
    display_cola_cols: list[str] = []
    for col in COLA_COLS:
        display_col = f"{col}_display"
        dff[display_col] = dff[col] * cola_multiplier
        display_cola_cols.append(display_col)

    dff["rule_label"] = dff["rule"] + " | " + dff["RuleName"]

    for level, (lo_col, hi_col) in CI_LEVEL_MAP.items():
        dff[f"significance_class_{level}"] = np.select(
            [dff[lo_col] > 1.0, dff[hi_col] < 1.0],
            ["Elevated", "Below Expected"],
            default="Uncertain",
        )
    dff["significance_class"] = dff["significance_class_95"]

    dff["ae_gap"] = dff["ae_ratio"] - 1.0
    dff["abs_ae_gap"] = dff["ae_gap"].abs()
    dff["ci_width"] = dff["ci_upper_95"] - dff["ci_lower_95"]
    dff["impact_score"] = np.log1p(dff["hit_count"].clip(lower=0)) * dff["abs_ae_gap"]

    dominant_idx = dff[display_cola_cols].values.argmax(axis=1)
    dff["dominant_cola"] = [COLA_LABEL_MAP[COLA_COLS[idx]] for idx in dominant_idx]
    dff["dominant_cola_pct"] = dff[display_cola_cols].max(axis=1)

    dff["confidence_band"] = pd.Categorical(
        np.select(
            [
                dff["ci_lower_95"] > 1,
                dff["ci_lower_90"] > 1,
                dff["ci_lower_80"] > 1,
                dff["ci_upper_95"] < 1,
                dff["ci_upper_90"] < 1,
                dff["ci_upper_80"] < 1,
            ],
            [
                "Elevated 95%",
                "Elevated 90%",
                "Elevated 80%",
                "Below Expected 95%",
                "Below Expected 90%",
                "Below Expected 80%",
            ],
            default="Uncertain",
        ),
        categories=CONFIDENCE_BAND_ORDER,
        ordered=True,
    )

    dff = dff.sort_values(
        ["impact_score", "claim_count", "hit_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    return dff


def apply_filters(
    df: pd.DataFrame,
    *,
    categories: list[str] | None,
    significance_values: list[str] | None,
    search_text: str | None,
    min_hit_count: float | None,
    min_claim_count: float | None,
) -> pd.DataFrame:
    dff = df.copy()

    if categories:
        dff = dff[dff["category"].isin(categories)]

    if significance_values:
        dff = dff[dff["significance_class"].isin(significance_values)]

    if search_text:
        search = str(search_text).strip().lower()
        dff = dff[
            dff["rule"].str.lower().str.contains(search, na=False)
            | dff["RuleName"].str.lower().str.contains(search, na=False)
            | dff["category"].str.lower().str.contains(search, na=False)
        ]

    min_hit = 0.0 if min_hit_count is None else float(min_hit_count)
    min_claim = 0.0 if min_claim_count is None else float(min_claim_count)
    dff = dff[dff["hit_count"] >= min_hit]
    dff = dff[dff["claim_count"] >= min_claim]
    return dff.reset_index(drop=True)


def _load_prepared_df_from_config(*, config_id: str) -> tuple[str, pd.DataFrame]:
    config, file_path = get_dataset_config_with_file(config_id)
    module_config = get_binary_feature_module_config(config)
    mapping = module_config.model_dump()
    source_columns = list(mapping.values())
    if len(set(source_columns)) != len(source_columns):
        raise ValueError("Binary Feature module_config contains duplicate column mappings")

    df = read_dataframe_from_path(file_path=file_path, columns=source_columns)
    renamed = df.rename(columns={source: target for target, source in mapping.items()})
    prepared = prepare_rule_df(renamed)
    return config.dataset_name, prepared


def _build_kpis(df: pd.DataFrame) -> ApiBinaryFeatureKpis:
    if df.empty:
        return ApiBinaryFeatureKpis(
            visible_rule_count=0,
            median_hit_rate=0.0,
            median_claim_count=0.0,
            median_ae=0.0,
            elevated_count=0,
            uncertain_count=0,
            below_expected_count=0,
        )

    return ApiBinaryFeatureKpis(
        visible_rule_count=int(len(df)),
        median_hit_rate=float(df["hit_rate"].median()),
        median_claim_count=float(df["claim_count"].median()),
        median_ae=float(df["ae_ratio"].median()),
        elevated_count=int((df["significance_class"] == "Elevated").sum()),
        uncertain_count=int((df["significance_class"] == "Uncertain").sum()),
        below_expected_count=int((df["significance_class"] == "Below Expected").sum()),
    )


def _serialize_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _serialize_rows(df: pd.DataFrame) -> list[ApiBinaryFeatureRow]:
    rows: list[ApiBinaryFeatureRow] = []
    for record in df.to_dict(orient="records"):
        clean = {key: _serialize_value(value) for key, value in record.items()}
        clean["confidence_band"] = str(clean["confidence_band"])
        rows.append(ApiBinaryFeatureRow.model_validate(clean))
    return rows


def calculate_binary_feature_ae(
    *,
    params: ApiBinaryFeatureCalculateRequest,
) -> ApiBinaryFeatureCalculateResponse:
    dataset_name, base_df = _load_prepared_df_from_config(config_id=params.config_id)
    available_categories = sorted(base_df["category"].dropna().unique().tolist())

    ci_level = params.ci_level.value
    ci_lower_col, ci_upper_col = CI_LEVEL_MAP[ci_level]

    working_df = base_df.copy()
    significance_col = f"significance_class_{ci_level}"
    working_df["significance_class"] = working_df[significance_col]

    filtered_df = apply_filters(
        working_df,
        categories=params.categories,
        significance_values=[value.value for value in params.significance_values],
        search_text=params.search_text,
        min_hit_count=params.min_hit_count,
        min_claim_count=params.min_claim_count,
    )

    filtered_df["ci_lower"] = filtered_df[ci_lower_col]
    filtered_df["ci_upper"] = filtered_df[ci_upper_col]
    filtered_df["confidence_band"] = filtered_df["confidence_band"].astype(str)

    return ApiBinaryFeatureCalculateResponse(
        dataset_name=dataset_name,
        available_categories=available_categories,
        kpis=_build_kpis(filtered_df),
        rows=_serialize_rows(filtered_df),
    )
