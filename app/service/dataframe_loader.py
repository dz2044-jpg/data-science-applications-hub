from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def _csv_skiprows_for_random_sample(
    *, total_rows: int, nrows: int, seed: int = 42
) -> set[int]:
    if total_rows <= nrows:
        return set()
    rng = random.Random(seed)
    keep_rows = set(rng.sample(range(1, total_rows + 1), nrows))
    return {idx for idx in range(1, total_rows + 1) if idx not in keep_rows}


def _count_csv_rows_from_bytes(file_bytes: bytes) -> int:
    return max(0, sum(1 for _ in pd.io.common.BytesIO(file_bytes)) - 1)


def _count_csv_rows_from_path(file_path: Path) -> int:
    with file_path.open("rb") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def read_dataframe_from_bytes(
    *,
    file_bytes: bytes,
    filename: str,
    nrows: int | None = None,
    random_sample: bool = False,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a dataframe from bytes for CSV, Excel, or Parquet."""
    suffix = Path(filename).suffix.lower()

    if suffix == ".csv":
        if random_sample and nrows is not None:
            total_rows = _count_csv_rows_from_bytes(file_bytes)
            skiprows = _csv_skiprows_for_random_sample(
                total_rows=total_rows,
                nrows=nrows,
            )
            return pd.read_csv(
                pd.io.common.BytesIO(file_bytes),
                skiprows=lambda x: x in skiprows,
                usecols=columns,
            )
        return pd.read_csv(
            pd.io.common.BytesIO(file_bytes),
            nrows=nrows,
            usecols=columns,
        )

    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(
            pd.io.common.BytesIO(file_bytes),
            usecols=columns,
        )
        if nrows is None:
            return df
        if random_sample and len(df) > nrows:
            return df.sample(n=nrows, random_state=42)
        return df.head(nrows)

    if suffix == ".parquet":
        df = pd.read_parquet(
            pd.io.common.BytesIO(file_bytes),
            engine="pyarrow",
            columns=columns,
        )
        if nrows is None:
            return df
        if random_sample and len(df) > nrows:
            return df.sample(n=nrows, random_state=42)
        return df.head(nrows)

    raise ValueError(f"Unsupported file format: {suffix}")


def read_dataframe_from_path(
    *,
    file_path: Path,
    nrows: int | None = None,
    random_sample: bool = False,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a dataframe from a file path for CSV, Excel, or Parquet."""
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        if random_sample and nrows is not None:
            total_rows = _count_csv_rows_from_path(file_path)
            skiprows = _csv_skiprows_for_random_sample(
                total_rows=total_rows,
                nrows=nrows,
            )
            return pd.read_csv(
                file_path,
                skiprows=lambda x: x in skiprows,
                usecols=columns,
            )
        return pd.read_csv(file_path, nrows=nrows, usecols=columns)

    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, usecols=columns)
        if nrows is None:
            return df
        if random_sample and len(df) > nrows:
            return df.sample(n=nrows, random_state=42)
        return df.head(nrows)

    if suffix == ".parquet":
        df = pd.read_parquet(file_path, engine="pyarrow", columns=columns)
        if nrows is None:
            return df
        if random_sample and len(df) > nrows:
            return df.sample(n=nrows, random_state=42)
        return df.head(nrows)

    raise ValueError(f"Unsupported file format: {suffix}")
