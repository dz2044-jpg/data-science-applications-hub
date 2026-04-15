from __future__ import annotations

from pathlib import Path

import pytest

from app.retrieve.datasets import list_csv_datasets, read_csv_dataset_bytes


def test_list_csv_datasets_filters_and_sorts(tmp_path: Path) -> None:
    (tmp_path / "b.csv").write_text("date,deaths\n2025-01-01,1\n", encoding="utf-8")
    (tmp_path / "a.csv").write_text("date,deaths\n2025-01-01,1\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")

    assert list_csv_datasets(data_dir=tmp_path) == ["a.csv", "b.csv"]


def test_read_csv_dataset_bytes_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        read_csv_dataset_bytes(data_dir=tmp_path, dataset_name="../secret.csv")


def test_read_csv_dataset_bytes_requires_csv_extension(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        read_csv_dataset_bytes(data_dir=tmp_path, dataset_name="data.txt")

