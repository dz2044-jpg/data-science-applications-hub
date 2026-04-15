from __future__ import annotations

from io import BytesIO
from pathlib import Path

from app.models.ae import (
    ApiAeUnivariateFromConfigParameters,
    ApiAeXVariableNumeric,
    ApiNumericBinning,
)
from app.models.dataset_config import (
    ApiColumnMapping,
    ApiCreateDatasetConfigRequest,
    PerformanceType,
)
from app.service.ae_univariate import perform_ae_univariate_from_config
from app.service.dataset_config import create_dataset_config, save_uploaded_file


def test_perform_ae_univariate_from_config_uses_saved_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("AEMONITOR_DATA_DIR", str(tmp_path))

    request = ApiCreateDatasetConfigRequest(
        dataset_name="configured-ae",
        performance_type=PerformanceType.MORTALITY_AE,
        file_path="ae.csv",
        column_mapping=ApiColumnMapping(
            policy_number_column="application_number",
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
            b"application_number,MEC,MAC,MAN,MEN,MOC,age,sex\n"
            b"A1,1,1,100,100,1,30,F\n"
            b"A2,1,2,200,100,1,50,M\n"
            b"A3,1,0,0,100,1,70,M\n"
        ),
        "ae.csv",
    )

    result = perform_ae_univariate_from_config(
        params=ApiAeUnivariateFromConfigParameters(
            config_id=config.id,
            x_variable=ApiAeXVariableNumeric(
                name="age",
                binning=ApiNumericBinning.UNIFORM,
                bin_count=3,
            ),
        )
    )

    assert result.rows
    assert result.rows[-1].variable_group == "Total"
    assert result.rows[-1].sample_size == 3
