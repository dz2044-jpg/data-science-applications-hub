from __future__ import annotations

from pathlib import Path

import pytest

from app.models.ae import (
    ApiAePolynomialFitParameters,
    ApiAeUnivariateParameters,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.service.ae_univariate import perform_ae_univariate


def test_service_ae_univariate_uses_env_application_id_column(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "data.csv").write_text(
        "application_number,MEC,MAC,age\n"
        "a1,10,9,10\n"
        "a2,10,11,20\n",
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
            poly_fit=ApiAePolynomialFitParameters(degree=1, weighted=True),
        )
    )
    assert result.rows[-1].variable_group == "Total"
    assert result.rows[-1].sample_size == 2
    assert result.poly_fit is not None
    assert result.poly_fit.degree == 1
