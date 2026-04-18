from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from app.utils.env import (
    get_application_id_column_override,
    get_max_cola_m1_causes,
    get_max_insight_dimensions,
    get_max_split_groups,
    get_max_unique_values,
)
from app.utils.paths import get_data_dir


@pytest.mark.parametrize(
    ("name", "getter", "value", "expected"),
    [
        ("INSIGHT_HUB_MAX_UNIQUE_VALUES", get_max_unique_values, "111", 111),
        ("INSIGHT_HUB_MAX_INSIGHT_DIMENSIONS", get_max_insight_dimensions, "9", 9),
        ("INSIGHT_HUB_MAX_COLA_M1_CAUSES", get_max_cola_m1_causes, "15", 15),
        ("INSIGHT_HUB_MAX_SPLIT_GROUPS", get_max_split_groups, "41", 41),
    ],
)
def test_numeric_env_values_are_read(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    getter: Callable[[], int],
    value: str,
    expected: int,
) -> None:
    monkeypatch.setenv(name, value)
    assert getter() == expected


def test_insight_hub_data_dir_override_is_used(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    override = tmp_path / "preferred"
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(override))
    assert get_data_dir() == override.resolve()


def test_insight_hub_application_id_override_is_used(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number")
    assert get_application_id_column_override() == "application_number"
