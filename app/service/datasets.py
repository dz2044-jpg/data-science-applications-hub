from __future__ import annotations

from app.models.datasets import ApiDatasetInfo, ApiListDatasetsResults
from app.retrieve.datasets import list_datasets as retrieve_list_datasets
from app.utils.paths import get_data_dir


def list_datasets() -> ApiListDatasetsResults:
    """List all datasets with supported file formats (CSV, Excel, Parquet)."""
    data_dir = get_data_dir()
    names = retrieve_list_datasets(data_dir=data_dir)
    return ApiListDatasetsResults(datasets=[ApiDatasetInfo(name=n) for n in names])
