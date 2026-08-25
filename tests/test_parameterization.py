"""Tests for the shared normalized optimization parameterization."""

import numpy as np
import pytest

from optimization.constraints import is_physically_valid
from optimization.parameterization import DELTA_N, to_normalized, to_physical, validate_normalized


def test_zero_normalized_vector_maps_to_a_valid_strictly_ordered_vector() -> None:
    parameters = to_physical(np.zeros(8))

    assert is_physically_valid(parameters)
    assert parameters[2] + DELTA_N <= parameters[3]
    assert parameters[4] + DELTA_N <= parameters[6]


def test_one_normalized_vector_maps_to_a_valid_vector() -> None:
    parameters = to_physical(np.ones(8))

    assert is_physically_valid(parameters)
    np.testing.assert_allclose(parameters[[0, 1, 5, 7]], [10.0, 20.0, 4.0, 4.0])
    assert parameters[2] < parameters[3]
    assert parameters[4] < parameters[6]


def test_half_normalized_vector_maps_deterministically() -> None:
    parameters = to_physical(np.full(8, 0.5))

    assert is_physically_valid(parameters)
    np.testing.assert_array_equal(parameters, to_physical(np.full(8, 0.5)))


def test_random_normalized_points_are_valid_and_round_trip_in_the_interior() -> None:
    normalized = np.random.default_rng(20260825).uniform(1e-6, 1.0 - 1e-6, size=(1_000, 8))

    for point in normalized:
        parameters = to_physical(point)
        assert is_physically_valid(parameters)
        np.testing.assert_allclose(to_normalized(parameters), point, rtol=0.0, atol=2e-14)


def test_physical_to_normalized_to_physical_round_trip() -> None:
    normalized = np.array([0.2, 0.8, 0.3, 0.7, 0.4, 0.6, 0.1, 0.9])
    parameters = to_physical(normalized)

    np.testing.assert_allclose(to_physical(to_normalized(parameters)), parameters, rtol=0.0, atol=2e-14)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf])
def test_normalized_nan_and_infinite_values_are_rejected(value: float) -> None:
    normalized = np.full(8, 0.5)
    normalized[3] = value

    with pytest.raises(ValueError, match="finite"):
        validate_normalized(normalized)


@pytest.mark.parametrize("normalized", [np.zeros(7), np.zeros(9), np.zeros((1, 8))])
def test_normalized_incorrect_shape_is_rejected(normalized: np.ndarray) -> None:
    with pytest.raises(ValueError, match="shape"):
        to_physical(normalized)


@pytest.mark.parametrize("coordinate", [-1e-12, 1.0 + 1e-12])
def test_normalized_out_of_bounds_values_are_rejected(coordinate: float) -> None:
    normalized = np.full(8, 0.5)
    normalized[0] = coordinate

    with pytest.raises(ValueError, match="0 <="):
        validate_normalized(normalized)


def test_trimmed_gap_is_explicitly_enforced_by_the_inverse() -> None:
    parameters = np.array([0.0, 10.0, 2.0, 2.0 + DELTA_N / 2.0, 3.0, 1.0, 4.0, 1.0])

    assert is_physically_valid(parameters)
    with pytest.raises(ValueError, match="DELTA_N"):
        to_normalized(parameters)


def test_one_hundred_thousand_uniform_points_are_valid_and_uniform_over_each_triangle() -> None:
    normalized = np.random.default_rng(20260826).uniform(0.0, 1.0, size=(100_000, 8))
    parameters = np.array([to_physical(point) for point in normalized])

    assert np.all(np.isfinite(parameters))
    assert all(is_physically_valid(point) for point in parameters)
    assert np.all(parameters[:, 2] >= 1.5)
    assert np.all(parameters[:, 3] <= 6.0)
    assert np.all(parameters[:, 4] >= 1.5)
    assert np.all(parameters[:, 6] <= 6.0)
    assert np.all(parameters[:, 2] + DELTA_N <= parameters[:, 3])
    assert np.all(parameters[:, 4] + DELTA_N <= parameters[:, 6])

    side = 6.0 - 1.5 - DELTA_N
    # For a uniform triangle, both x = n_w - 1.5 and y = n_2w - n_w - DELTA_N have mean side / 3.
    for lower_column, upper_column in ((2, 3), (4, 6)):
        x = parameters[:, lower_column] - 1.5
        y = parameters[:, upper_column] - parameters[:, lower_column] - DELTA_N
        assert abs(float(np.mean(x)) - side / 3.0) < 0.02
        assert abs(float(np.mean(y)) - side / 3.0) < 0.02
