from __future__ import annotations

from fastapi.testclient import TestClient

from app import create_app
from app.core.service.schema_profile import get_core_schema_from_bytes


def test_get_core_schema_from_bytes_profiles_generic_columns() -> None:
    csv_bytes = (
        b"MEC,MAC,sex,age,as_of\n"
        b"10,9,M,40,2020-01-01\n"
        b"10,12,F,41,2020-01-03\n"
        b"10,8,M,42,2020-01-02\n"
    )

    schema = get_core_schema_from_bytes(file_bytes=csv_bytes, filename="demo.csv")

    assert schema.dataset_name == "demo.csv"
    assert schema.max_unique_values >= 0
    columns = {column.name: column for column in schema.columns}
    assert columns["sex"].kind == "categorical"
    assert columns["age"].kind == "categorical"
    assert columns["as_of"].kind == "date"


def test_core_upload_schema_endpoint_returns_generic_shape() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/core/upload-schema",
            files={"file": ("demo.csv", b"MEC,MAC,sex\n10,9,M\n10,8,F\n", "text/csv")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_name"] == "demo.csv"
    assert "columns" in body
    assert "max_unique_values" in body
    assert "column_suggestions" not in body
    assert "mec_column" not in body
    assert "mac_column" not in body
