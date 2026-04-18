from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from app.utils.paths import get_data_dir

_CANONICAL_STORAGE_DIR = ".insight-hub"
_FILES_DIR = "files"
_CONFIGS_FILE = "dataset_configs.json"
_BOOTSTRAP_LOCK = Lock()


def bootstrap_storage() -> Path:
    data_dir = get_data_dir()
    with _BOOTSTRAP_LOCK:
        return _bootstrap_storage_locked(data_dir)


def get_storage_root() -> Path:
    return bootstrap_storage()


def get_configs_file() -> Path:
    return get_storage_root() / _CONFIGS_FILE


def get_files_dir(*, create: bool = False) -> Path:
    files_dir = get_storage_root() / _FILES_DIR
    if create:
        files_dir.mkdir(parents=True, exist_ok=True)
    return files_dir


def get_config_file_dir(config_id: str, *, create: bool = False) -> Path:
    config_dir = get_files_dir(create=create) / config_id
    if create:
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def normalize_stored_file_path(
    config_id: str, stored_file_path: str
) -> tuple[str, bool]:
    if not stored_file_path:
        return stored_file_path, False

    absolute = _normalize_absolute_managed_path(config_id, stored_file_path)
    if absolute is not None:
        return absolute, absolute != stored_file_path

    relative = _normalize_storage_relative_path(config_id, stored_file_path)
    if relative is not None:
        return relative, relative != stored_file_path

    return stored_file_path, False


def get_dataset_file_path(config_id: str, stored_file_path: str) -> Path | None:
    normalized, _ = normalize_stored_file_path(config_id, stored_file_path)
    if not normalized:
        return None

    relative_path = Path(normalized)
    if relative_path == Path(".") or relative_path.is_absolute():
        return None

    config_dir = get_config_file_dir(config_id, create=False)
    resolved_path = (config_dir / relative_path).resolve(strict=False)
    resolved_dir = config_dir.resolve(strict=False)
    try:
        resolved_path.relative_to(resolved_dir)
    except ValueError:
        return None
    return resolved_path


def _bootstrap_storage_locked(data_dir: Path) -> Path:
    canonical_root = _storage_root(data_dir)

    if canonical_root.exists():
        if not canonical_root.is_dir():
            raise RuntimeError(f"Storage path is not a directory: {canonical_root}")
        active_root = canonical_root
    else:
        canonical_root.mkdir(parents=True, exist_ok=True)
        active_root = canonical_root

    _normalize_dataset_config_paths(active_root / _CONFIGS_FILE)
    return active_root


def _normalize_dataset_config_paths(configs_file: Path) -> None:
    if not configs_file.exists():
        return

    try:
        with configs_file.open(encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return

    if not isinstance(payload, list):
        return

    changed = False
    for item in payload:
        if not isinstance(item, dict):
            continue
        config_id = item.get("id")
        file_path = item.get("file_path")
        if not isinstance(config_id, str) or not isinstance(file_path, str):
            continue

        normalized, was_changed = normalize_stored_file_path(
            config_id, file_path
        )
        if was_changed:
            item["file_path"] = normalized
            changed = True

    if not changed:
        return

    with configs_file.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def _normalize_absolute_managed_path(
    config_id: str, stored_file_path: str
) -> str | None:
    candidate = Path(stored_file_path).expanduser()
    if not candidate.is_absolute():
        return None

    resolved_candidate = candidate.resolve(strict=False)
    for base_dir in _managed_config_dirs(config_id):
        try:
            relative_path = resolved_candidate.relative_to(
                base_dir.resolve(strict=False)
            )
        except ValueError:
            continue

        if relative_path == Path("."):
            return None
        return relative_path.as_posix()
    return None


def _normalize_storage_relative_path(
    config_id: str, stored_file_path: str
) -> str | None:
    normalized_text = stored_file_path.replace("\\", "/")
    while normalized_text.startswith("./"):
        normalized_text = normalized_text[2:]

    prefixes = (f"{_CANONICAL_STORAGE_DIR}/{_FILES_DIR}/{config_id}/",)
    for prefix in prefixes:
        if normalized_text.startswith(prefix):
            remainder = normalized_text[len(prefix) :]
            return remainder or None
    return None


def _managed_config_dirs(config_id: str) -> tuple[Path]:
    data_dir = get_data_dir()
    return (_storage_root(data_dir) / _FILES_DIR / config_id,)


def _storage_root(data_dir: Path) -> Path:
    return data_dir / _CANONICAL_STORAGE_DIR
