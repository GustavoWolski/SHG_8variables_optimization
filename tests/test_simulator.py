"""Sanity tests for the physical simulator before MATLAB numerical comparison."""

import numpy as np

from physics.simulator import shg_4layers, shg_mos2_ratios, simulate


P0 = np.array([0.0, 10.0, 2.10, 2.43, 2.04, 0.70, 1.42, 0.80])
EXPERIMENTAL_THICKNESSES_NM = np.array([65, 80, 100, 150, 190, 250, 300, 400, 500, 600])


def test_simulate_returns_one_dimensional_outputs_for_all_experimental_points() -> None:
    result = simulate(P0, EXPERIMENTAL_THICKNESSES_NM)

    assert result.T.shape == (EXPERIMENTAL_THICKNESSES_NM.size,)
    assert result.R.shape == (EXPERIMENTAL_THICKNESSES_NM.size,)
    assert result.T.dtype == np.float64
    assert result.R.dtype == np.float64
    assert result.diagnostics is None
    assert np.all(np.isfinite(result.T))
    assert np.all(np.isfinite(result.R))


def test_raw_intensities_are_finite_and_nonnegative_for_p0() -> None:
    raw = shg_4layers(EXPERIMENTAL_THICKNESSES_NM, P0)

    assert np.all(np.isfinite(raw.I_4))
    assert np.all(np.isfinite(raw.I_1))
    assert np.isfinite(raw.IMoS24)
    assert np.isfinite(raw.IMoS21)
    assert np.all(raw.I_4 >= 0)
    assert np.all(raw.I_1 >= 0)
    assert raw.IMoS24 >= 0
    assert raw.IMoS21 >= 0


def test_simulation_is_deterministic() -> None:
    first = simulate(P0, EXPERIMENTAL_THICKNESSES_NM)
    second = simulate(P0, EXPERIMENTAL_THICKNESSES_NM)

    np.testing.assert_array_equal(first.T, second.T)
    np.testing.assert_array_equal(first.R, second.R)


def test_single_thickness_supports_optional_diagnostics() -> None:
    result = simulate(P0, 65.0, diagnostics=True)

    assert result.T.shape == (1,)
    assert result.R.shape == (1,)
    assert result.diagnostics is not None
    assert result.diagnostics.t1w.shape == (2, 2)
    assert result.diagnostics.e31w.shape == (2, 1)
    assert result.diagnostics.mfact_es.shape == (2, 2)
    assert result.diagnostics.s2k.shape == (2, 2)
    assert result.diagnostics.s0k.shape == (2, 2)
    assert result.diagnostics.eshg.shape == (2, 1)
    assert np.isfinite(result.diagnostics.i_4)
    assert np.isfinite(result.diagnostics.i_1)


def test_shg_mos2_ratios_matches_public_simulation_output() -> None:
    transmission, reflection = shg_mos2_ratios(EXPERIMENTAL_THICKNESSES_NM, P0)
    result = simulate(P0, EXPERIMENTAL_THICKNESSES_NM)

    np.testing.assert_array_equal(transmission, result.T)
    np.testing.assert_array_equal(reflection, result.R)
