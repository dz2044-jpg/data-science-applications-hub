from __future__ import annotations

import pytest

from app.modules.mortality_ae.service.dataset_schema import (
    get_dataset_schema_from_bytes,
)


def test_get_dataset_schema_infers_kinds_and_uniques(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_MAX_UNIQUE_VALUES", "10")

    schema = get_dataset_schema_from_bytes(
        file_bytes=(
            b"MEC,MAC,sex,age,as_of,flag\n"
            b"10,9,M,40,2020-01-01,0\n"
            b"10,12,F,41,2020-01-03,1\n"
            b"10,8,M,42,2020-01-02,0\n"
        ),
        filename="demo.csv",
    )
    assert schema.dataset_name == "demo.csv"
    assert schema.mec_column == "MEC"
    assert schema.mac_column == "MAC"

    cols = {c.name: c for c in schema.columns}
    assert cols["MEC"].kind == "numeric"
    assert cols["MAC"].kind == "numeric"
    assert cols["sex"].kind == "categorical"
    assert cols["sex"].unique_count == 2
    assert set(cols["sex"].unique_values or []) == {"M", "F"}
    assert cols["age"].kind == "categorical"
    assert cols["age"].unique_count == 3
    assert set(cols["age"].unique_values or []) == {"40", "41", "42"}
    assert cols["as_of"].kind == "date"
    assert cols["as_of"].date_min is not None
    assert cols["as_of"].date_max is not None
    assert cols["flag"].kind == "categorical"


def test_get_dataset_schema_requires_mec_mac(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValueError):
        get_dataset_schema_from_bytes(file_bytes=b"x,y\n1,2\n", filename="bad.csv")
