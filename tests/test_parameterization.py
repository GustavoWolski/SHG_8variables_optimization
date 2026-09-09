"""Tests for the shared independent normalized optimization parameterization."""

import numpy as np
import pytest

from optimization.constraints import PARAMETER_COUNT, is_physically_valid
from optimization.parameterization import NORMALIZED_PARAMETER_COUNT, to_normalized, to_physical, validate_normalized


def test_physical_and_normalized_vectors_have_eight_coordinates() -> None:
    parameters = to_physical(np.zeros(NORMALIZED_PARAMETER_COUNT))

    assert PARAMETER_COUNT == 8
    assert NORMALIZED_PARAMETER_COUNT == 8
    assert parameters.shape == (8,)


def test_zero_normalized_vector_maps_oxide_indices_to_one() -> None:
    parameters = to_physical(np.zeros(8))

    assert is_physically_valid(parameters)
    np.testing.assert_array_equal(parameters[2:4], [1.0, 1.0])


def test_one_normalized_vector_maps_oxide_indices_to_one_point_two() -> None:
    parameters = to_physical(np.ones(8))

    assert is_physically_valid(parameters)
    np.testing.assert_allclose(parameters[[0, 1, 5, 7]], [10.0, 20.0, 4.0, 4.0])
    np.testing.assert_array_equal(parameters[2:4], [1.2, 1.2])
    np.testing.assert_array_equal(parameters[[4, 6]], [6.0, 6.0])


def test_layer_3_real_indices_map_independently_and_allow_reverse_order() -> None:
    normalized = np.array([0.5, 0.5, 0.5, 0.5, 0.9, 0.1, 0.5, 0.5])
    parameters = to_physical(normalized)

    assert parameters[4] > parameters[6]
    assert is_physically_valid(parameters)
    np.testing.assert_allclose(to_normalized(parameters), normalized, rtol=0.0, atol=2e-14)


def test_random_normalized_points_are_in_bounds_and_round_trip() -> None:
    normalized = np.random.default_rng(20260909).uniform(0.0, 1.0, size=(1_000, 8))
    parameters = np.array([to_physical(point) for point in normalized])

    assert np.all(np.isfinite(parameters))
    assert all(is_physically_valid(point) for point in parameters)
    assert np.all((parameters[:, 2] >= 1.0) & (parameters[:, 2] <= 1.2))
    assert np.all((parameters[:, 3] >= 1.0) & (parameters[:, 3] <= 1.2))
    assert np.all((parameters[:, 4] >= 1.5) & (parameters[:, 4] <= 6.0))
    assert np.all((parameters[:, 6] >= 1.5) & (parameters[:, 6] <= 6.0))
    np.testing.assert_allclose(parameters[:, 2], 1.0 + 0.2 * normalized[:, 2], rtol=0.0, atol=0.0)
    np.testing.assert_allclose(parameters[:, 3], 1.0 + 0.2 * normalized[:, 3], rtol=0.0, atol=0.0)
    np.testing.assert_allclose(
        np.array([to_normalized(point) for point in parameters]), normalized, rtol=0.0, atol=2e-14
    )


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
