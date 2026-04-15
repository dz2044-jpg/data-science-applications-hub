from __future__ import annotations

from io import BytesIO

import pandas as pd


def _validate_and_normalize_dataframe(
    df: pd.DataFrame,
    *,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
) -> pd.DataFrame:
    """Validate and normalize a DataFrame regardless of source format."""
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


def read_mortality_csv_upload(
    *,
    csv_bytes: bytes,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
) -> pd.DataFrame:
    """Read and normalize data from CSV file bytes."""
    df = pd.read_csv(BytesIO(csv_bytes))
    return _validate_and_normalize_dataframe(
        df,
        date_column=date_column,
        value_column=value_column,
        group_column=group_column,
        date_format=date_format,
    )


def read_mortality_excel_upload(
    *,
    excel_bytes: bytes,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """Read and normalize data from Excel file bytes."""
    df = pd.read_excel(BytesIO(excel_bytes), sheet_name=sheet_name)
    return _validate_and_normalize_dataframe(
        df,
        date_column=date_column,
        value_column=value_column,
        group_column=group_column,
        date_format=date_format,
    )


def read_mortality_parquet_upload(
    *,
    parquet_bytes: bytes,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
) -> pd.DataFrame:
    """Read and normalize data from Parquet file bytes."""
    df = pd.read_parquet(BytesIO(parquet_bytes), engine='pyarrow')
    return _validate_and_normalize_dataframe(
        df,
        date_column=date_column,
        value_column=value_column,
        group_column=group_column,
        date_format=date_format,
    )


def read_mortality_upload(
    *,
    file_bytes: bytes,
    file_format: str,
    date_column: str,
    value_column: str,
    group_column: str | None,
    date_format: str | None,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """Read and normalize data from uploaded file in any supported format.
    
    Args:
        file_bytes: Raw file bytes
        file_format: One of 'csv', 'excel', or 'parquet'
        date_column: Name of the date column
        value_column: Name of the value column
        group_column: Optional name of the group column
        date_format: Optional date format string
        sheet_name: Sheet name or index for Excel files (default: 0)
    
    Returns:
        Normalized DataFrame with columns: date, series, value
    
    Raises:
        ValueError: If format is invalid or data validation fails
    """
    format_lower = file_format.lower()
    
    if format_lower in ("csv", ".csv"):
        return read_mortality_csv_upload(
            csv_bytes=file_bytes,
            date_column=date_column,
            value_column=value_column,
            group_column=group_column,
            date_format=date_format,
        )
    elif format_lower in ("excel", "xlsx", "xls", ".xlsx", ".xls"):
        return read_mortality_excel_upload(
            excel_bytes=file_bytes,
            date_column=date_column,
            value_column=value_column,
            group_column=group_column,
            date_format=date_format,
            sheet_name=sheet_name,
        )
    elif format_lower in ("parquet", ".parquet"):
        return read_mortality_parquet_upload(
            parquet_bytes=file_bytes,
            date_column=date_column,
            value_column=value_column,
            group_column=group_column,
            date_format=date_format,
        )
    else:
        raise ValueError(
            f"Unsupported file format: {file_format}. "
            f"Supported formats: csv, excel (xlsx/xls), parquet"
        )
