from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.models.dataset_config import ModuleId, PerformanceType
from app.service.dataset_config import get_config_file_path
from app.service.storage import normalize_stored_file_path


def _build_saved_config_payload(
    *, config_id: str, file_path: str
) -> dict[str, object]:
    return {
        "id": config_id,
        "dataset_name": "configured-ae",
        "performance_type": PerformanceType.MORTALITY_AE.value,
        "file_path": file_path,
        "module_id": ModuleId.MORTALITY_AE.value,
        "module_config": {
            "policy_number_column": "application_number",
            "face_amount_column": None,
            "mac_column": "MAC",
            "mec_column": "MEC",
            "man_column": "MAN",
            "men_column": "MEN",
            "moc_column": "MOC",
            "cola_m1_column": None,
        },
        "created_date": datetime(2025, 1, 1).isoformat(),
    }


def _write_saved_config_tree(
    *,
    storage_root: Path,
    config_id: str,
    stored_file_path: str,
    filename: str = "saved.csv",
) -> None:
    file_path = storage_root / "files" / config_id / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        "application_number,MEC,MAC,MAN,MEN,MOC,age\n"
        "A1,1,1,100,100,1,30\n"
        "A2,1,2,200,100,1,50\n",
        encoding="utf-8",
    )
    (storage_root / "dataset_configs.json").write_text(
        json.dumps(
            [
                _build_saved_config_payload(
                    config_id=config_id,
                    file_path=stored_file_path,
                )
            ],
            indent=2,
        ),
        encoding="utf-8",
    )


def test_startup_creates_canonical_storage_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))

    with TestClient(create_app()):
        pass

    assert (tmp_path / ".insight-hub").is_dir()


def test_startup_migrates_legacy_storage_and_normalizes_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    legacy_root = tmp_path / ".aemonitor"
    config_id = "legacy-config"
    legacy_file = legacy_root / "files" / config_id / "saved.csv"
    _write_saved_config_tree(
        storage_root=legacy_root,
        config_id=config_id,
        stored_file_path=str(legacy_file),
    )

    with TestClient(create_app()) as client:
        response = client.get(f"/api/dataset-configs/{config_id}/schema")
        assert response.status_code == 200

    canonical_root = tmp_path / ".insight-hub"
    assert canonical_root.is_dir()
    assert not legacy_root.exists()
    assert (canonical_root / "files" / config_id / "saved.csv").exists()

    payload = json.loads(
        (canonical_root / "dataset_configs.json").read_text(encoding="utf-8")
    )
    assert payload[0]["file_path"] == "saved.csv"


def test_copy_based_migration_warns_when_legacy_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import app.service.storage as storage_service

    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    legacy_root = tmp_path / ".aemonitor"
    config_id = "copy-migration"
    _write_saved_config_tree(
        storage_root=legacy_root,
        config_id=config_id,
        stored_file_path=".aemonitor/files/copy-migration/saved.csv",
    )

    original_rename = Path.rename
    original_rmtree = shutil.rmtree

    def fake_rename(self: Path, target: str | Path) -> Path:
        if self == legacy_root:
            raise OSError("cross-device link")
        return original_rename(self, target)

    def fake_rmtree(path: str | Path, *args: object, **kwargs: object) -> None:
        if Path(path) == legacy_root:
            raise OSError("locked by another process")
        original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(Path, "rename", fake_rename)
    monkeypatch.setattr(storage_service.shutil, "rmtree", fake_rmtree)

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200

    captured = capsys.readouterr()
    assert "could not remove legacy directory" in captured.err
    assert (tmp_path / ".insight-hub" / "dataset_configs.json").exists()
    assert legacy_root.exists()


def test_startup_prefers_existing_canonical_storage_when_both_dirs_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    legacy_root = tmp_path / ".aemonitor"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id="canonical-config",
        stored_file_path=".insight-hub/files/canonical-config/saved.csv",
    )
    _write_saved_config_tree(
        storage_root=legacy_root,
        config_id="legacy-config",
        stored_file_path=".aemonitor/files/legacy-config/saved.csv",
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/dataset-configs")
        assert response.status_code == 200

    config_ids = [item["id"] for item in response.json()["configs"]]
    assert config_ids == ["canonical-config"]
    assert legacy_root.exists()


def test_normalize_stored_file_path_handles_legacy_and_canonical_variants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    config_id = "path-config"

    legacy_absolute = str(
        tmp_path / ".aemonitor" / "files" / config_id / "legacy.csv"
    )
    outside_path = str(tmp_path / "outside.csv")

    assert normalize_stored_file_path(config_id, "plain.csv") == (
        "plain.csv",
        False,
    )
    assert normalize_stored_file_path(config_id, legacy_absolute) == (
        "legacy.csv",
        True,
    )
    assert normalize_stored_file_path(
        config_id,
        ".aemonitor/files/path-config/legacy.csv",
    ) == ("legacy.csv", True)
    assert normalize_stored_file_path(
        config_id,
        ".insight-hub/files/path-config/current.csv",
    ) == ("current.csv", True)
    assert normalize_stored_file_path(config_id, outside_path) == (
        outside_path,
        False,
    )


def test_get_config_file_path_resolves_through_storage_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    canonical_root = tmp_path / ".insight-hub"
    config_id = "resolved-config"
    _write_saved_config_tree(
        storage_root=canonical_root,
        config_id=config_id,
        stored_file_path=".insight-hub/files/resolved-config/saved.csv",
    )

    file_path = get_config_file_path(config_id)

    assert file_path == canonical_root / "files" / config_id / "saved.csv"
