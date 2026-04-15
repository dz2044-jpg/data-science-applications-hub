from __future__ import annotations

from io import BytesIO

import pandas as pd


def read_mortality_csv_upload(
    *,
    csv_bytes: bytes,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
) -> pd.DataFrame:
    df = pd.read_csv(BytesIO(csv_bytes))
    required_columns = {date_column, value_column}
    missing = sorted(required_columns - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if group_column is not None and group_column not in df.columns:
        raise ValueError(f"Missing group column: {group_column}")

    parsed_dates = pd.to_datetime(
        df[date_column],
        format=date_format,
        errors="coerce",
        utc=False,
    )
    parsed_values = pd.to_numeric(df[value_column], errors="coerce")

    invalid_date_rows = parsed_dates.isna().sum()
    invalid_value_rows = parsed_values.isna().sum()
    if invalid_date_rows:
        raise ValueError(f"Found {invalid_date_rows} rows with invalid dates")
    if invalid_value_rows:
        raise ValueError(f"Found {invalid_value_rows} rows with invalid values")

    series_name = (
        df[group_column].astype(str) if group_column is not None else "deaths"
    )

    normalized = pd.DataFrame(
        {
            "date": parsed_dates.dt.normalize(),
            "series": series_name,
            "value": parsed_values.astype(float),
        }
    )
    return normalized
