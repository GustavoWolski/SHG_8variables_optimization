"""Regression tests for the MATLAB soda-lime glass index helper."""

import numpy as np
import pytest

from physics.glass import nlimeglass


TOLERANCE = {"rel": 1e-14, "abs": 1e-15}


@pytest.mark.parametrize("lambda_m", [1560e-9, 780e-9, 1000e-9])
def test_nlimeglass_matches_matlab_expression_for_scalar_wavelengths(lambda_m: float) -> None:
    l = lambda_m / 1e-6
    expected = 1.5130 - 0.003169 * l**2 + 0.003962 / (l**2)

    assert nlimeglass(lambda_m) == pytest.approx(expected, **TOLERANCE)


def test_nlimeglass_matches_matlab_expression_for_numpy_scalar() -> None:
    lambda_m = np.float64(1560e-9)
    l = lambda_m / 1e-6
    expected = 1.5130 - 0.003169 * l**2 + 0.003962 / (l**2)

    assert nlimeglass(lambda_m) == pytest.approx(expected, **TOLERANCE)


def test_nlimeglass_matches_matlab_expression_elementwise_for_numpy_array() -> None:
    lambda_m = np.array([780e-9, 1000e-9, 1560e-9])
    l = lambda_m / 1e-6
    expected = 1.5130 - 0.003169 * l**2 + 0.003962 / (l**2)

    np.testing.assert_allclose(nlimeglass(lambda_m), expected, rtol=1e-14, atol=1e-15)
