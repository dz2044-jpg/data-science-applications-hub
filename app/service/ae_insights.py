from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from app.models.ae import (
    ApiAeXVariableCategorical,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.models.insights import (
    ApiAeInsightDrill,
    ApiAeInsightResult,
    ApiAeInsightsFromConfigRequest,
    ApiAeInsightsResults,
)
from app.service.ae_univariate import _detect_application_id_column
from app.service.dataframe_loader import read_dataframe_from_path
from app.service.dataset_config import get_dataset_config_with_file
from app.service.dataset_schema import get_dataset_schema_from_path

_MISSING_LABEL = "(Missing)"


@dataclass(frozen=True)
class _InsightDimension:
    name: str
    alias: str
    kind: str
    distinct_count: int
    edges: list[float] | None = None


def _max_candidate_dimensions() -> int:
    raw = (os.getenv("AEMONITOR_MAX_INSIGHT_DIMENSIONS") or "").strip()
    if not raw:
        return 8
    try:
        value = int(raw)
    except ValueError:
        return 8
    return max(2, min(value, 12))


def _quote_identifier(name: str) -> str:
    return f'"{name.replace(chr(34), chr(34) * 2)}"'


def _quote_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _quote_number(value: float) -> str:
    if not np.isfinite(value):
        raise ValueError("Numeric bucket edges must be finite")
    return repr(float(value))


def _path_literal(file_path: Path) -> str:
    return _quote_string(str(file_path))


def _format_bucket_edge(value: float) -> str:
    rounded = round(float(value), 6)
    if float(rounded).is_integer():
        return f"{int(rounded):,}"
    return f"{rounded:,.6f}".rstrip("0").rstrip(".")


def _normalize_optional_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalized_tokens(name: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]


def _is_identifier_like(
    *,
    name: str,
    kind: str,
    distinct_count: int,
    row_count: int,
) -> bool:
    tokens = _normalized_tokens(name)
    joined = "".join(tokens)
    if not tokens:
        return False

    strong_names = {
        "id",
        "policyid",
        "policynumber",
        "applicationid",
        "applicationnumber",
        "recordid",
        "recordnumber",
        "memberid",
        "claimid",
        "certificateid",
    }
    if joined in strong_names:
        return True

    if any(token in {"id", "identifier"} for token in tokens):
        return True

    near_unique = row_count > 0 and distinct_count >= max(100, int(row_count * 0.95))
    if joined.endswith("number") or joined.endswith("num") or joined.endswith("id"):
        return near_unique

    if kind == "categorical" and near_unique:
        return any(
            token in {"policy", "application", "record", "claim", "member", "certificate"}
            for token in tokens
        )

    return False


def _metric_expression(column_name: str | None, alias: str) -> str:
    if column_name is None:
        return f"0.0 AS {_quote_identifier(alias)}"
    return (
        f"COALESCE(TRY_CAST({_quote_identifier(column_name)} AS DOUBLE), 0.0) "
        f"AS {_quote_identifier(alias)}"
    )


def _categorical_dimension_expression(spec: _InsightDimension) -> str:
    source = _quote_identifier(spec.name)
    alias = _quote_identifier(spec.alias)
    return (
        f"COALESCE(NULLIF(TRIM(CAST({source} AS VARCHAR)), ''), "
        f"{_quote_string(_MISSING_LABEL)}) AS {alias}"
    )


def _numeric_dimension_expression(spec: _InsightDimension) -> str:
    if not spec.edges or len(spec.edges) < 2:
        raise ValueError(f"Numeric insight dimension '{spec.name}' has no valid edges")

    value_expr = f"TRY_CAST({_quote_identifier(spec.name)} AS DOUBLE)"
    clauses: list[str] = []
    for idx in range(1, len(spec.edges)):
        hi = spec.edges[idx]
        lo = spec.edges[idx - 1]
        if idx == 1:
            label = f"[{_format_bucket_edge(lo)}, {_format_bucket_edge(hi)}]"
        else:
            label = f"({_format_bucket_edge(lo)}, {_format_bucket_edge(hi)}]"
        clauses.append(
            f"WHEN {value_expr} <= {_quote_number(hi)} THEN {_quote_string(label)}"
        )

    return (
        f"COALESCE(CASE WHEN {value_expr} IS NULL THEN NULL "
        + " ".join(clauses)
        + f" END, {_quote_string(_MISSING_LABEL)}) AS {_quote_identifier(spec.alias)}"
    )


def _dimension_expression(spec: _InsightDimension) -> str:
    if spec.kind == "numeric":
        return _numeric_dimension_expression(spec)
    return _categorical_dimension_expression(spec)


def _compute_quantile_edges(series: pd.Series) -> list[float] | None:
    numeric = pd.to_numeric(series, errors="coerce")
    values = numeric[np.isfinite(numeric.to_numpy(dtype=float))]
    if len(values) == 0:
        return None

    raw_edges = np.percentile(values.to_numpy(dtype=float), [0, 20, 40, 60, 80, 100])
    unique_edges: list[float] = []
    for edge in raw_edges.tolist():
        edge_value = float(edge)
        if not unique_edges or not np.isclose(edge_value, unique_edges[-1]):
            unique_edges.append(edge_value)

    if len(unique_edges) < 2:
        return None
    return unique_edges


def _build_drill(dimensions: list[_InsightDimension]) -> ApiAeInsightDrill:
    def to_variable(spec: _InsightDimension):
        if spec.kind == "numeric":
            return ApiAeXVariableNumeric(
                name=spec.name,
                binning=ApiNumericBinning.QUINTILE,
                bin_count=5,
            )
        return ApiAeXVariableCategorical(
            name=spec.name,
            grouping="all_unique",
            groups=None,
            remaining_name="Remaining",
            remaining_position=None,
        )

    if len(dimensions) == 1:
        return ApiAeInsightDrill(x_variable=to_variable(dimensions[0]))

    first, second = dimensions
    if first.kind == "numeric" and second.kind == "categorical":
        x_dim, split_dim = first, second
    elif first.kind == "categorical" and second.kind == "numeric":
        x_dim, split_dim = second, first
    elif first.distinct_count >= second.distinct_count:
        x_dim, split_dim = first, second
    else:
        x_dim, split_dim = second, first

    return ApiAeInsightDrill(
        x_variable=to_variable(x_dim),
        split_variable=to_variable(split_dim),
    )


def _sort_key(
    insight: ApiAeInsightResult, *, metric: str, rank_by: str
) -> tuple[float, int, str]:
    # Rank by A/E value (highest first)
    ae_value = insight.ae_count if metric == "count" else insight.ae_amount
    # Handle None values by sorting them to the end (use negative infinity)
    primary_key = ae_value if ae_value is not None else float("-inf")
    return (-primary_key, len(insight.dimensions), insight.segment_label)


def _register_source_table(conn: duckdb.DuckDBPyConnection, *, file_path: Path) -> str:
    table_name = "source_data"
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        conn.execute(
            "CREATE OR REPLACE TEMP VIEW source_data AS "
            f"SELECT * FROM read_csv_auto({_path_literal(file_path)}, header=true)"
        )
        return table_name
    if suffix == ".parquet":
        conn.execute(
            "CREATE OR REPLACE TEMP VIEW source_data AS "
            f"SELECT * FROM read_parquet({_path_literal(file_path)})"
        )
        return table_name

    df = read_dataframe_from_path(file_path=file_path)
    conn.register(table_name, df)
    return table_name


def _profile_candidates(
    *,
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    config,
    file_path: Path,
) -> list[_InsightDimension]:
    schema = get_dataset_schema_from_path(
        file_path=file_path,
        dataset_name=config.dataset_name,
    )
    mapped_columns = {
        name
        for name in [
            _normalize_optional_name(config.column_mapping.policy_number_column),
            _normalize_optional_name(config.column_mapping.face_amount_column),
            _normalize_optional_name(config.column_mapping.mac_column),
            _normalize_optional_name(config.column_mapping.mec_column),
            _normalize_optional_name(config.column_mapping.man_column),
            _normalize_optional_name(config.column_mapping.men_column),
            _normalize_optional_name(config.column_mapping.moc_column),
            _normalize_optional_name(config.column_mapping.cola_m1_column),
        ]
        if name is not None
    }

    candidates = [
        column
        for column in schema.columns
        if column.name not in mapped_columns and column.kind != "date"
    ]
    if not candidates:
        return []

    dtype_probe = read_dataframe_from_path(
        file_path=file_path,
        nrows=1000,
        columns=[column.name for column in candidates],
    )

    count_exprs = [
        f"COUNT(DISTINCT {_quote_identifier(column.name)}) AS {_quote_identifier(f'd_{idx}')}"
        for idx, column in enumerate(candidates)
    ]
    profile_row = conn.execute(
        "SELECT COUNT(*) AS row_count, "
        + ", ".join(count_exprs)
        + f" FROM {table_name}"
    ).fetchone()
    if profile_row is None:
        return []

    row_count = int(profile_row[0])
    selected: list[_InsightDimension] = []
    for idx, column in enumerate(candidates):
        distinct_count = int(profile_row[idx + 1] or 0)
        if distinct_count <= 1:
            continue

        if _is_identifier_like(
            name=column.name,
            kind=str(column.kind),
            distinct_count=distinct_count,
            row_count=row_count,
        ):
            continue

        is_numeric_dtype = pd.api.types.is_numeric_dtype(dtype_probe[column.name].dtype)
        if is_numeric_dtype and distinct_count <= 50:
            continue

        if not is_numeric_dtype and str(column.kind) == "categorical" and distinct_count <= 50:
            selected.append(
                _InsightDimension(
                    name=column.name,
                    alias=f"dim_{len(selected)}",
                    kind="categorical",
                    distinct_count=distinct_count,
                )
            )
            continue

        if is_numeric_dtype and distinct_count > 50:
            selected.append(
                _InsightDimension(
                    name=column.name,
                    alias=f"dim_{len(selected)}",
                    kind="numeric",
                    distinct_count=distinct_count,
                )
            )

    if not selected:
        return []

    selected = selected[: _max_candidate_dimensions()]
    numeric_names = [spec.name for spec in selected if spec.kind == "numeric"]
    if not numeric_names:
        return selected

    numeric_df = read_dataframe_from_path(file_path=file_path, columns=numeric_names)
    finalized: list[_InsightDimension] = []
    for spec in selected:
        if spec.kind != "numeric":
            finalized.append(spec)
            continue

        edges = _compute_quantile_edges(numeric_df[spec.name])
        if edges is None:
            continue
        finalized.append(
            _InsightDimension(
                name=spec.name,
                alias=spec.alias,
                kind=spec.kind,
                distinct_count=spec.distinct_count,
                edges=edges,
            )
        )
    return finalized


def perform_ae_insights_from_config(
    *, params: ApiAeInsightsFromConfigRequest
) -> ApiAeInsightsResults:
    config, file_path = get_dataset_config_with_file(params.config_id)
    schema = get_dataset_schema_from_path(
        file_path=file_path,
        dataset_name=config.dataset_name,
    )
    available_columns = {column.name for column in schema.columns}

    required_columns = {
        config.column_mapping.mac_column,
        config.column_mapping.mec_column,
        config.column_mapping.man_column,
        config.column_mapping.men_column,
    }
    missing_columns = sorted(required_columns - available_columns)
    if missing_columns:
        raise ValueError(
            "Saved configuration points to missing columns: "
            + ", ".join(missing_columns)
        )

    probe_df = read_dataframe_from_path(file_path=file_path, nrows=5)
    app_id_column = _normalize_optional_name(config.column_mapping.policy_number_column)
    if app_id_column is None:
        app_id_column = _detect_application_id_column(probe_df)
    if app_id_column not in available_columns:
        raise ValueError(f"Missing application id column: {app_id_column}")

    conn = duckdb.connect()
    try:
        table_name = _register_source_table(conn, file_path=file_path)
        dimensions = _profile_candidates(
            conn=conn,
            table_name=table_name,
            config=config,
            file_path=file_path,
        )
        if not dimensions:
            return ApiAeInsightsResults(
                config_id=params.config_id,
                count_insights=[],
                amount_insights=[],
            )

        dimension_select = ",\n                ".join(
            _dimension_expression(spec) for spec in dimensions
        )
        grouping_sets = [
            f"({_quote_identifier(spec.alias)})"
            for spec in dimensions
        ]
        for idx, left in enumerate(dimensions):
            for right in dimensions[idx + 1 :]:
                grouping_sets.append(
                    f"({_quote_identifier(left.alias)}, {_quote_identifier(right.alias)})"
                )

        binned_query = f"""
            WITH BinnedData AS (
                SELECT
                    {dimension_select},
                    {_quote_identifier(app_id_column)} AS "__app_id__",
                    {_metric_expression(config.column_mapping.mac_column, "actual_count")},
                    {_metric_expression(config.column_mapping.mec_column, "expected_count")},
                    {_metric_expression(config.column_mapping.man_column, "actual_amount")},
                    {_metric_expression(config.column_mapping.men_column, "expected_amount")},
                    {_metric_expression(_normalize_optional_name(config.column_mapping.moc_column), "exposure_count")}
                FROM {table_name}
            )
            SELECT
                {", ".join(_quote_identifier(spec.alias) for spec in dimensions)},
                COUNT(DISTINCT "__app_id__") AS sample_size,
                SUM(exposure_count) AS exposure_count,
                SUM(actual_count) AS actual_count,
                SUM(expected_count) AS expected_count,
                SUM(actual_amount) AS actual_amount,
                SUM(expected_amount) AS expected_amount
            FROM BinnedData
            GROUP BY GROUPING SETS ({", ".join(grouping_sets)})
        """
        results_df = conn.execute(binned_query).df()
    finally:
        conn.close()

    spec_by_alias = {spec.alias: spec for spec in dimensions}
    parsed: list[ApiAeInsightResult] = []
    for _, row in results_df.iterrows():
        active_aliases = [
            spec.alias for spec in dimensions if pd.notna(row[spec.alias])
        ]
        if not active_aliases:
            continue

        active_dimensions = [spec_by_alias[alias] for alias in active_aliases]
        segment_filters = {
            spec.name: str(row[spec.alias]) for spec in active_dimensions
        }
        segment_label = " | ".join(
            f"{name}: {value}" for name, value in segment_filters.items()
        )
        actual_count = float(row["actual_count"] or 0.0)
        expected_count = float(row["expected_count"] or 0.0)
        actual_amount = float(row["actual_amount"] or 0.0)
        expected_amount = float(row["expected_amount"] or 0.0)
        parsed.append(
            ApiAeInsightResult(
                dimensions=[spec.name for spec in active_dimensions],
                segment_label=segment_label,
                segment_filters=segment_filters,
                sample_size=int(row["sample_size"] or 0),
                exposure_count=float(row["exposure_count"] or 0.0),
                actual_count=actual_count,
                expected_count=expected_count,
                variance_count=actual_count - expected_count,
                ae_count=(actual_count / expected_count) if expected_count > 0 else None,
                actual_amount=actual_amount,
                expected_amount=expected_amount,
                variance_amount=actual_amount - expected_amount,
                ae_amount=(actual_amount / expected_amount) if expected_amount > 0 else None,
                drill=_build_drill(active_dimensions),
            )
        )

    count_insights = sorted(
        [
            insight
            for insight in parsed
            if insight.sample_size >= 50 and insight.expected_count >= 5
        ],
        key=lambda insight: _sort_key(insight, metric="count", rank_by="ae"),
    )[: params.max_results_per_metric]

    amount_insights = sorted(
        [
            insight
            for insight in parsed
            if insight.expected_amount >= 10000
        ],
        key=lambda insight: _sort_key(insight, metric="amount", rank_by="ae"),
    )[: params.max_results_per_metric]

    return ApiAeInsightsResults(
        config_id=params.config_id,
        count_insights=count_insights,
        amount_insights=amount_insights,
    )
