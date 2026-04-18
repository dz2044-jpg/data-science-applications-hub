from __future__ import annotations

import pytest

from app.modules.mortality_ae.models.ae import (
    ApiAeExclusions,
    ApiAeUnivariateParameters,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.modules.mortality_ae.service.ae_univariate import (
    perform_ae_univariate_from_upload,
)


def test_excluding_cola_m1_excludes_entire_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number")

    res = perform_ae_univariate_from_upload(
        file_bytes=(
            b"application_number,MEC,MAC,age,COLA_M1,COLA_M2\n"
            b"a1,10,1,20,ACC,ACC1\n"
            b"a1,10,0,20,OTHER,OTH1\n"
            b"a2,10,1,30,ACC,ACC2\n"
            b"a3,10,1,40,CANC,C2\n"
        ),
        filename="data.csv",
        params=ApiAeUnivariateParameters(
            x_variable=ApiAeXVariableNumeric(
                name="age",
                binning=ApiNumericBinning.UNIFORM,
                bin_count=2,
            ),
            exclusions=ApiAeExclusions(exclude_cola_m1=["ACC"]),
        )
    )

    assert res.rows
    assert res.rows[-1].variable_group == "Total"
    assert res.rows[-1].sample_size == 1  # only a3 remains


def test_excluding_cola_m2_within_m1_excludes_only_matching_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INSIGHT_HUB_APPLICATION_ID_COLUMN", "application_number")

    res = perform_ae_univariate_from_upload(
        file_bytes=(
            b"application_number,MEC,MAC,age,COLA_M1,COLA_M2\n"
            b"a1,10,1,20,ACC,ACC1\n"
            b"a2,10,1,30,ACC,ACC2\n"
            b"a3,10,1,40,CANC,C2\n"
        ),
        filename="data.csv",
        params=ApiAeUnivariateParameters(
            x_variable=ApiAeXVariableNumeric(
                name="age",
                binning=ApiNumericBinning.UNIFORM,
                bin_count=2,
            ),
            exclusions=ApiAeExclusions(exclude_cola_m2_by_m1={"ACC": ["ACC2"]}),
        )
    )

    assert res.rows
    assert res.rows[-1].variable_group == "Total"
    assert res.rows[-1].sample_size == 2  # a1 + a3 remain
