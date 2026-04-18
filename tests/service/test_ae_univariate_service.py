from __future__ import annotations

import pytest

from app.modules.mortality_ae.models.ae import (
    ApiAePolynomialFitParameters,
    ApiAeUnivariateParameters,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.modules.mortality_ae.service.ae_univariate import (
    perform_ae_univariate_from_upload,
)


def test_service_ae_univariate_uses_env_application_id_column(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number")

    result = perform_ae_univariate_from_upload(
        file_bytes=(
            b"application_number,MEC,MAC,age\n"
            b"a1,10,9,10\n"
            b"a2,10,11,20\n"
        ),
        filename="data.csv",
        params=ApiAeUnivariateParameters(
            x_variable=ApiAeXVariableNumeric(
                name="age",
                binning=ApiNumericBinning.UNIFORM,
                bin_count=2,
            ),
            poly_fit=ApiAePolynomialFitParameters(degree=1, weighted=True),
        )
    )
    assert result.rows[-1].variable_group == "Total"
    assert result.rows[-1].sample_size == 2
    assert result.poly_fit is not None
    assert result.poly_fit.degree == 1
