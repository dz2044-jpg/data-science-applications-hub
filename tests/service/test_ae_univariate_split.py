from __future__ import annotations

from pathlib import Path

import pytest

from app.models.ae import (
    ApiAePolynomialFitParameters,
    ApiAeUnivariateParameters,
    ApiAeXVariableCategorical,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.service.ae_univariate import perform_ae_univariate


def test_service_returns_split_results_when_split_variable_provided(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "data.csv").write_text(
        "application_number,MEC,MAC,age,sex\n"
        "a1,10,9,20,M\n"
        "a2,10,11,30,F\n"
        "a3,10,10,40,M\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("INSIGHT_HUB_DATA_DIR", str(tmp_path))
    monkeypatch.setenv(
        "INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number"
    )

    result = perform_ae_univariate(
        params=ApiAeUnivariateParameters(
            dataset_name="data.csv",
            x_variable=ApiAeXVariableNumeric(
                name="age",
                binning=ApiNumericBinning.UNIFORM,
                bin_count=2,
            ),
            split_variable=ApiAeXVariableCategorical(
                name="sex",
                grouping="all_unique",
            ),
            poly_fit=ApiAePolynomialFitParameters(degree=1, weighted=False),
        )
    )

    assert result.rows
    assert result.poly_fit is not None
    assert result.split_results is not None
    assert {s.split_group for s in result.split_results} == {"F", "M"}
    assert all(
        s.rows and s.rows[-1].variable_group == "Total"
        for s in result.split_results
    )
    by_group = {s.split_group: s for s in (result.split_results or [])}
    assert by_group["F"].poly_fit is None  # only one point in this split
    assert by_group["M"].poly_fit is not None  # two points in this split
