from __future__ import annotations

from pathlib import Path


# Supported file extensions
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}


def list_csv_datasets(*, data_dir: Path) -> list[str]:
    """List CSV datasets (deprecated - use list_datasets instead)."""
    return list_datasets(data_dir=data_dir, extensions={".csv"})


def list_datasets(
    *, data_dir: Path, extensions: set[str] | None = None
) -> list[str]:
    """List all datasets with supported file extensions.
    
    Args:
        data_dir: Directory containing dataset files
        extensions: Set of file extensions to filter by (default: all supported)
    
    Returns:
        Sorted list of dataset filenames
    """
    if not data_dir.exists():
        return []
    if not data_dir.is_dir():
        raise ValueError("Data directory is not a directory")

    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS

    names: list[str] = []
    for path in data_dir.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() not in extensions:
            continue
        names.append(path.name)
    return sorted(names, key=lambda s: s.lower())


def read_csv_dataset_bytes(*, data_dir: Path, dataset_name: str) -> bytes:
    """Read CSV dataset bytes (deprecated - use read_dataset_bytes instead)."""
    return read_dataset_bytes(data_dir=data_dir, dataset_name=dataset_name)


def read_dataset_bytes(*, data_dir: Path, dataset_name: str) -> bytes:
    """Read dataset file bytes for any supported format.
    
    Args:
        data_dir: Directory containing dataset files
        dataset_name: Name of the dataset file
    
    Returns:
        Raw bytes of the dataset file
    
    Raises:
        ValueError: If dataset name is invalid or file not found
    """
    name = dataset_name.strip()
    if not name:
        raise ValueError("dataset_name is required")
    if name != Path(name).name:
        raise ValueError("Invalid dataset_name")
    
    # Check if file has a supported extension
    suffix = Path(name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file extension: {suffix}. "
            f"Supported extensions: {supported_list}"
        )

    path = (data_dir / name).resolve()
    try:
        path.relative_to(data_dir.resolve())
    except ValueError as exc:
        raise ValueError("Invalid dataset_name") from exc

    if not path.exists() or not path.is_file():
        raise ValueError("Dataset not found")

    return path.read_bytes()
