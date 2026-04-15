from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

from app.models.ae import (
    ApiAeAtomicVariable,
    ApiAeCrossGroupDefinition,
    ApiAePolynomialFitParameters,
    ApiAePolynomialFitResults,
    ApiAeUnivariateRow,
    ApiAeXVariable,
    ApiAeXVariableCategorical,
    ApiAeXVariableCross,
    ApiAeXVariableDate,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.models.chart import ApiChartColumn, ApiChartTable, ApiSeriesFormat


def safe_div(numerator: float, denominator: float) -> float | None:
    """Safely divide two numbers, returning None if denominator is 0."""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return None
    return numerator / denominator


def _compute_mortality_rate_ci(
    mac: float,
    moc: float,
    confidence_level: float = 0.95,
) -> tuple[float, float] | tuple[None, None]:
    """
    Compute mortality rate confidence interval using Beta distribution (shared by both count and amount).
    
    Args:
        mac: Mortality Actual Count (deaths)
        moc: Mortality Exposure Count (policy count)
        confidence_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (lower_rate, upper_rate), or (None, None) if cannot compute
    """
    # Validate inputs
    if (
        not isinstance(mac, (int, float))
        or not isinstance(moc, (int, float))
        or pd.isna(mac)
        or pd.isna(moc)
        or moc <= 0
        or mac < 0
        or mac > moc
        or confidence_level <= 0
        or confidence_level >= 1
    ):
        return None, None
    
    # Calculate alpha for two-tailed CI
    alpha_ci = (1 - confidence_level) / 2
    
    # Beta distribution parameters (Jeffrey's prior)
    alpha_beta = mac + 0.5
    beta_beta = moc - mac + 0.5
    
    # Mortality rate CI
    lower_rate = stats.beta.ppf(alpha_ci, alpha_beta, beta_beta)
    upper_rate = stats.beta.ppf(1 - alpha_ci, alpha_beta, beta_beta)
    
    return lower_rate, upper_rate


def compute_ae_ci(
    mac: float,
    moc: float,
    mec: float,
    confidence_level: float = 0.95,
) -> tuple[float | None, float | None]:
    """
    Compute confidence interval for A/E ratio by count using Beta distribution.
    
    Args:
        mac: Mortality Actual Count (deaths)
        moc: Mortality Exposure Count (policy count)
        mec: Mortality Expected Count
        confidence_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (ae_ci_lower, ae_ci_upper), or (None, None) if cannot compute
    """
    # Validate expected count
    if not isinstance(mec, (int, float)) or pd.isna(mec) or mec <= 0:
        return None, None
    
    # Get mortality rate CI (shared calculation)
    lower_rate, upper_rate = _compute_mortality_rate_ci(mac, moc, confidence_level)
    if lower_rate is None:
        return None, None
    
    # Convert rate to death count
    lower_count = lower_rate * moc
    upper_count = upper_rate * moc
    
    # Convert to A/E ratio
    ae_ci_lower = lower_count / mec
    ae_ci_upper = upper_count / mec
    
    return ae_ci_lower, ae_ci_upper


def compute_ae_ci_amount(
    mac: float,
    moc: float,
    mec: float,
    actual_amount: float,
    expected_amount: float,
    confidence_level: float = 0.95,
) -> tuple[float | None, float | None]:
    """
    Compute confidence interval for A/E ratio by amount using Beta distribution.
    
    Uses hybrid approach for average claim amount:
    - If mac > 0: uses actual average (actual_amount / mac)
    - If mac = 0: uses expected average (expected_amount / mec)
    
    Args:
        mac: Mortality Actual Count (deaths)
        moc: Mortality Exposure Count (policy count)
        mec: Mortality Expected Count
        actual_amount: Actual claim amount (MAN)
        expected_amount: Expected claim amount (MEN)
        confidence_level: Confidence level (default 0.95 for 95% CI)
        
    Returns:
        Tuple of (ae_ci_lower, ae_ci_upper), or (None, None) if cannot compute
    """
    # Validate amount inputs
    if (
        not isinstance(actual_amount, (int, float))
        or not isinstance(expected_amount, (int, float))
        or not isinstance(mec, (int, float))
        or pd.isna(actual_amount)
        or pd.isna(expected_amount)
        or pd.isna(mec)
        or expected_amount <= 0
        or mec <= 0
        or actual_amount < 0
    ):
        return None, None
    
    # Get mortality rate CI (same calculation as count metric)
    lower_rate, upper_rate = _compute_mortality_rate_ci(mac, moc, confidence_level)
    if lower_rate is None:
        return None, None
    
    # Determine average claim amount (hybrid approach)
    if mac > 0:
        avg_claim_amount = actual_amount / mac  # Use actual average
    else:
        avg_claim_amount = expected_amount / mec  # Use expected average
    
    # Convert rate to claim amount
    lower_amount = lower_rate * moc * avg_claim_amount
    upper_amount = upper_rate * moc * avg_claim_amount
    
    # Convert to A/E ratio
    ae_ci_lower = lower_amount / expected_amount
    ae_ci_upper = upper_amount / expected_amount
    
    return ae_ci_lower, ae_ci_upper


@dataclass(frozen=True)
class _AggRow:
    key: str
    avg_x: float | None
    sample_size: int
    deaths: float
    expected: float
    actual_amount: float
    expected_amount: float
    exposure_count: float
    total_face_amount: float


def _format_num(x: float) -> str:
    if np.isnan(x) or np.isinf(x):
        return "—"
    if abs(x) >= 1000:
        return f"{x:.0f}"
    if abs(x) >= 10:
        return f"{x:.2f}".rstrip("0").rstrip(".")
    return f"{x:.4f}".rstrip("0").rstrip(".")


def _format_dt(ts: pd.Timestamp) -> str:
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC")
    if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
        return ts.strftime("%Y-%m-%d")
    return ts.strftime("%Y-%m-%d %H:%M")


def _interval_label_date(interval: pd.Interval, *, force_left_closed: bool = False) -> str:
    left_sec = float(interval.left)
    right_sec = float(interval.right)
    left_ts = pd.to_datetime(left_sec, unit="s", utc=True)
    right_ts = pd.to_datetime(right_sec, unit="s", utc=True)

    left_bracket = (
        "["
        if (force_left_closed or interval.closed in {"left", "both"})
        else "("
    )
    right_bracket = "]" if interval.closed in {"right", "both"} else ")"
    return f"{left_bracket}{_format_dt(left_ts)}, {_format_dt(right_ts)}{right_bracket}"


def _dt_to_seconds(dt: pd.Series) -> pd.Series:
    vals = dt.astype("int64")
    return vals.astype(float) / 1_000_000_000.0

def _interval_label(interval: pd.Interval, *, force_left_closed: bool = False) -> str:
    left = float(interval.left)
    right = float(interval.right)

    left_bracket = (
        "["
        if (force_left_closed or interval.closed in {"left", "both"})
        else "("
    )
    right_bracket = "]" if interval.closed in {"right", "both"} else ")"
    return f"{left_bracket}{_format_num(left)}, {_format_num(right)}{right_bracket}"


def _labels_from_bins(bins: pd.Series) -> tuple[pd.Series, list[str]]:
    if not hasattr(bins, "cat"):
        labels = bins.astype(str).fillna("Missing")
        order = sorted(labels.dropna().unique().tolist(), key=str)
        if "Missing" in set(labels.unique().tolist()):
            order = [o for o in order if o != "Missing"] + ["Missing"]
        return labels, order

    categories = list(bins.cat.categories)  # type: ignore[attr-defined]
    cat_labels = [
        _interval_label(c, force_left_closed=(i == 0))
        for i, c in enumerate(categories)  # type: ignore[attr-defined]
    ]

    codes = bins.cat.codes.to_numpy()  # type: ignore[attr-defined]
    labels_arr = np.empty(shape=(len(codes),), dtype=object)
    missing_mask = codes < 0
    labels_arr[missing_mask] = "Missing"
    if len(cat_labels):
        idx = codes[~missing_mask]
        labels_arr[~missing_mask] = np.asarray(cat_labels, dtype=object)[idx]
    labels = pd.Series(labels_arr, index=bins.index, dtype="string")

    order = cat_labels + (["Missing"] if bool(missing_mask.any()) else [])
    return labels, order


def _labels_from_bins_date(bins: pd.Series) -> tuple[pd.Series, list[str]]:
    if not hasattr(bins, "cat"):
        labels = bins.astype(str).fillna("Missing")
        order = sorted(labels.dropna().unique().tolist(), key=str)
        if "Missing" in set(labels.unique().tolist()):
            order = [o for o in order if o != "Missing"] + ["Missing"]
        return labels, order

    categories = list(bins.cat.categories)  # type: ignore[attr-defined]
    cat_labels = [
        _interval_label_date(c, force_left_closed=(i == 0))
        for i, c in enumerate(categories)  # type: ignore[attr-defined]
    ]

    codes = bins.cat.codes.to_numpy()  # type: ignore[attr-defined]
    labels_arr = np.empty(shape=(len(codes),), dtype=object)
    missing_mask = codes < 0
    labels_arr[missing_mask] = "Missing"
    if len(cat_labels):
        idx = codes[~missing_mask]
        labels_arr[~missing_mask] = np.asarray(cat_labels, dtype=object)[idx]
    labels = pd.Series(labels_arr, index=bins.index, dtype="string")

    order = cat_labels + (["Missing"] if bool(missing_mask.any()) else [])
    return labels, order


def _compute_group_labels_for_atomic_variable(
    *, df: pd.DataFrame, variable: ApiAeAtomicVariable
) -> tuple[pd.Series, list[str]]:
    if variable.kind == "numeric":
        x = pd.to_numeric(df[variable.name], errors="coerce")
        finite = x[np.isfinite(x.to_numpy(dtype=float))]
        if len(finite) == 0:
            raise ValueError("Variable has no numeric values")

        if variable.binning in {ApiNumericBinning.UNIFORM, ApiNumericBinning.QUINTILE}:
            if variable.bin_count is None:
                raise ValueError("bin_count is required")
            bin_count = int(variable.bin_count)
            if variable.binning == ApiNumericBinning.UNIFORM:
                lo = float(finite.min())
                hi = float(finite.max())
                edges = (
                    np.array([lo, hi], dtype=float)
                    if lo == hi
                    else np.linspace(lo, hi, bin_count + 1)
                )
                bins = pd.cut(x, bins=edges, include_lowest=True, duplicates="drop")
            else:
                bins = pd.qcut(x, q=bin_count, duplicates="drop")
            return _labels_from_bins(bins)

        if variable.binning == ApiNumericBinning.CUSTOM:
            raw = variable.custom_edges or []
            edges_raw = sorted({float(v) for v in raw if np.isfinite(float(v))})
            if len(edges_raw) == 0:
                raise ValueError("custom_edges must be provided for custom binning")

            lo = float(finite.min())
            hi = float(finite.max())
            inner = [e for e in edges_raw if lo < e < hi]
            edges = [lo] + inner + [hi]
            bins = pd.cut(x, bins=edges, include_lowest=True, duplicates="drop")
            return _labels_from_bins(bins)

        raise ValueError("Unsupported numeric binning")

    if variable.kind == "date":
        dt = pd.to_datetime(df[variable.name], errors="coerce", utc=True)
        mask = dt.notna()
        if not bool(mask.any()):
            raise ValueError("Variable has no datetime values")

        sec = _dt_to_seconds(dt)
        finite = sec[mask]
        lo = float(finite.min())
        hi = float(finite.max())

        if variable.binning in {ApiNumericBinning.UNIFORM, ApiNumericBinning.QUINTILE}:
            if variable.bin_count is None:
                raise ValueError("bin_count is required")
            bin_count = int(variable.bin_count)
            if variable.binning == ApiNumericBinning.UNIFORM:
                edges = (
                    np.array([lo, hi], dtype=float)
                    if lo == hi
                    else np.linspace(lo, hi, bin_count + 1)
                )
                bins = pd.cut(sec, bins=edges, include_lowest=True, duplicates="drop")
            else:
                bins = pd.qcut(sec, q=bin_count, duplicates="drop")
            return _labels_from_bins_date(bins)

        if variable.binning == ApiNumericBinning.CUSTOM:
            raw = variable.custom_edges or []
            parsed = pd.to_datetime(pd.Series(raw, dtype="string"), errors="coerce", utc=True)
            secs_raw = _dt_to_seconds(parsed).to_numpy(dtype=float)
            edges_raw = sorted({float(v) for v in secs_raw.tolist() if np.isfinite(float(v))})
            if len(edges_raw) == 0:
                raise ValueError("custom_edges must be provided for custom binning")

            inner = [e for e in edges_raw if lo < e < hi]
            edges = [lo] + inner + [hi]
            bins = pd.cut(sec, bins=edges, include_lowest=True, duplicates="drop")
            return _labels_from_bins_date(bins)

        raise ValueError("Unsupported date binning")

    s = df[variable.name].astype("string").fillna("Missing").astype(str)

    if variable.grouping == "all_unique":
        unique = sorted(set(s.tolist()), key=str)
        if "Missing" in set(unique):
            unique = [u for u in unique if u != "Missing"] + ["Missing"]
        return s, unique

    groups = variable.groups or []
    names = [g.name for g in groups] + [variable.remaining_name]
    if len(set(names)) != len(names):
        raise ValueError("Group names must be unique")

    name_by_value: dict[str, str] = {}
    for g in groups:
        for v in g.values:
            if v in name_by_value:
                raise ValueError("A categorical value cannot be in multiple groups")
            name_by_value[v] = g.name

    labels = s.map(lambda v: name_by_value.get(v, variable.remaining_name))
    group_positions = [g.x_position for g in groups]
    any_pos = any(p is not None for p in group_positions) or (
        variable.remaining_position is not None
    )
    if any_pos:
        if variable.remaining_position is None or any(p is None for p in group_positions):
            raise ValueError("All groups must have x_position when using custom positions")
        positions = {g.name: float(g.x_position) for g in groups} | {
            variable.remaining_name: float(variable.remaining_position),
        }
        if any(not np.isfinite(v) for v in positions.values()):
            raise ValueError("x_position values must be finite")
        if len(set(positions.values())) != len(positions.values()):
            raise ValueError("x_position values must be unique")
        order = [k for k, _v in sorted(positions.items(), key=lambda kv: kv[1])]
    else:
        order = [g.name for g in groups] + [variable.remaining_name]
    if "Missing" in set(s.tolist()) and "Missing" not in set(order):
        order.append("Missing")
    return labels, order


def _validate_cross_groups_no_overlap(
    *,
    a_labels: pd.Series,
    b_labels: pd.Series,
    groups: list[ApiAeCrossGroupDefinition],
) -> None:
    masks: list[np.ndarray] = []
    for g in groups:
        if not g.name.strip():
            raise ValueError("Cross group name cannot be empty")
        if bool(g.a_any) and bool(g.b_any):
            raise ValueError(
                "A cross group cannot have both a_any and b_any enabled"
            )
        if not bool(g.a_any) and len(g.a_values) == 0:
            raise ValueError("Cross group must specify a_values or enable a_any")
        if not bool(g.b_any) and len(g.b_values) == 0:
            raise ValueError("Cross group must specify b_values or enable b_any")

        a_ok = True if bool(g.a_any) else a_labels.isin(g.a_values)
        b_ok = True if bool(g.b_any) else b_labels.isin(g.b_values)
        masks.append((a_ok & b_ok).to_numpy(dtype=bool))

    if not masks:
        return

    stacked = np.vstack(masks)
    overlap = np.sum(stacked, axis=0) > 1
    if bool(overlap.any()):
        raise ValueError("Cross groups overlap; refine group definitions to be disjoint")


def _compute_group_labels_for_cross_variable(
    *, df: pd.DataFrame, variable: ApiAeXVariableCross
) -> tuple[pd.Series, list[str]]:
    a_labels, _a_order = _compute_group_labels_for_atomic_variable(
        df=df, variable=variable.a_variable
    )
    b_labels, _b_order = _compute_group_labels_for_atomic_variable(
        df=df, variable=variable.b_variable
    )

    groups = variable.groups or []
    names = [g.name for g in groups] + [variable.remaining_name]
    if len(set(names)) != len(names):
        raise ValueError("Cross group names must be unique")

    _validate_cross_groups_no_overlap(a_labels=a_labels, b_labels=b_labels, groups=groups)

    remaining = variable.remaining_name
    labels = pd.Series([remaining] * len(df.index), index=df.index, dtype="string")
    for g in groups:
        a_ok = True if bool(g.a_any) else a_labels.isin(g.a_values)
        b_ok = True if bool(g.b_any) else b_labels.isin(g.b_values)
        mask = (a_ok & b_ok) & (labels == remaining)
        labels = labels.mask(mask, g.name)

    group_positions = [g.x_position for g in groups]
    any_pos = any(p is not None for p in group_positions) or (
        variable.remaining_position is not None
    )
    if any_pos:
        if variable.remaining_position is None or any(p is None for p in group_positions):
            raise ValueError("All cross groups must have x_position when using custom positions")
        positions = {g.name: float(g.x_position) for g in groups} | {
            variable.remaining_name: float(variable.remaining_position),
        }
        if any(not np.isfinite(v) for v in positions.values()):
            raise ValueError("x_position values must be finite")
        if len(set(positions.values())) != len(positions.values()):
            raise ValueError("x_position values must be unique")
        order = [k for k, _v in sorted(positions.items(), key=lambda kv: kv[1])]
    else:
        order = [g.name for g in groups] + [variable.remaining_name]
    return labels, order


def compute_group_labels_for_variable(
    *, df: pd.DataFrame, variable: ApiAeXVariable
) -> tuple[pd.Series, list[str]]:
    if variable.kind == "cross":
        return _compute_group_labels_for_cross_variable(df=df, variable=variable)
    return _compute_group_labels_for_atomic_variable(df=df, variable=variable)


def _weighted_r2(
    *, y: np.ndarray, y_hat: np.ndarray, w: np.ndarray | None
) -> float | None:
    if y.shape != y_hat.shape:
        return None
    if w is None:
        y_mean = float(np.mean(y))
        sst = float(np.sum((y - y_mean) ** 2))
        sse = float(np.sum((y - y_hat) ** 2))
    else:
        w_sum = float(np.sum(w))
        if w_sum <= 0:
            return None
        y_mean = float(np.sum(w * y) / w_sum)
        sst = float(np.sum(w * (y - y_mean) ** 2))
        sse = float(np.sum(w * (y - y_hat) ** 2))
    if sst <= 0:
        return None
    return 1.0 - (sse / sst)


def compute_polynomial_fit(
    *,
    rows: list[ApiAeUnivariateRow],
    x_variable: ApiAeXVariable,
    params: ApiAePolynomialFitParameters,
    x_domain: tuple[float, float] | None = None,
) -> ApiAePolynomialFitResults | None:
    deg = int(params.degree)
    if deg < 1 or deg > 3:
        raise ValueError("poly_fit.degree must be 1, 2, or 3")

    xs: list[float] = []
    ys: list[float] = []
    ws: list[float] = []

    for r in rows:
        if r.variable_group == "Total":
            continue
        if r.ae is None or not np.isfinite(float(r.ae)):
            continue
        ae_val = float(r.ae)

        if x_variable.kind in {"numeric", "date"}:
            if r.avg_x is None or not np.isfinite(float(r.avg_x)):
                continue
            xs.append(float(r.avg_x))
        else:
            if r.x_coord is None or not np.isfinite(float(r.x_coord)):
                continue
            xs.append(float(r.x_coord))

        ys.append(ae_val)
        ws.append(float(max(1, int(r.sample_size))))

    if len(xs) < deg + 1:
        return None

    x = np.asarray(xs, dtype=float)
    y = np.asarray(ys, dtype=float)
    w = np.asarray(ws, dtype=float) if bool(params.weighted) else None

    try:
        coeffs = np.polyfit(x, y, deg=deg, w=w)
    except Exception as exc:  # pragma: no cover
        raise ValueError("Failed to fit polynomial") from exc

    y_hat = np.polyval(coeffs, x)
    r2 = _weighted_r2(y=y, y_hat=y_hat, w=w)

    if x_domain is not None:
        x_min, x_max = x_domain
    else:
        x_min = float(np.min(x))
        x_max = float(np.max(x))

    fit_xs: np.ndarray
    if x_variable.kind in {"numeric", "date"}:
        if not np.isfinite(x_min) or not np.isfinite(x_max):
            return None
        if x_min == x_max:
            fit_xs = np.asarray([x_min], dtype=float)
        else:
            fit_xs = np.linspace(x_min, x_max, 200)
    else:
        if not np.isfinite(x_min) or not np.isfinite(x_max):
            return None
        if x_min == x_max:
            fit_xs = np.asarray([x_min], dtype=float)
        else:
            fit_xs = np.linspace(x_min, x_max, 200)

    fit_ys = np.polyval(coeffs, fit_xs)
    fit_rows = [[float(fit_xs[i]), float(fit_ys[i])] for i in range(len(fit_xs))]

    return ApiAePolynomialFitResults(
        degree=deg,
        weighted=bool(params.weighted),
        coefficients=[float(c) for c in coeffs.tolist()],
        r2=r2,
        fit_table=ApiChartTable(
            columns=[
                ApiChartColumn(name="x", format=ApiSeriesFormat.NUMBER),
                ApiChartColumn(name="y_hat", format=ApiSeriesFormat.NUMBER),
            ],
            rows=fit_rows,
        ),
    )


def _aggregate(
    *,
    df: pd.DataFrame,
    group_col: str,
    avg_col: str | None,
    app_id_column: str,
    mec_column: str,
    mac_column: str,
    man_column: str | None,
    men_column: str | None,
    moc_column: str | None,
    face_amount_column: str | None,
    order: list[str] | None,
) -> list[_AggRow]:
    grouped = df.groupby(group_col, dropna=False)
    rows: list[_AggRow] = []
    for key, g in grouped:
        label = str(key)
        avg_x = None
        if avg_col is not None:
            avg_series = pd.to_numeric(g[avg_col], errors="coerce")
            avg_series = avg_series[np.isfinite(avg_series.to_numpy(dtype=float))]
            if len(avg_series):
                avg_x = float(avg_series.mean())
        
        actual_amount = 0.0
        expected_amount = 0.0
        if man_column is not None and man_column in g.columns:
            actual_amount = float(g[man_column].sum())
        if men_column is not None and men_column in g.columns:
            expected_amount = float(g[men_column].sum())
        
        exposure_count = 0.0
        if moc_column is not None and moc_column in g.columns:
            exposure_count = float(g[moc_column].sum())
        
        total_face_amount = 0.0
        if face_amount_column is not None and face_amount_column in g.columns:
            # Sum face amount by unique policy number only
            face_by_policy = g.groupby(app_id_column, dropna=True)[face_amount_column].first()
            face_sum = face_by_policy.sum()
            total_face_amount = 0.0 if pd.isna(face_sum) else float(face_sum)
        
        rows.append(
            _AggRow(
                key=label,
                avg_x=avg_x,
                sample_size=int(g[app_id_column].nunique(dropna=True)),
                deaths=float(g[mac_column].sum()),
                expected=float(g[mec_column].sum()),
                actual_amount=actual_amount,
                expected_amount=expected_amount,
                exposure_count=exposure_count,
                total_face_amount=total_face_amount,
            )
        )

    if order is not None:
        by_key = {r.key: r for r in rows}
        ordered = [by_key[k] for k in order if k in by_key]
        remainder = [r for r in rows if r.key not in set(order)]
        rows = ordered + sorted(remainder, key=lambda r: r.key)
    else:
        rows = sorted(rows, key=lambda r: r.key)
    return rows


def _rows_to_api(
    rows: list[_AggRow], *, x_coord_by_key: dict[str, float] | None = None
) -> list[ApiAeUnivariateRow]:
    api_rows: list[ApiAeUnivariateRow] = []
    for r in rows:
        ae = safe_div(r.deaths, r.expected)
        ae_amount = safe_div(r.actual_amount, r.expected_amount)
        
        # Calculate confidence intervals for A/E by count
        ae_ci_lower, ae_ci_upper = compute_ae_ci(
            mac=r.deaths,
            moc=r.exposure_count,
            mec=r.expected,
            confidence_level=0.95,
        )
        
        # Calculate confidence intervals for A/E by amount
        ae_amount_ci_lower, ae_amount_ci_upper = compute_ae_ci_amount(
            mac=r.deaths,
            moc=r.exposure_count,
            mec=r.expected,
            actual_amount=r.actual_amount,
            expected_amount=r.expected_amount,
            confidence_level=0.95,
        )
        
        api_rows.append(
            ApiAeUnivariateRow(
                variable_group=r.key,
                avg_x=r.avg_x,
                x_coord=x_coord_by_key.get(r.key) if x_coord_by_key is not None else None,
                sample_size=r.sample_size,
                deaths=r.deaths,
                expected_count=r.expected,
                actual_amount=r.actual_amount,
                expected_amount=r.expected_amount,
                exposure_count=r.exposure_count,
                total_face_amount=r.total_face_amount,
                ae=ae,
                ae_amount=ae_amount,
                ae_ci_lower=ae_ci_lower,
                ae_ci_upper=ae_ci_upper,
                ae_amount_ci_lower=ae_amount_ci_lower,
                ae_amount_ci_upper=ae_amount_ci_upper,
            )
        )
    return api_rows


def _compute_numeric(
    *,
    df: pd.DataFrame,
    spec: ApiAeXVariableNumeric,
    app_id_column: str,
    mec_column: str,
    mac_column: str,
    man_column: str | None,
    men_column: str | None,
    moc_column: str | None,
    face_amount_column: str | None,
) -> list[ApiAeUnivariateRow]:
    x = pd.to_numeric(df[spec.name], errors="coerce")
    finite = x[np.isfinite(x.to_numpy(dtype=float))]
    if len(finite) == 0:
        raise ValueError("X variable has no numeric values")

    group_col = "__x_group__"
    order: list[str] = []

    if spec.binning in {ApiNumericBinning.UNIFORM, ApiNumericBinning.QUINTILE}:
        if spec.bin_count is None:
            raise ValueError("bin_count is required")
        bin_count = int(spec.bin_count)
        if spec.binning == ApiNumericBinning.UNIFORM:
            lo = float(finite.min())
            hi = float(finite.max())
            if lo == hi:
                edges = np.array([lo, hi], dtype=float)
            else:
                edges = np.linspace(lo, hi, bin_count + 1)
            bins = pd.cut(x, bins=edges, include_lowest=True, duplicates="drop")
        else:
            bins = pd.qcut(x, q=bin_count, duplicates="drop")

        labels, order = _labels_from_bins(bins)
        df = df.copy()
        df[group_col] = labels
        df["__x_value__"] = x

        agg = _aggregate(
            df=df,
            group_col=group_col,
            avg_col="__x_value__",
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=order,
        )
        x_coord_by_key = {r.key: float(i) for i, r in enumerate(agg)}
        return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    if spec.binning == ApiNumericBinning.CUSTOM:
        raw = spec.custom_edges or []
        edges_raw = sorted({float(x) for x in raw if np.isfinite(float(x))})
        if len(edges_raw) == 0:
            raise ValueError("custom_edges must be provided for custom binning")

        lo = float(finite.min())
        hi = float(finite.max())
        inner = [e for e in edges_raw if lo < e < hi]
        edges = [lo] + inner + [hi]
        if len(edges) < 2:
            raise ValueError("custom_edges produce no valid bins")

        bins = pd.cut(x, bins=edges, include_lowest=True, duplicates="drop")
        labels, order = _labels_from_bins(bins)
        df = df.copy()
        df[group_col] = labels
        df["__x_value__"] = x

        agg = _aggregate(
            df=df,
            group_col=group_col,
            avg_col="__x_value__",
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=order,
        )
        x_coord_by_key = {r.key: float(i) for i, r in enumerate(agg)}
        return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    raise ValueError("Unsupported numeric binning")


def _compute_date(
    *,
    df: pd.DataFrame,
    spec: ApiAeXVariableDate,
    app_id_column: str,
    mec_column: str,
    mac_column: str,
    man_column: str | None,
    men_column: str | None,
    moc_column: str | None,
    face_amount_column: str | None,
) -> list[ApiAeUnivariateRow]:
    dt = pd.to_datetime(df[spec.name], errors="coerce", utc=True)
    mask = dt.notna()
    if not bool(mask.any()):
        raise ValueError("X variable has no datetime values")

    sec = _dt_to_seconds(dt)
    finite = sec[mask]
    lo = float(finite.min())
    hi = float(finite.max())

    group_col = "__x_group__"
    order: list[str] = []

    if spec.binning in {ApiNumericBinning.UNIFORM, ApiNumericBinning.QUINTILE}:
        if spec.bin_count is None:
            raise ValueError("bin_count is required")
        bin_count = int(spec.bin_count)
        if spec.binning == ApiNumericBinning.UNIFORM:
            edges = (
                np.array([lo, hi], dtype=float)
                if lo == hi
                else np.linspace(lo, hi, bin_count + 1)
            )
            bins = pd.cut(sec, bins=edges, include_lowest=True, duplicates="drop")
        else:
            bins = pd.qcut(sec, q=bin_count, duplicates="drop")

        labels, order = _labels_from_bins_date(bins)
        df2 = df.copy()
        df2[group_col] = labels
        df2["__x_value__"] = sec

        agg = _aggregate(
            df=df2,
            group_col=group_col,
            avg_col="__x_value__",
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=order,
        )
        x_coord_by_key = {r.key: float(i) for i, r in enumerate(agg)}
        return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    if spec.binning == ApiNumericBinning.CUSTOM:
        raw = spec.custom_edges or []
        parsed = pd.to_datetime(pd.Series(raw, dtype="string"), errors="coerce", utc=True)
        secs_raw = _dt_to_seconds(parsed).to_numpy(dtype=float)
        edges_raw = sorted({float(v) for v in secs_raw.tolist() if np.isfinite(float(v))})
        if len(edges_raw) == 0:
            raise ValueError("custom_edges must be provided for custom binning")

        inner = [e for e in edges_raw if lo < e < hi]
        edges = [lo] + inner + [hi]
        if len(edges) < 2:
            raise ValueError("custom_edges produce no valid bins")

        bins = pd.cut(sec, bins=edges, include_lowest=True, duplicates="drop")
        labels, order = _labels_from_bins_date(bins)
        df2 = df.copy()
        df2[group_col] = labels
        df2["__x_value__"] = sec

        agg = _aggregate(
            df=df2,
            group_col=group_col,
            avg_col="__x_value__",
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=order,
        )
        x_coord_by_key = {r.key: float(i) for i, r in enumerate(agg)}
        return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    raise ValueError("Unsupported date binning")


def _compute_categorical(
    *,
    df: pd.DataFrame,
    spec: ApiAeXVariableCategorical,
    app_id_column: str,
    mec_column: str,
    mac_column: str,
    man_column: str | None,
    men_column: str | None,
    moc_column: str | None,
    face_amount_column: str | None,
) -> list[ApiAeUnivariateRow]:
    s = df[spec.name].astype("string")
    s = s.fillna("Missing")
    values = s.astype(str)

    group_col = "__x_group__"
    df = df.copy()

    if spec.grouping == "all_unique":
        df[group_col] = values
        agg = _aggregate(
            df=df,
            group_col=group_col,
            avg_col=None,
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=None,
        )
        x_coord_by_key = {r.key: float(i) for i, r in enumerate(agg)}
        return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    groups = spec.groups or []
    names = [g.name for g in groups] + [spec.remaining_name]
    if len(set(names)) != len(names):
        raise ValueError("Group names must be unique")

    name_by_value: dict[str, str] = {}
    for g in groups:
        for v in g.values:
            if v in name_by_value:
                raise ValueError("A categorical value cannot be in multiple groups")
            name_by_value[v] = g.name

    df[group_col] = values.map(lambda v: name_by_value.get(v, spec.remaining_name))
    group_positions = [g.x_position for g in groups]
    any_pos = any(p is not None for p in group_positions) or (
        spec.remaining_position is not None
    )
    x_coord_by_key: dict[str, float] | None = None
    if any_pos:
        if spec.remaining_position is None or any(p is None for p in group_positions):
            raise ValueError("All groups must have x_position when using custom positions")
        x_coord_by_key = {g.name: float(g.x_position) for g in groups}
        x_coord_by_key[spec.remaining_name] = float(spec.remaining_position)
        if any(not np.isfinite(v) for v in x_coord_by_key.values()):
            raise ValueError("x_position values must be finite")
        if len(set(x_coord_by_key.values())) != len(x_coord_by_key.values()):
            raise ValueError("x_position values must be unique")
        order = [k for k, _v in sorted(x_coord_by_key.items(), key=lambda kv: kv[1])]
    else:
        order = [g.name for g in groups] + [spec.remaining_name]
        x_coord_by_key = {name: float(i) for i, name in enumerate(order)}
    agg = _aggregate(
        df=df,
        group_col=group_col,
        avg_col=None,
        app_id_column=app_id_column,
        mec_column=mec_column,
        mac_column=mac_column,
        man_column=man_column,
        men_column=men_column,
        moc_column=moc_column,
        face_amount_column=face_amount_column,
        order=order,
    )
    return _rows_to_api(agg, x_coord_by_key=x_coord_by_key)


def compute_ae_univariate_rows(
    *,
    df: pd.DataFrame,
    x_variable: ApiAeXVariable,
    app_id_column: str,
    mec_column: str,
    mac_column: str,
    man_column: str | None = None,
    men_column: str | None = None,
    moc_column: str | None = None,
    face_amount_column: str | None = None,
) -> list[ApiAeUnivariateRow]:
    if x_variable.kind == "numeric":
        rows = _compute_numeric(
            df=df,
            spec=x_variable,
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
        )
    elif x_variable.kind == "date":
        rows = _compute_date(
            df=df,
            spec=x_variable,
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
        )
    elif x_variable.kind == "categorical":
        rows = _compute_categorical(
            df=df,
            spec=x_variable,
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
        )
    else:  # cross
        labels, order = compute_group_labels_for_variable(df=df, variable=x_variable)
        df2 = df.copy()
        df2["__x_group__"] = labels.astype(str)
        agg = _aggregate(
            df=df2,
            group_col="__x_group__",
            avg_col=None,
            app_id_column=app_id_column,
            mec_column=mec_column,
            mac_column=mac_column,
            man_column=man_column,
            men_column=men_column,
            moc_column=moc_column,
            face_amount_column=face_amount_column,
            order=order,
        )
        x_coord_by_key: dict[str, float] | None = None
        if any(g.x_position is not None for g in (x_variable.groups or [])) or (
            x_variable.remaining_position is not None
        ):
            groups = x_variable.groups or []
            if x_variable.remaining_position is None or any(
                g.x_position is None for g in groups
            ):
                raise ValueError(
                    "All cross groups must have x_position when using custom positions"
                )
            x_coord_by_key = {g.name: float(g.x_position) for g in groups}
            x_coord_by_key[x_variable.remaining_name] = float(
                x_variable.remaining_position
            )
        else:
            x_coord_by_key = {name: float(i) for i, name in enumerate(order)}
        rows = _rows_to_api(agg, x_coord_by_key=x_coord_by_key)

    total_avg_x: float | None = None
    if x_variable.kind == "numeric":
        x_all = pd.to_numeric(df[x_variable.name], errors="coerce")
        x_all = x_all[np.isfinite(x_all.to_numpy(dtype=float))]
        if len(x_all):
            total_avg_x = float(x_all.mean())
    elif x_variable.kind == "date":
        dt = pd.to_datetime(df[x_variable.name], errors="coerce", utc=True)
        mask = dt.notna()
        if bool(mask.any()):
            sec = _dt_to_seconds(dt)
            total_avg_x = float(sec[mask].mean())
    total_deaths = float(df[mac_column].sum())
    total_expected = float(df[mec_column].sum())
    total_ae = safe_div(total_deaths, total_expected)
    total_sample_size = int(df[app_id_column].nunique(dropna=True))
    
    total_actual_amount = 0.0
    total_expected_amount = 0.0
    if man_column is not None and man_column in df.columns:
        total_actual_amount = float(df[man_column].sum())
    if men_column is not None and men_column in df.columns:
        total_expected_amount = float(df[men_column].sum())
    total_ae_amount = safe_div(total_actual_amount, total_expected_amount)
    
    total_exposure_count = 0.0
    if moc_column is not None and moc_column in df.columns:
        total_exposure_count = float(df[moc_column].sum())
    
    total_face_amount = 0.0
    if face_amount_column is not None and face_amount_column in df.columns:
        # Sum face amount by unique policy number only
        face_by_policy = df.groupby(app_id_column, dropna=True)[face_amount_column].first()
        face_sum = face_by_policy.sum()
        total_face_amount = 0.0 if pd.isna(face_sum) else float(face_sum)

    # Calculate confidence intervals for total
    total_ci_lower, total_ci_upper = compute_ae_ci(
        mac=total_deaths,
        moc=total_exposure_count,
        mec=total_expected,
        confidence_level=0.95,
    )

    rows.append(
        ApiAeUnivariateRow(
            variable_group="Total",
            avg_x=total_avg_x,
            x_coord=None,
            sample_size=total_sample_size,
            deaths=total_deaths,
            expected_count=total_expected,
            actual_amount=total_actual_amount,
            expected_amount=total_expected_amount,
            exposure_count=total_exposure_count,
            total_face_amount=total_face_amount,
            ae=total_ae,
            ae_amount=total_ae_amount,
            ae_ci_lower=total_ci_lower,
            ae_ci_upper=total_ci_upper,
        )
    )
    return rows
