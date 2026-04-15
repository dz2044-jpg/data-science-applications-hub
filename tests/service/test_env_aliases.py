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
    (
        "new_name",
        "legacy_name",
        "getter",
        "new_value",
        "legacy_value",
        "expected",
    ),
    [
        (
            "INSIGHT_HUB_MAX_UNIQUE_VALUES",
            "AEMONITOR_MAX_UNIQUE_VALUES",
            get_max_unique_values,
            "111",
            "17",
            111,
        ),
        (
            "INSIGHT_HUB_MAX_INSIGHT_DIMENSIONS",
            "AEMONITOR_MAX_INSIGHT_DIMENSIONS",
            get_max_insight_dimensions,
            "9",
            "4",
            9,
        ),
        (
            "INSIGHT_HUB_MAX_COLA_M1_CAUSES",
            "AEMONITOR_MAX_COLA_M1_CAUSES",
            get_max_cola_m1_causes,
            "15",
            "3",
            15,
        ),
        (
            "INSIGHT_HUB_MAX_SPLIT_GROUPS",
            "AEMONITOR_MAX_SPLIT_GROUPS",
            get_max_split_groups,
            "41",
            "7",
            41,
        ),
    ],
)
def test_new_numeric_env_aliases_take_precedence(
    monkeypatch: pytest.MonkeyPatch,
    new_name: str,
    legacy_name: str,
    getter: Callable[[], int],
    new_value: str,
    legacy_value: str,
    expected: int,
) -> None:
    monkeypatch.setenv(new_name, new_value)
    monkeypatch.setenv(legacy_name, legacy_value)

    assert getter() == expected


@pytest.mark.parametrize(
    ("legacy_name", "getter", "legacy_value", "expected"),
    [
        ("AEMONITOR_MAX_UNIQUE_VALUES", get_max_unique_values, "19", 19),
        (
            "AEMONITOR_MAX_INSIGHT_DIMENSIONS",
            get_max_insight_dimensions,
            "6",
            6,
        ),
        ("AEMONITOR_MAX_COLA_M1_CAUSES", get_max_cola_m1_causes, "13", 13),
        ("AEMONITOR_MAX_SPLIT_GROUPS", get_max_split_groups, "23", 23),
    ],
)
def test_legacy_numeric_env_aliases_still_work(
    monkeypatch: pytest.MonkeyPatch,
    legacy_name: str,
    getter: Callable[[], int],
    legacy_value: str,
    expected: int,
) -> None:
    monkeypatch.setenv(legacy_name, legacy_value)

    assert getter() == expected


def test_insight_hub_data_dir_takes_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    preferred = tmp_path / "preferred"
    fallback = tmp_path / "fallback"
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(preferred))
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(fallback))

    assert get_data_dir() == preferred.resolve()


def test_legacy_data_dir_alias_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fallback = tmp_path / "fallback"
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(fallback))

    assert get_data_dir() == fallback.resolve()


def test_insight_hub_application_id_alias_takes_precedence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "new_app_id")
    monkeypatch.setenv("AEMONITOR_APPLICATION_ID_COLUMN", "legacy_app_id")

    assert get_application_id_column_override() == "new_app_id"


def test_legacy_application_id_alias_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AEMONITOR_APPLICATION_ID_COLUMN", "legacy_app_id")

    assert get_application_id_column_override() == "legacy_app_id"
