"""Sanity tests for the physical simulator before MATLAB numerical comparison."""

import numpy as np

from physics.simulator import (
    D2_FIXED_NM,
    N2_2W_FIXED,
    N2_W_FIXED,
    effective_active_thickness_nm,
    shg_4layers,
    shg_mos2_ratios,
    simulate,
)


P0 = np.array([0.0, 0.0, 2.04, 0.70, 1.42, 0.80])
P_SEARCH_SPACE = np.array([0.0, 10.0, 5.50, 0.70, 2.00, 0.80])
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


def test_simulate_is_finite_and_deterministic_for_valid_reversed_layer_3_indices() -> None:
    first = simulate(P_SEARCH_SPACE, EXPERIMENTAL_THICKNESSES_NM)
    second = simulate(P_SEARCH_SPACE, EXPERIMENTAL_THICKNESSES_NM)

    assert np.all(np.isfinite(first.T))
    assert np.all(np.isfinite(first.R))
    np.testing.assert_array_equal(first.T, second.T)
    np.testing.assert_array_equal(first.R, second.R)


def test_single_thickness_supports_optional_diagnostics() -> None:
    result = simulate(P0, 65.0, diagnostics=True)

    assert result.T.shape == (1,)
    assert result.R.shape == (1,)
    assert result.diagnostics is not None
    assert result.diagnostics.d2_m == D2_FIXED_NM * 1e-9
    assert result.diagnostics.n21w == N2_W_FIXED
    assert result.diagnostics.n22w == N2_2W_FIXED
    assert result.diagnostics.d3_nominal_nm == 65.0
    assert result.diagnostics.d3_effective_nm == 65.0
    assert result.diagnostics.t1w.shape == (2, 2)
    assert result.diagnostics.e31w.shape == (2, 1)
    assert result.diagnostics.mfact_es.shape == (2, 2)
    assert result.diagnostics.s2k.shape == (2, 2)
    assert result.diagnostics.s0k.shape == (2, 2)
    assert result.diagnostics.eshg.shape == (2, 1)
    assert np.isfinite(result.diagnostics.i_4)
    assert np.isfinite(result.diagnostics.i_1)


def test_effective_active_thickness_applies_global_offset_and_zero_floor() -> None:
    assert effective_active_thickness_nm(65.0, 0.0) == 65.0
    assert effective_active_thickness_nm(65.0, 10.0) == 75.0
    assert effective_active_thickness_nm(5.0, -20.0) == 0.0


def test_negative_corrected_thickness_is_zero_in_the_simulator() -> None:
    parameters = P0.copy()
    parameters[1] = -20.0
    result = simulate(parameters, 5.0, diagnostics=True)
    assert result.diagnostics is not None
    assert result.diagnostics.d3_effective_nm == 0.0
    assert result.diagnostics.d3_m == 0.0
    assert np.all(np.isfinite(result.T))
    assert np.all(np.isfinite(result.R))


def test_delta_d3_is_used_by_all_active_thickness_phases_and_sources() -> None:
    result = simulate(P_SEARCH_SPACE, 5.0, diagnostics=True)
    assert result.diagnostics is not None
    assert result.diagnostics.d3_effective_nm == 15.0
    assert result.diagnostics.d3_m == np.float64(15.0) * 1e-9
    assert result.diagnostics.phase31w == result.diagnostics.n31w * (2 * np.pi / 1560e-9) * result.diagnostics.d3_m
    assert result.diagnostics.phase32w == result.diagnostics.n32w * 2 * (2 * np.pi / 1560e-9) * result.diagnostics.d3_m


def test_shg_mos2_ratios_matches_public_simulation_output() -> None:
    transmission, reflection = shg_mos2_ratios(EXPERIMENTAL_THICKNESSES_NM, P0)
    result = simulate(P0, EXPERIMENTAL_THICKNESSES_NM)

    np.testing.assert_array_equal(transmission, result.T)
    np.testing.assert_array_equal(reflection, result.R)
