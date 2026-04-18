from __future__ import annotations

import pytest

from app.modules.mortality_ae.models.ae import (
    ApiAePolynomialFitParameters,
    ApiAeUnivariateParameters,
    ApiAeXVariableCategorical,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.modules.mortality_ae.service.ae_univariate import (
    perform_ae_univariate_from_upload,
)


def test_service_returns_split_results_when_split_variable_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number")

    result = perform_ae_univariate_from_upload(
        file_bytes=(
            b"application_number,MEC,MAC,age,sex\n"
            b"a1,10,9,20,M\n"
            b"a2,10,11,30,F\n"
            b"a3,10,10,40,M\n"
        ),
        filename="data.csv",
        params=ApiAeUnivariateParameters(
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
