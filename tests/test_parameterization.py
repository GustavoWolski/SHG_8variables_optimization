"""Tests for the shared six-dimensional normalized parameterization."""

import numpy as np
import pytest

from optimization.constraints import PARAMETER_COUNT, is_physically_valid
from optimization.parameterization import NORMALIZED_PARAMETER_COUNT, to_normalized, to_physical, validate_normalized


def test_physical_and_normalized_vectors_have_six_coordinates() -> None:
    parameters = to_physical(np.zeros(NORMALIZED_PARAMETER_COUNT))
    assert PARAMETER_COUNT == NORMALIZED_PARAMETER_COUNT == 6
    assert parameters.shape == (6,)


@pytest.mark.parametrize(("coordinate", "expected"), [(0.0, -20.0), (0.5, 0.0), (1.0, 20.0)])
def test_delta_d3_linear_mapping(coordinate: float, expected: float) -> None:
    normalized = np.full(6, 0.5)
    normalized[1] = coordinate
    assert to_physical(normalized)[1] == expected


def test_all_coordinates_map_to_their_independent_bounds() -> None:
    np.testing.assert_array_equal(to_physical(np.zeros(6)), [-10.0, -20.0, 1.5, 0.0, 1.5, 0.0])
    np.testing.assert_array_equal(to_physical(np.ones(6)), [10.0, 20.0, 6.0, 4.0, 6.0, 4.0])


def test_layer_3_real_indices_map_independently_and_allow_reverse_order() -> None:
    normalized = np.array([0.5, 0.5, 0.9, 0.5, 0.1, 0.5])
    parameters = to_physical(normalized)
    assert parameters[2] > parameters[4]
    assert is_physically_valid(parameters)
    np.testing.assert_allclose(to_normalized(parameters), normalized, rtol=0.0, atol=2e-14)


def test_random_normalized_points_are_in_bounds_and_round_trip() -> None:
    normalized = np.random.default_rng(20260909).uniform(0.0, 1.0, size=(1_000, 6))
    parameters = np.array([to_physical(point) for point in normalized])
    assert np.all(np.isfinite(parameters))
    assert all(is_physically_valid(point) for point in parameters)
    np.testing.assert_allclose(np.array([to_normalized(point) for point in parameters]), normalized, rtol=0.0, atol=2e-14)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_normalized_nan_and_infinite_values_are_rejected(value: float) -> None:
    normalized = np.full(6, 0.5)
    normalized[3] = value
    with pytest.raises(ValueError, match="finite"):
        validate_normalized(normalized)


@pytest.mark.parametrize("normalized", [np.zeros(5), np.zeros(7), np.zeros((1, 6))])
def test_normalized_incorrect_shape_is_rejected(normalized: np.ndarray) -> None:
    with pytest.raises(ValueError, match="shape"):
        to_physical(normalized)


@pytest.mark.parametrize("coordinate", [-1e-12, 1.0 + 1e-12])
def test_normalized_out_of_bounds_values_are_rejected(coordinate: float) -> None:
    normalized = np.full(6, 0.5)
    normalized[0] = coordinate
    with pytest.raises(ValueError, match="0 <="):
        validate_normalized(normalized)
