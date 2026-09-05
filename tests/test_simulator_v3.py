"""Internal physical checks for the V3 air | Nb | glass simulator."""

import numpy as np
import pytest

from physics.simulator_v3 import shg_3layers_v3, simulate_v3


P_V3 = np.array([0.0, 140.0, 2.6, 0.7, 2.0, 0.8])
EXPERIMENTAL_THICKNESSES_NM = np.array([65, 80, 100, 150, 190, 250, 300, 400, 500, 600])


def test_v3_simulator_returns_finite_transmission_and_reflection() -> None:
    result = simulate_v3(P_V3, EXPERIMENTAL_THICKNESSES_NM)

    assert result.T.shape == (EXPERIMENTAL_THICKNESSES_NM.size,)
    assert result.R.shape == (EXPERIMENTAL_THICKNESSES_NM.size,)
    assert np.all(np.isfinite(result.T))
    assert np.all(np.isfinite(result.R))
    assert np.all(np.isfinite(result.I_4))
    assert np.all(np.isfinite(result.I_1))


def test_v3_simulator_is_deterministic() -> None:
    first = simulate_v3(P_V3, EXPERIMENTAL_THICKNESSES_NM)
    second = simulate_v3(P_V3, EXPERIMENTAL_THICKNESSES_NM)

    np.testing.assert_array_equal(first.T, second.T)
    np.testing.assert_array_equal(first.R, second.R)


def test_v3_diagnostics_expose_only_the_direct_nb_stack_matrices() -> None:
    result = simulate_v3(P_V3, 150.0, diagnostics=True)

    assert result.diagnostics is not None
    diagnostics = result.diagnostics
    assert diagnostics.d3_nb_m == pytest.approx(140e-9)
    assert diagnostics.t1w.shape == (2, 2)
    assert diagnostics.e31w.shape == (2, 1)
    assert diagnostics.m311w.shape == (2, 2)
    assert diagnostics.p31w.shape == (2, 2)
    assert diagnostics.m431w.shape == (2, 2)
    assert diagnostics.m312w.shape == (2, 2)
    assert not hasattr(diagnostics, "n21w")
    assert not hasattr(diagnostics, "d2_m")
    assert not hasattr(diagnostics, "m211w")
    assert not hasattr(diagnostics, "p21w")
    assert not hasattr(diagnostics, "m322w")


def test_v3_simulator_rejects_a_vector_with_legacy_oxide_coordinates() -> None:
    with pytest.raises(ValueError, match="exactly six"):
        shg_3layers_v3(EXPERIMENTAL_THICKNESSES_NM, np.zeros(8))
