"""Tests for the official optimization parameter space."""

import numpy as np
import pytest

from optimization.constraints import (
    LOWER_BOUNDS,
    PARAMETER_COUNT,
    PARAMETER_NAMES,
    UPPER_BOUNDS,
    constraint_violations,
    invalid_reasons,
    is_physically_valid,
    lower_bounds,
    upper_bounds,
    validate_parameter_vector,
    validate_physical_parameters,
)


VALID_PARAMETERS = np.array([0.0, 10.0, 2.0, 3.0, 2.5, 1.0, 3.5, 2.0])


def _codes(parameters: np.ndarray) -> set[str]:
    return {violation.code for violation in constraint_violations(parameters)}


def test_official_parameter_order_and_bounds_are_exposed_immutably() -> None:
    assert PARAMETER_NAMES == (
        "log10_chi", "d2_nm", "n2_w", "n2_2w", "re_n3_w", "im_n3_w", "re_n3_2w", "im_n3_2w"
    )
    assert PARAMETER_COUNT == 8
    np.testing.assert_array_equal(lower_bounds(), LOWER_BOUNDS)
    np.testing.assert_array_equal(upper_bounds(), UPPER_BOUNDS)


def test_fully_valid_vector_passes_all_checks() -> None:
    validated = validate_physical_parameters(VALID_PARAMETERS)
    np.testing.assert_array_equal(validated, VALID_PARAMETERS)
    assert is_physically_valid(VALID_PARAMETERS)
    assert constraint_violations(VALID_PARAMETERS) == ()
    assert invalid_reasons(VALID_PARAMETERS) == ()


@pytest.mark.parametrize("index", range(PARAMETER_COUNT), ids=PARAMETER_NAMES)
def test_each_parameter_below_its_lower_bound_is_invalid(index: int) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[index] = LOWER_BOUNDS[index] - 0.1

    violations = constraint_violations(parameters)

    assert not is_physically_valid(parameters)
    assert any(
        violation.code == "below_lower_bound" and violation.parameter_names == (PARAMETER_NAMES[index],)
        for violation in violations
    )


@pytest.mark.parametrize("index", range(PARAMETER_COUNT), ids=PARAMETER_NAMES)
def test_each_parameter_above_its_upper_bound_is_invalid(index: int) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[index] = UPPER_BOUNDS[index] + 0.1

    violations = constraint_violations(parameters)

    assert not is_physically_valid(parameters)
    assert any(
        violation.code == "above_upper_bound" and violation.parameter_names == (PARAMETER_NAMES[index],)
        for violation in violations
    )


def test_n2_normal_dispersion_must_be_strict() -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[2] = parameters[3]

    assert "normal_dispersion_n2" in _codes(parameters)
    assert any("n2_w" in reason and "n2_2w" in reason for reason in invalid_reasons(parameters))


def test_n3_real_normal_dispersion_must_be_strict() -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[4] = parameters[6]

    assert "normal_dispersion_n3" in _codes(parameters)
    assert any("re_n3_w" in reason and "re_n3_2w" in reason for reason in invalid_reasons(parameters))


@pytest.mark.parametrize(
    "parameters",
    [
        np.array([-10.0, 0.0, 1.5, 6.0, 1.5, 0.0, 6.0, 0.0]),
        np.array([10.0, 20.0, 1.5, 6.0, 1.5, 4.0, 6.0, 4.0]),
    ],
)
def test_feasible_vectors_at_inclusive_box_limits_are_valid(parameters: np.ndarray) -> None:
    assert is_physically_valid(parameters)


def test_strict_dispersion_can_make_a_closed_box_boundary_infeasible() -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[2] = 6.0
    parameters[3] = 6.0

    assert "above_upper_bound" not in _codes(parameters)
    assert "normal_dispersion_n2" in _codes(parameters)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nan_and_infinite_values_are_invalid(value: float) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[5] = value

    assert _codes(parameters) == {"non_finite"}
    with pytest.raises(ValueError, match="NaN or infinity"):
        validate_parameter_vector(parameters)


@pytest.mark.parametrize("length", [0, 7, 9])
def test_incorrect_vector_length_is_invalid(length: int) -> None:
    parameters = np.zeros(length)

    assert _codes(parameters) == {"invalid_length"}
    with pytest.raises(ValueError, match="exactly 8 parameters"):
        validate_physical_parameters(parameters)


def test_non_vector_shape_is_invalid() -> None:
    parameters = VALID_PARAMETERS.reshape(2, 4)

    assert _codes(parameters) == {"invalid_shape"}

