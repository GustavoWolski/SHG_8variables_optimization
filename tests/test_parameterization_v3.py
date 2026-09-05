"""Tests for V3's six-coordinate direct-box parameterization."""

import numpy as np

from optimization.constraints_v3 import is_physically_valid_v3
from optimization.parameterization_v3 import to_normalized_v3, to_physical_v3


def test_v3_normalized_boundaries_map_to_the_direct_nb_and_index_bounds() -> None:
    lower = to_physical_v3(np.zeros(6))
    upper = to_physical_v3(np.ones(6))

    np.testing.assert_array_equal(lower, [-10.0, 130.0, 1.5, 0.0, 1.5, 0.0])
    np.testing.assert_array_equal(upper, [10.0, 150.0, 6.0, 4.0, 6.0, 4.0])


def test_v3_parameterization_has_no_real_index_ordering_or_margin() -> None:
    parameters = to_physical_v3(np.array([0.5, 0.5, 1.0, 0.25, 0.0, 0.75]))

    assert parameters[2] > parameters[4]
    assert is_physically_valid_v3(parameters)


def test_v3_parameterization_round_trips_exactly_with_affine_coordinates() -> None:
    normalized = np.array([0.2, 0.8, 0.9, 0.1, 0.3, 0.7])

    np.testing.assert_allclose(to_normalized_v3(to_physical_v3(normalized)), normalized, rtol=0.0, atol=1e-15)
