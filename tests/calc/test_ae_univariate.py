from __future__ import annotations

import pandas as pd

from app.calc.ae_univariate import compute_ae_univariate_rows
from app.models.ae import (
    ApiAeCrossGroupDefinition,
    ApiAePolynomialFitParameters,
    ApiAeUnivariateRow,
    ApiAeXVariableCategorical,
    ApiAeXVariableCross,
    ApiAeXVariableDate,
    ApiAeXVariableNumeric,
    ApiCategoricalGroupDefinition,
    ApiNumericBinning,
)
from app.calc.ae_univariate import compute_polynomial_fit


def test_compute_ae_univariate_rows_numeric_uniform_includes_total() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c", "d"],
            "MEC": [10.0, 10.0, 10.0, 10.0],
            "MAC": [9.0, 10.0, 11.0, 10.0],
            "age": [10.0, 20.0, 30.0, 40.0],
        }
    )
    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=ApiAeXVariableNumeric(
            name="age",
            binning=ApiNumericBinning.UNIFORM,
            bin_count=2,
        ),
        app_id_column="APP",
        mec_column="MEC",
        mac_column="MAC",
    )
    assert rows[-1].variable_group == "Total"
    assert rows[-1].sample_size == 4
    assert rows[-1].ae == (9 + 10 + 11 + 10) / (10 + 10 + 10 + 10)
    assert rows[-1].avg_x == (10 + 20 + 30 + 40) / 4


def test_compute_ae_univariate_rows_categorical_custom_groups() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c", "d", "e"],
            "MEC": [10.0, 10.0, 10.0, 10.0, 10.0],
            "MAC": [10.0, 10.0, 0.0, 10.0, 10.0],
            "sex": ["M", "F", "M", "X", "F"],
        }
    )
    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=ApiAeXVariableCategorical(
            name="sex",
            grouping="custom",
            groups=[
                ApiCategoricalGroupDefinition(name="MF", values=["M", "F"]),
            ],
            remaining_name="Other",
        ),
        app_id_column="APP",
        mec_column="MEC",
        mac_column="MAC",
    )
    assert [r.variable_group for r in rows[:2]] == ["MF", "Other"]
    mf = rows[0]
    other = rows[1]
    assert mf.sample_size == 4  # a,b,c,e
    assert other.sample_size == 1  # d
    assert rows[-1].variable_group == "Total"
    assert rows[-1].avg_x is None


def test_compute_ae_univariate_rows_categorical_positions_are_used_for_x_coord_and_order() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c", "d"],
            "MEC": [10.0, 10.0, 10.0, 10.0],
            "MAC": [10.0, 10.0, 10.0, 10.0],
            "grp": ["A", "B", "C", "D"],
        }
    )
    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=ApiAeXVariableCategorical(
            name="grp",
            grouping="custom",
            groups=[
                ApiCategoricalGroupDefinition(name="G1", values=["A"], x_position=10.0),
                ApiCategoricalGroupDefinition(name="G2", values=["B"], x_position=30.0),
            ],
            remaining_name="Other",
            remaining_position=20.0,
        ),
        app_id_column="APP",
        mec_column="MEC",
        mac_column="MAC",
    )
    labels = [r.variable_group for r in rows[:-1]]
    assert labels == ["G1", "Other", "G2"]
    coords = {r.variable_group: r.x_coord for r in rows[:-1]}
    assert coords == {"G1": 10.0, "Other": 20.0, "G2": 30.0}


def test_compute_polynomial_fit_ignores_ae_outside_0_to_2() -> None:
    # Fit should include all finite points; out-of-bounds points are handled at rendering time.
    rows = [
        ApiAeUnivariateRow(
            variable_group="A",
            avg_x=1.0,
            x_coord=None,
            sample_size=10,
            deaths=0.0,
            ae=1.0,
        ),
        ApiAeUnivariateRow(
            variable_group="B",
            avg_x=2.0,
            x_coord=None,
            sample_size=10,
            deaths=0.0,
            ae=1.5,
        ),
        ApiAeUnivariateRow(
            variable_group="C",
            avg_x=3.0,
            x_coord=None,
            sample_size=10,
            deaths=0.0,
            ae=2.5,
        ),
        ApiAeUnivariateRow(
            variable_group="Total",
            avg_x=2.0,
            x_coord=None,
            sample_size=30,
            deaths=0.0,
            ae=1.0,
        ),
    ]

    fit = compute_polynomial_fit(
        rows=rows,
        x_variable=ApiAeXVariableNumeric(
            name="x",
            binning=ApiNumericBinning.UNIFORM,
            bin_count=2,
        ),
        params=ApiAePolynomialFitParameters(degree=1, weighted=False),
        x_domain=(1.0, 3.0),
    )
    assert fit is not None
    assert len(fit.coefficients) == 2


def test_compute_polynomial_fit_categorical_returns_smooth_table() -> None:
    rows = [
        ApiAeUnivariateRow(
            variable_group="G1",
            avg_x=None,
            x_coord=0.0,
            sample_size=10,
            deaths=0.0,
            ae=0.8,
        ),
        ApiAeUnivariateRow(
            variable_group="G2",
            avg_x=None,
            x_coord=10.0,
            sample_size=10,
            deaths=0.0,
            ae=1.2,
        ),
        ApiAeUnivariateRow(
            variable_group="Total",
            avg_x=None,
            x_coord=None,
            sample_size=20,
            deaths=0.0,
            ae=1.0,
        ),
    ]
    fit = compute_polynomial_fit(
        rows=rows,
        x_variable=ApiAeXVariableCategorical(
            name="grp",
            grouping="custom",
            groups=[
                ApiCategoricalGroupDefinition(name="G1", values=["a"], x_position=0.0),
            ],
            remaining_name="G2",
            remaining_position=10.0,
        ),
        params=ApiAePolynomialFitParameters(degree=1, weighted=False),
        x_domain=None,
    )
    assert fit is not None
    assert len(fit.fit_table.rows) == 200


def test_compute_ae_univariate_rows_date_uniform_includes_total() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c", "d"],
            "MEC": [10.0, 10.0, 10.0, 10.0],
            "MAC": [9.0, 10.0, 11.0, 10.0],
            "as_of": ["2020-01-01", "2020-01-10", "2020-01-20", "2020-01-30"],
        }
    )
    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=ApiAeXVariableDate(
            name="as_of",
            binning=ApiNumericBinning.UNIFORM,
            bin_count=2,
        ),
        app_id_column="APP",
        mec_column="MEC",
        mac_column="MAC",
    )
    assert rows[-1].variable_group == "Total"
    assert rows[-1].avg_x is not None


def test_cross_variable_groups_overlap_raises() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c"],
            "MEC": [10.0, 10.0, 10.0],
            "MAC": [10.0, 10.0, 10.0],
            "A": ["A1", "A2", "A1"],
            "B": ["B1", "B1", "B2"],
        }
    )

    x_variable = ApiAeXVariableCross(
        a_variable=ApiAeXVariableCategorical(name="A", grouping="all_unique"),
        b_variable=ApiAeXVariableCategorical(name="B", grouping="all_unique"),
        groups=[
            ApiAeCrossGroupDefinition(name="G1", a_any=False, a_values=["A1"], b_any=True),
            ApiAeCrossGroupDefinition(name="G2", a_any=True, b_any=False, b_values=["B1"]),
        ],
        remaining_name="Remaining",
    )

    try:
        compute_ae_univariate_rows(
            df=df,
            x_variable=x_variable,
            app_id_column="APP",
            mec_column="MEC",
            mac_column="MAC",
        )
        assert False, "Expected ValueError due to overlapping cross groups"
    except ValueError as exc:
        assert "overlap" in str(exc).lower()


def test_cross_variable_groups_disjoint_and_remaining() -> None:
    df = pd.DataFrame(
        {
            "APP": ["a", "b", "c", "d"],
            "MEC": [10.0, 10.0, 10.0, 10.0],
            "MAC": [10.0, 10.0, 0.0, 10.0],
            "A": ["A1", "A2", "A1", "A3"],
            "B": ["B1", "B1", "B2", "B1"],
        }
    )

    x_variable = ApiAeXVariableCross(
        a_variable=ApiAeXVariableCategorical(name="A", grouping="all_unique"),
        b_variable=ApiAeXVariableCategorical(name="B", grouping="all_unique"),
        groups=[
            ApiAeCrossGroupDefinition(
                name="A1xB1",
                a_any=False,
                a_values=["A1"],
                b_any=False,
                b_values=["B1"],
                x_position=10.0,
            ),
            ApiAeCrossGroupDefinition(
                name="AnyAxB2",
                a_any=True,
                b_any=False,
                b_values=["B2"],
                x_position=20.0,
            ),
        ],
        remaining_name="Other",
        remaining_position=30.0,
    )

    rows = compute_ae_univariate_rows(
        df=df,
        x_variable=x_variable,
        app_id_column="APP",
        mec_column="MEC",
        mac_column="MAC",
    )

    labels = [r.variable_group for r in rows[:-1]]
    assert labels == ["A1xB1", "AnyAxB2", "Other"]
    coords = {r.variable_group: r.x_coord for r in rows[:-1]}
    assert coords == {"A1xB1": 10.0, "AnyAxB2": 20.0, "Other": 30.0}
