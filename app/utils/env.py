from __future__ import annotations

import os


def _get_env_value(name: str) -> str | None:
    raw = (os.getenv(name) or "").strip()
    if raw:
        return raw
    return None


def _get_int_env(
    name: str,
    *,
    default: int,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    raw = _get_env_value(name)
    if raw is None:
        return default

    try:
        value = int(raw)
    except ValueError:
        return default

    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


def get_data_dir_override() -> str | None:
    return _get_env_value("INSIGHT_HUB_DATA_DIR")


def get_application_id_column_override() -> str | None:
    return _get_env_value("INSIGHT_HUB_APPLICATION_ID_COLUMN")


def get_max_unique_values() -> int:
    return _get_int_env(
        "INSIGHT_HUB_MAX_UNIQUE_VALUES",
        default=100,
        minimum=0,
        maximum=5000,
    )


def get_max_insight_dimensions() -> int:
    return _get_int_env(
        "INSIGHT_HUB_MAX_INSIGHT_DIMENSIONS",
        default=8,
        minimum=2,
        maximum=12,
    )


def get_max_cola_m1_causes() -> int:
    return _get_int_env(
        "INSIGHT_HUB_MAX_COLA_M1_CAUSES",
        default=12,
        minimum=1,
        maximum=30,
    )


def get_max_split_groups() -> int:
    return _get_int_env(
        "INSIGHT_HUB_MAX_SPLIT_GROUPS",
        default=50,
        minimum=1,
    )
