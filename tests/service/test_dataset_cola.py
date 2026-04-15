from __future__ import annotations

from pathlib import Path

import pytest

from app.service.dataset_cola import get_dataset_cola


def test_get_dataset_cola_returns_m2_by_m1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "demo.csv").write_text(
        "MEC,MAC,COLA_M1,COLA_M2\n"
        "10,9,ACC,ACC1\n"
        "10,9,ACC,ACC2\n"
        "10,9,CANC,C1\n"
        "10,9,CANC,\n"
        "10,9,,\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("AEMONITOR_MAX_UNIQUE_VALUES", "10")

    res = get_dataset_cola(dataset_name="demo.csv")
    assert res.dataset_name == "demo.csv"
    assert set(res.cola_m2_by_m1.keys()) == {"ACC", "CANC"}
    assert set(res.cola_m2_by_m1["ACC"]) == {"ACC1", "ACC2"}
    assert res.cola_m2_by_m1["CANC"] == ["C1"]

