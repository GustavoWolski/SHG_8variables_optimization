"""Tests for the final six-variable optimization parameter space."""

import numpy as np
import pytest

from optimization.constraints import (
    LOWER_BOUNDS, PARAMETER_COUNT, PARAMETER_NAMES, UPPER_BOUNDS,
    constraint_violations, invalid_reasons, is_physically_valid,
    lower_bounds, upper_bounds, validate_parameter_vector, validate_physical_parameters,
)

VALID_PARAMETERS = np.array([0.0, 0.0, 2.5, 1.0, 3.5, 2.0])


def _codes(parameters: np.ndarray) -> set[str]:
    return {violation.code for violation in constraint_violations(parameters)}


def test_official_parameter_order_and_bounds_are_exposed_immutably() -> None:
    assert PARAMETER_NAMES == ("log10_chi", "delta_d3_nm", "n3_w", "k3_w", "n3_2w", "k3_2w")
    assert PARAMETER_COUNT == 6
    assert not {"d2_nm", "n2_w", "n2_2w"}.intersection(PARAMETER_NAMES)
    assert LOWER_BOUNDS == (-10.0, -20.0, 0.1, 0.0, 0.1, 0.0)
    assert UPPER_BOUNDS == (10.0, 20.0, 10.0, 10.0, 10.0, 10.0)
    np.testing.assert_array_equal(lower_bounds(), LOWER_BOUNDS)
    np.testing.assert_array_equal(upper_bounds(), UPPER_BOUNDS)


def test_fully_valid_vector_passes_all_checks() -> None:
    np.testing.assert_array_equal(validate_physical_parameters(VALID_PARAMETERS), VALID_PARAMETERS)
    assert is_physically_valid(VALID_PARAMETERS)
    assert constraint_violations(VALID_PARAMETERS) == ()
    assert invalid_reasons(VALID_PARAMETERS) == ()


@pytest.mark.parametrize("index", range(PARAMETER_COUNT), ids=PARAMETER_NAMES)
def test_each_parameter_below_its_lower_bound_is_invalid(index: int) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[index] = LOWER_BOUNDS[index] - 0.1
    violations = constraint_violations(parameters)
    assert not is_physically_valid(parameters)
    assert any(v.code == "below_lower_bound" and v.parameter_names == (PARAMETER_NAMES[index],) for v in violations)


@pytest.mark.parametrize("index", range(PARAMETER_COUNT), ids=PARAMETER_NAMES)
def test_each_parameter_above_its_upper_bound_is_invalid(index: int) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[index] = UPPER_BOUNDS[index] + 0.1
    violations = constraint_violations(parameters)
    assert not is_physically_valid(parameters)
    assert any(v.code == "above_upper_bound" and v.parameter_names == (PARAMETER_NAMES[index],) for v in violations)


@pytest.mark.parametrize("delta", [-20.0, 0.0, 20.0])
def test_delta_d3_inclusive_bounds_are_valid(delta: float) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[1] = delta
    assert is_physically_valid(parameters)


def test_layer_3_real_indices_are_independent_and_reverse_order_is_valid() -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[2], parameters[4] = 9.5, 0.2
    assert is_physically_valid(parameters)
    assert "normal_dispersion_n3" not in _codes(parameters)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_nan_and_infinite_values_are_invalid(value: float) -> None:
    parameters = VALID_PARAMETERS.copy()
    parameters[3] = value
    assert _codes(parameters) == {"non_finite"}
    with pytest.raises(ValueError, match="NaN or infinity"):
        validate_parameter_vector(parameters)


@pytest.mark.parametrize("length", [0, 5, 7, 8])
def test_incorrect_vector_length_is_invalid(length: int) -> None:
    parameters = np.zeros(length)
    assert _codes(parameters) == {"invalid_length"}
    with pytest.raises(ValueError, match="exactly 6 parameters"):
        validate_physical_parameters(parameters)


def test_non_vector_shape_is_invalid() -> None:
    assert _codes(VALID_PARAMETERS.reshape(2, 3)) == {"invalid_shape"}
