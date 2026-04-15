from __future__ import annotations

import os
from pathlib import Path


def get_data_dir() -> Path:
    env = (os.getenv("AEMONITOR_DATA_DIR") or "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]

