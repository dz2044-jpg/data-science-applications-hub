from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.models.dataset_config import (
    ApiColumnMapping,
    ApiCreateDatasetConfigRequest,
    PerformanceType,
)
from app.service.dataset_config import (
    create_dataset_config,
    get_config_file_path,
    get_dataset_config,
    save_uploaded_file,
)


def test_saved_configs_persist_across_app_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(tmp_path))
    (tmp_path / "root-dataset.csv").write_text("x,y\n1,2\n", encoding="utf-8")

    request = ApiCreateDatasetConfigRequest(
        dataset_name="persisted-config",
        performance_type=PerformanceType.MORTALITY_AE,
        file_path="persisted.csv",
        column_mapping=ApiColumnMapping(
            policy_number_column="policy_number",
            face_amount_column=None,
            mac_column="MAC",
            mec_column="MEC",
            man_column="MAN",
            men_column="MEN",
            moc_column="MOC",
            cola_m1_column=None,
        ),
    )
    config = create_dataset_config(request)
    save_uploaded_file(
        config.id,
        BytesIO(
            b"policy_number,MEC,MAC,MAN,MEN,MOC,sex\n"
            b"P1,1,1,100,100,1,F\n"
        ),
        "persisted.csv",
    )

    with TestClient(create_app()) as client:
        response = client.get("/api/datasets")
        assert response.status_code == 200
        assert response.json() == {"datasets": [{"name": "root-dataset.csv"}]}

    persisted = get_dataset_config(config.id)
    assert persisted is not None
    file_path = get_config_file_path(config.id)
    assert file_path is not None
    assert file_path.exists()
