from __future__ import annotations

from pathlib import Path

from app.utils.env import get_data_dir_override


def get_data_dir() -> Path:
    env = get_data_dir_override()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]
