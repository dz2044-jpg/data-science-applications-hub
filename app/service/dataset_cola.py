from __future__ import annotations

import pandas as pd

from app.models.datasets import ApiDatasetColaResults
from app.retrieve.datasets import read_dataset_bytes
from app.utils.env import get_max_unique_values
from app.utils.paths import get_data_dir

COLA_M1_COLUMN = "COLA_M1"
COLA_M2_COLUMN = "COLA_M2"


def _max_unique_values() -> int:
    return max(1, get_max_unique_values())


def _read_dataframe_columns(*, file_bytes: bytes, filename: str, columns: list[str]) -> pd.DataFrame:
    """Read specific columns from a dataset file based on extension."""
    from pathlib import Path
    suffix = Path(filename).suffix.lower()
    
    if suffix == ".csv":
        return pd.read_csv(
            pd.io.common.BytesIO(file_bytes),
            usecols=columns,
        )
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        return df[columns]
    elif suffix == ".parquet":
        # Parquet can efficiently read specific columns
        return pd.read_parquet(
            pd.io.common.BytesIO(file_bytes),
            columns=columns,
            engine='pyarrow',
        )
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def get_dataset_cola(*, dataset_name: str) -> ApiDatasetColaResults:
    file_bytes = read_dataset_bytes(
        data_dir=get_data_dir(),
        dataset_name=dataset_name,
    )
    max_uniques = _max_unique_values()

    df = _read_dataframe_columns(
        file_bytes=file_bytes,
        filename=dataset_name,
        columns=[COLA_M1_COLUMN, COLA_M2_COLUMN],
    )
    if COLA_M1_COLUMN not in df.columns or COLA_M2_COLUMN not in df.columns:
        raise ValueError(f"Missing required columns: {COLA_M1_COLUMN}, {COLA_M2_COLUMN}")

    m1 = df[COLA_M1_COLUMN].fillna("").astype(str).str.strip()
    m2 = df[COLA_M2_COLUMN].fillna("").astype(str).str.strip()

    # Filter to rows with a COLA_M1 value.
    mask = m1 != ""
    if not mask.any():
        return ApiDatasetColaResults(
            dataset_name=dataset_name,
            cola_m1_column=COLA_M1_COLUMN,
            cola_m2_column=COLA_M2_COLUMN,
            cola_m2_by_m1={},
            max_unique_values=max_uniques,
        )

    df2 = pd.DataFrame({"m1": m1[mask], "m2": m2[mask]})

    cola_m2_by_m1: dict[str, list[str]] = {}
    for key, group in df2.groupby("m1", sort=True):
        if not isinstance(key, str):
            continue
        values = (
            group["m2"]
            .loc[group["m2"] != ""]
            .drop_duplicates()
            .sort_values(kind="stable")
            .tolist()
        )
        if len(values) > max_uniques:
            values = values[:max_uniques]
        cola_m2_by_m1[str(key)] = [str(v) for v in values]

    # Cap number of parent categories as well (for large datasets).
    if len(cola_m2_by_m1) > max_uniques:
        keys = sorted(cola_m2_by_m1.keys(), key=lambda s: s.lower())
        cola_m2_by_m1 = {k: cola_m2_by_m1[k] for k in keys[:max_uniques]}

    return ApiDatasetColaResults(
        dataset_name=dataset_name,
        cola_m1_column=COLA_M1_COLUMN,
        cola_m2_column=COLA_M2_COLUMN,
        cola_m2_by_m1=cola_m2_by_m1,
        max_unique_values=max_uniques,
    )
