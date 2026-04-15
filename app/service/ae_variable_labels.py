from __future__ import annotations

import pandas as pd

from app.calc.ae_univariate import compute_group_labels_for_variable
from app.models.ae import ApiAeVariableLabelsParameters, ApiAeVariableLabelsResults
from app.retrieve.datasets import read_dataset_bytes
from app.utils.env import get_max_unique_values
from app.utils.paths import get_data_dir


def _max_unique_values() -> int:
    return get_max_unique_values()


def _read_dataframe_from_bytes(*, file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Read DataFrame from file bytes based on extension."""
    from pathlib import Path
    suffix = Path(filename).suffix.lower()
    
    if suffix == ".csv":
        return pd.read_csv(pd.io.common.BytesIO(file_bytes))
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(pd.io.common.BytesIO(file_bytes))
    elif suffix == ".parquet":
        return pd.read_parquet(pd.io.common.BytesIO(file_bytes), engine='pyarrow')
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def perform_ae_variable_labels(
    *, params: ApiAeVariableLabelsParameters
) -> ApiAeVariableLabelsResults:
    file_bytes = read_dataset_bytes(
        data_dir=get_data_dir(),
        dataset_name=params.dataset_name,
    )
    df = _read_dataframe_from_bytes(file_bytes=file_bytes, filename=params.dataset_name)

    if params.variable.name not in df.columns:
        raise ValueError(f"Missing required column: {params.variable.name}")

    _labels, order = compute_group_labels_for_variable(df=df, variable=params.variable)
    if (
        params.variable.kind == "categorical"
        and params.variable.grouping == "all_unique"
        and len(order) > _max_unique_values()
    ):
        raise ValueError(
            "Too many unique values for UI selection; reduce cardinality or increase "
            "INSIGHT_HUB_MAX_UNIQUE_VALUES"
        )
    return ApiAeVariableLabelsResults(labels=[str(x) for x in order])
