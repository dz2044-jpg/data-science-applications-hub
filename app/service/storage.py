from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from threading import Lock

from app.utils.paths import get_data_dir

_CANONICAL_STORAGE_DIR = ".insight-hub"
_LEGACY_STORAGE_DIR = ".aemonitor"
_MIGRATING_STORAGE_DIR = ".insight-hub.migrating"
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
    legacy_root = _legacy_storage_root(data_dir)
    temp_root = _temp_storage_root(data_dir)

    for path in (canonical_root, legacy_root, temp_root):
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"Storage path is not a directory: {path}")

    if temp_root.exists() and not canonical_root.exists():
        if not legacy_root.exists():
            raise RuntimeError(
                f"Found incomplete storage migration at {temp_root}"
            )
        shutil.rmtree(temp_root)

    if canonical_root.exists():
        active_root = canonical_root
    elif legacy_root.exists():
        active_root = _migrate_legacy_storage(
            legacy_root=legacy_root,
            canonical_root=canonical_root,
            temp_root=temp_root,
        )
    else:
        canonical_root.mkdir(parents=True, exist_ok=True)
        active_root = canonical_root

    _normalize_dataset_config_paths(active_root / _CONFIGS_FILE)
    return active_root


def _migrate_legacy_storage(
    *,
    legacy_root: Path,
    canonical_root: Path,
    temp_root: Path,
) -> Path:
    try:
        legacy_root.rename(canonical_root)
        return canonical_root
    except OSError:
        if temp_root.exists():
            shutil.rmtree(temp_root)

        shutil.copytree(legacy_root, temp_root)
        _verify_tree_copy(legacy_root, temp_root)
        temp_root.rename(canonical_root)
        try:
            shutil.rmtree(legacy_root)
        except OSError as exc:
            print(
                "Warning: migrated storage to "
                f"{canonical_root} but could not remove legacy directory "
                f"{legacy_root}: {exc}",
                file=sys.stderr,
            )
        return canonical_root


def _verify_tree_copy(source_root: Path, copied_root: Path) -> None:
    if _snapshot_tree(source_root) != _snapshot_tree(copied_root):
        raise RuntimeError(
            "Copied storage tree does not match source: "
            f"{source_root} -> {copied_root}"
        )


def _snapshot_tree(root: Path) -> dict[str, tuple[str, int | None]]:
    snapshot: dict[str, tuple[str, int | None]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_dir():
            snapshot[relative] = ("dir", None)
        elif path.is_file():
            snapshot[relative] = ("file", path.stat().st_size)
    return snapshot


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

    prefixes = (
        f"{_CANONICAL_STORAGE_DIR}/{_FILES_DIR}/{config_id}/",
        f"{_LEGACY_STORAGE_DIR}/{_FILES_DIR}/{config_id}/",
    )
    for prefix in prefixes:
        if normalized_text.startswith(prefix):
            remainder = normalized_text[len(prefix) :]
            return remainder or None
    return None


def _managed_config_dirs(config_id: str) -> tuple[Path, Path]:
    data_dir = get_data_dir()
    return (
        _storage_root(data_dir) / _FILES_DIR / config_id,
        _legacy_storage_root(data_dir) / _FILES_DIR / config_id,
    )


def _storage_root(data_dir: Path) -> Path:
    return data_dir / _CANONICAL_STORAGE_DIR


def _legacy_storage_root(data_dir: Path) -> Path:
    return data_dir / _LEGACY_STORAGE_DIR


def _temp_storage_root(data_dir: Path) -> Path:
    return data_dir / _MIGRATING_STORAGE_DIR
