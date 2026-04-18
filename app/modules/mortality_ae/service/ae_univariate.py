from __future__ import annotations

import numpy as np
import pandas as pd

from app.core.models.dataset_config import get_mortality_module_config
from app.core.service.dataframe_loader import (
    read_dataframe_from_bytes,
    read_dataframe_from_path,
)
from app.core.service.dataset_config import get_dataset_config_with_file
from app.modules.mortality_ae.calc.ae_univariate import (
    compute_ae_univariate_rows,
    compute_group_labels_for_variable,
    compute_polynomial_fit,
)
from app.modules.mortality_ae.models.ae import (
    ApiAeColaM1StackedResults,
    ApiAeColaM1StackedRow,
    ApiAeExclusions,
    ApiAePolynomialFitResults,
    ApiAeUnivariateFromConfigParameters,
    ApiAeUnivariateParameters,
    ApiAeUnivariateResults,
    ApiAeUnivariateRow,
    ApiAeUnivariateSplitResults,
    ApiAeXVariable,
)
from app.modules.mortality_ae.models.ae import ApiColumnMapping as ApiAeColumnMapping
from app.modules.mortality_ae.service.dataset_schema import (
    COLA_M1_COLUMN,
    COLA_M2_COLUMN,
    MAC_COLUMN,
    MEC_COLUMN,
)
from app.utils.env import (
    get_application_id_column_override,
    get_max_cola_m1_causes,
    get_max_split_groups,
)


def _is_death_cause_m1(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v:
        return True  # treat empty as "Missing"
    return v not in {"alive", "no data"}


def _compute_cola_m1_stacked(
    *,
    df: pd.DataFrame,
    x_variable: ApiAeXVariable,
    mac_column: str,
    man_column: str | None = None,
    cola_m1_column: str | None = None,
    causes: list[str] | None = None,
) -> ApiAeColaM1StackedResults | None:
    if cola_m1_column is None or cola_m1_column not in df.columns:
        return None

    x_labels, x_order = compute_group_labels_for_variable(df=df, variable=x_variable)
    df2 = df.copy()
    df2["__x_group__"] = x_labels.astype(str)

    mac = pd.to_numeric(df2[mac_column], errors="coerce")
    mask_mac = np.isfinite(mac.to_numpy(dtype=float))
    if not bool(mask_mac.any()):
        return ApiAeColaM1StackedResults(causes=causes or [], rows=[], total_deaths=0.0, total_amount=0.0)
    df2 = df2.loc[mask_mac].copy()
    df2[mac_column] = mac.loc[mask_mac]
    
    # Process MAN column for amounts (if available)
    has_amounts = man_column is not None and man_column in df2.columns
    if has_amounts:
        man = pd.to_numeric(df2[man_column], errors="coerce")
        df2[man_column] = man.fillna(0.0)

    m1_raw = df2[cola_m1_column].fillna("").astype(str).str.strip()
    m1_norm = m1_raw.mask(m1_raw == "", "Missing")
    keep = m1_norm.map(_is_death_cause_m1)
    df2 = df2.loc[keep].copy()
    df2["__m1__"] = m1_norm.loc[keep]

    if df2.empty:
        rows = [
            ApiAeColaM1StackedRow(
                x_group=str(g),
                total_deaths=0.0,
                deaths_by_m1={},
                total_amount=0.0,
                amounts_by_m1={}
            )
            for g in x_order
        ]
        return ApiAeColaM1StackedResults(causes=causes or [], rows=rows, total_deaths=0.0, total_amount=0.0)

    max_causes = get_max_cola_m1_causes()

    if causes is None:
        totals_by_m1 = df2.groupby("__m1__", dropna=False)[mac_column].sum()
        totals_by_m1 = totals_by_m1.sort_values(ascending=False)
        base = [str(k) for k in totals_by_m1.index.tolist()[:max_causes]]
        other_sum = (
            float(totals_by_m1.iloc[max_causes:].sum())
            if len(totals_by_m1) > max_causes
            else 0.0
        )
        causes = base + (["Other"] if other_sum > 0 else [])
    else:
        causes = [str(c) for c in causes]

    main_causes = [c for c in causes if c != "Other"]
    set_main = set(main_causes)

    grouped_deaths = (
        df2.groupby(["__x_group__", "__m1__"], dropna=False)[mac_column]
        .sum()
        .astype(float)
    )
    
    # Group amounts if available
    grouped_amounts = None
    if has_amounts:
        grouped_amounts = (
            df2.groupby(["__x_group__", "__m1__"], dropna=False)[man_column]
            .sum()
            .astype(float)
        )

    rows: list[ApiAeColaM1StackedRow] = []
    total_deaths = float(df2[mac_column].sum())
    total_amount = float(df2[man_column].sum()) if has_amounts else 0.0
    
    for g in x_order:
        g_key = str(g)
        deaths_by_m1: dict[str, float] = {}
        amounts_by_m1: dict[str, float] = {}
        group_total_deaths = 0.0
        group_total_amount = 0.0
        other_deaths = 0.0
        other_amount = 0.0
        
        # Sum all causes for this group.
        for (xg, m1), val in grouped_deaths.items():
            if str(xg) != g_key:
                continue
            deaths = float(val)
            if deaths <= 0:
                continue
            group_total_deaths += deaths
            m1_name = str(m1)
            
            # Get corresponding amount if available
            amount = 0.0
            if grouped_amounts is not None:
                amount = float(grouped_amounts.get((xg, m1), 0.0))
                group_total_amount += amount
            
            if m1_name in set_main:
                deaths_by_m1[m1_name] = deaths_by_m1.get(m1_name, 0.0) + deaths
                if grouped_amounts is not None:
                    amounts_by_m1[m1_name] = amounts_by_m1.get(m1_name, 0.0) + amount
            else:
                other_deaths += deaths
                other_amount += amount

        if "Other" in causes and other_deaths > 0:
            deaths_by_m1["Other"] = other_deaths
            if grouped_amounts is not None:
                amounts_by_m1["Other"] = other_amount

        rows.append(
            ApiAeColaM1StackedRow(
                x_group=g_key,
                total_deaths=group_total_deaths,
                deaths_by_m1=deaths_by_m1,
                total_amount=group_total_amount,
                amounts_by_m1=amounts_by_m1,
            )
        )

    return ApiAeColaM1StackedResults(
        causes=causes,
        rows=rows,
        total_deaths=total_deaths,
        total_amount=total_amount
    )


def _detect_application_id_column(df: pd.DataFrame) -> str:
    override = get_application_id_column_override()
    if override:
        if override not in df.columns:
            raise ValueError(f"application_id_column '{override}' not found in dataset")
        return override

    candidates = [
        "application_number",
        "applicationnumber",
        "application_id",
        "applicationid",
        "app_number",
        "appnumber",
        "app_id",
        "appid",
        "policy_number",
        "policynumber",
        "record_id",
        "recordid",
    ]
    cols_by_lower = {str(c).lower(): str(c) for c in df.columns.tolist()}
    for key in candidates:
        if key in cols_by_lower:
            return cols_by_lower[key]

    raise ValueError(
        "Could not detect application id column; set INSIGHT_HUB_APPLICATION_ID_COLUMN"
    )


def _required_columns_for_variable(variable: ApiAeXVariable) -> list[str]:
    if variable.kind == "cross":
        return (
            _required_columns_for_variable(variable.a_variable)
            + _required_columns_for_variable(variable.b_variable)
        )
    return [variable.name]


def _apply_exclusions(
    *, df: pd.DataFrame, app_id_column: str, exclusions: ApiAeExclusions | None
) -> pd.DataFrame:
    if exclusions is None:
        return df

    exclude_m1 = {str(x).strip() for x in exclusions.exclude_cola_m1 if str(x).strip()}
    exclude_m2_by_m1: dict[str, set[str]] = {}
    for k, values in exclusions.exclude_cola_m2_by_m1.items():
        key = str(k).strip()
        if not key or key in exclude_m1:
            continue
        vals = {str(v).strip() for v in values if str(v).strip()}
        if vals:
            exclude_m2_by_m1[key] = vals

    if not exclude_m1 and not exclude_m2_by_m1:
        return df

    for col in [COLA_M1_COLUMN, COLA_M2_COLUMN]:
        if col not in df.columns:
            raise ValueError(f"Missing required column for exclusions: {col}")

    m1 = df[COLA_M1_COLUMN].fillna("").astype(str).str.strip()
    m2 = df[COLA_M2_COLUMN].fillna("").astype(str).str.strip()

    row_excluded = pd.Series(False, index=df.index)
    if exclude_m1:
        row_excluded = row_excluded | m1.isin(sorted(exclude_m1))
    if exclude_m2_by_m1:
        for key, vals in exclude_m2_by_m1.items():
            row_excluded = row_excluded | ((m1 == key) & m2.isin(sorted(vals)))

    if not bool(row_excluded.any()):
        return df

    excluded_app_ids = (
        df.loc[row_excluded, app_id_column].dropna().drop_duplicates().tolist()
    )
    if not excluded_app_ids:
        return df

    return df.loc[~df[app_id_column].isin(excluded_app_ids)].copy()


def _perform_ae_univariate_core(*, df: pd.DataFrame, params: ApiAeUnivariateParameters) -> ApiAeUnivariateResults:
    """Core A/E univariate logic that works on a dataframe."""
    # Get column mappings from params or use defaults
    if params.column_mapping is not None:
        policy_number_column = params.column_mapping.policy_number_column or _detect_application_id_column(df)
        mac_column = params.column_mapping.mac_column or MAC_COLUMN
        mec_column = params.column_mapping.mec_column or MEC_COLUMN
        man_column = params.column_mapping.man_column or None
        men_column = params.column_mapping.men_column or None
        moc_column = params.column_mapping.moc_column or None
        cola_m1_column = params.column_mapping.cola_m1_column or None
        face_amount_column = params.column_mapping.face_amount_column or None
    else:
        policy_number_column = _detect_application_id_column(df)
        mac_column = MAC_COLUMN
        mec_column = MEC_COLUMN
        man_column = None
        men_column = None
        moc_column = None
        cola_m1_column = None
        face_amount_column = None

    # Use provided application_id_column if specified
    app_id_column = params.application_id_column if params.application_id_column is not None else policy_number_column

    required_cols = [mec_column, mac_column] + _required_columns_for_variable(
        params.x_variable
    )
    if params.split_variable is not None:
        required_cols += _required_columns_for_variable(params.split_variable)

    for required in required_cols:
        if required not in df.columns:
            raise ValueError(f"Missing required column: {required}")

    if app_id_column not in df.columns:
        raise ValueError(f"Missing application id column: {app_id_column}")

    # Validate and convert MEC/MAC columns to numeric
    for col_name, col_label in [(mec_column, 'MEC'), (mac_column, 'MAC')]:
        original_na_count = df[col_name].isna().sum()
        df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
        new_na_count = df[col_name].isna().sum()
        # Only fail if conversion created NEW NaN values (non-numeric data)
        if new_na_count > original_na_count:
            raise ValueError(
                f"Column '{col_name}' ({col_label}) contains non-numeric values. "
                f"Please select a numeric column."
            )

    # Validate MAN/MEN/Face Amount if provided
    if man_column is not None and man_column in df.columns:
        df[man_column] = pd.to_numeric(df[man_column], errors="coerce")
    if men_column is not None and men_column in df.columns:
        df[men_column] = pd.to_numeric(df[men_column], errors="coerce")
    if face_amount_column is not None and face_amount_column in df.columns:
        df[face_amount_column] = pd.to_numeric(df[face_amount_column], errors="coerce")

    df = _apply_exclusions(
        df=df,
        app_id_column=app_id_column,
        exclusions=params.exclusions,
    )

    if df.empty:
        empty_rows = [
            ApiAeUnivariateRow(
                variable_group="Total",
                avg_x=None,
                sample_size=0,
                deaths=0.0,
                expected_count=0.0,
                actual_amount=0.0,
                expected_amount=0.0,
                total_face_amount=0.0,
                ae=None,
                ae_amount=None,
            )
        ]
        return ApiAeUnivariateResults(rows=empty_rows, split_results=None)

    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=params.x_variable,
        app_id_column=app_id_column,
        mec_column=mec_column,
        mac_column=mac_column,
        man_column=man_column,
        men_column=men_column,
        moc_column=moc_column,
        face_amount_column=face_amount_column,
    )

    cola_m1_stacked = _compute_cola_m1_stacked(
        df=df,
        x_variable=params.x_variable,
        mac_column=mac_column,
        man_column=man_column,
        cola_m1_column=cola_m1_column,
    )

    poly_fit: ApiAePolynomialFitResults | None = None
    if params.poly_fit is not None:
        x_domain: tuple[float, float] | None = None
        if params.x_variable.kind == "numeric":
            x = pd.to_numeric(df[params.x_variable.name], errors="coerce")
            mask = np.isfinite(x.to_numpy(dtype=float))
            if bool(mask.any()):
                finite = x.loc[mask]
                x_domain = (float(finite.min()), float(finite.max()))
        if params.x_variable.kind == "date":
            dt = pd.to_datetime(df[params.x_variable.name], errors="coerce", utc=True)
            mask = dt.notna()
            if bool(mask.any()):
                sec = (
                    pd.Series(dt.view("int64"), index=dt.index, dtype="int64").astype(float)
                    / 1_000_000_000.0
                )
                finite = sec.loc[mask]
                x_domain = (float(finite.min()), float(finite.max()))
        poly_fit = compute_polynomial_fit(
            rows=rows,
            x_variable=params.x_variable,
            params=params.poly_fit,
            x_domain=x_domain,
        )

    split_results: list[ApiAeUnivariateSplitResults] | None = None
    if params.split_variable is not None:
        labels, order = compute_group_labels_for_variable(
            df=df,
            variable=params.split_variable,
        )
        df = df.copy()
        df["__split_group__"] = labels

        max_groups = get_max_split_groups()
        if len(order) > max_groups:
            raise ValueError(
                f"Too many split groups ({len(order)}); increase INSIGHT_HUB_MAX_SPLIT_GROUPS"
            )

        split_results = []
        for key in order:
            subset = df[df["__split_group__"] == key]
            if subset.empty:
                continue
            subset_rows = compute_ae_univariate_rows(
                df=subset,
                x_variable=params.x_variable,
                app_id_column=app_id_column,
                mec_column=mec_column,
                mac_column=mac_column,
                man_column=man_column,
                men_column=men_column,
                moc_column=moc_column,
                face_amount_column=face_amount_column,
            )
            split_fit: ApiAePolynomialFitResults | None = None
            if params.poly_fit is not None:
                x_domain: tuple[float, float] | None = None
                if params.x_variable.kind == "numeric":
                    x = pd.to_numeric(subset[params.x_variable.name], errors="coerce")
                    mask = np.isfinite(x.to_numpy(dtype=float))
                    if bool(mask.any()):
                        finite = x.loc[mask]
                        x_domain = (float(finite.min()), float(finite.max()))
                if params.x_variable.kind == "date":
                    dt = pd.to_datetime(subset[params.x_variable.name], errors="coerce", utc=True)
                    mask = dt.notna()
                    if bool(mask.any()):
                        sec = (
                            pd.Series(dt.view("int64"), index=dt.index, dtype="int64").astype(float)
                            / 1_000_000_000.0
                        )
                        finite = sec.loc[mask]
                        x_domain = (float(finite.min()), float(finite.max()))
                split_fit = compute_polynomial_fit(
                    rows=subset_rows,
                    x_variable=params.x_variable,
                    params=params.poly_fit,
                    x_domain=x_domain,
                )
            split_cola = (
                _compute_cola_m1_stacked(
                    df=subset,
                    x_variable=params.x_variable,
                    mac_column=mac_column,
                    man_column=man_column,
                    cola_m1_column=cola_m1_column,
                    causes=(cola_m1_stacked.causes if cola_m1_stacked is not None else None),
                )
                if cola_m1_stacked is not None
                else None
            )
            split_results.append(
                ApiAeUnivariateSplitResults(
                    split_group=str(key),
                    rows=subset_rows,
                    poly_fit=split_fit,
                    cola_m1_stacked=split_cola,
                )
            )

    return ApiAeUnivariateResults(
        rows=rows,
        split_results=split_results,
        poly_fit=poly_fit,
        cola_m1_stacked=cola_m1_stacked,
    )

def perform_ae_univariate_from_upload(*, file_bytes: bytes, filename: str, params: ApiAeUnivariateParameters) -> ApiAeUnivariateResults:
    """Perform A/E univariate analysis from uploaded file bytes (CSV, Excel, Parquet)."""
    df = read_dataframe_from_bytes(file_bytes=file_bytes, filename=filename)
    return _perform_ae_univariate_core(df=df, params=params)


def perform_ae_univariate_from_config(
    *, params: ApiAeUnivariateFromConfigParameters
) -> ApiAeUnivariateResults:
    """Perform A/E univariate analysis from a saved dataset configuration."""
    config, file_path = get_dataset_config_with_file(params.config_id)
    mortality_config = get_mortality_module_config(config)
    df = read_dataframe_from_path(file_path=file_path)

    config_params = ApiAeUnivariateParameters(
        dataset_name=config.dataset_name,
        x_variable=params.x_variable,
        split_variable=params.split_variable,
        application_id_column=params.application_id_column,
        column_mapping=ApiAeColumnMapping(**mortality_config.model_dump()),
        exclusions=params.exclusions,
        poly_fit=params.poly_fit,
    )
    return _perform_ae_univariate_core(df=df, params=config_params)
