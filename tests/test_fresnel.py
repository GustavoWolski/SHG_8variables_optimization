"""Algebraic regression tests for the MATLAB Fresnel helper functions."""

import pytest

from physics.fresnel import rij, tij


EPS0 = 8.8541878176e-12
C = 3e8
Z0 = 1 / (EPS0 * C)
TOLERANCE = {"rel": 1e-14, "abs": 1e-15}


def test_rij_matches_matlab_expression_for_real_indices_and_zero_surface_conductivity() -> None:
    n1 = 1.0
    n2 = 1.513
    sig_s = 0.0

    expected = (n1 - n2 - Z0 * sig_s) / (n1 + n2 + Z0 * sig_s)

    assert rij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)


def test_rij_matches_matlab_expression_for_complex_indices_and_zero_surface_conductivity() -> None:
    n1 = 2.04 + 0.70j
    n2 = 2.10
    sig_s = 0.0

    expected = (n1 - n2 - Z0 * sig_s) / (n1 + n2 + Z0 * sig_s)

    assert rij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)


def test_rij_matches_matlab_expression_for_complex_surface_conductivity() -> None:
    n1 = 1.0
    n2 = 1.513 + 0.02j
    sig_s = 1.2e-4 - 2.5e-4j

    expected = (n1 - n2 - Z0 * sig_s) / (n1 + n2 + Z0 * sig_s)

    assert rij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)


def test_tij_matches_matlab_expression_for_real_indices_and_zero_surface_conductivity() -> None:
    n1 = 1.0
    n2 = 1.513
    sig_s = 0.0

    expected = 2 * n1 / (n1 + n2 + Z0 * sig_s)

    assert tij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)


def test_tij_matches_matlab_expression_for_complex_indices_and_zero_surface_conductivity() -> None:
    n1 = 2.04 + 0.70j
    n2 = 2.10
    sig_s = 0.0

    expected = 2 * n1 / (n1 + n2 + Z0 * sig_s)

    assert tij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)


def test_tij_matches_matlab_expression_for_complex_surface_conductivity() -> None:
    n1 = 1.0
    n2 = 1.513 + 0.02j
    sig_s = 1.2e-4 - 2.5e-4j

    expected = 2 * n1 / (n1 + n2 + Z0 * sig_s)

    assert tij(n1, n2, sig_s) == pytest.approx(expected, **TOLERANCE)
