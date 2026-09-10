"""Tests for the combined dense T/R visualization."""

from pathlib import Path

import numpy as np

from analysis.plotting import CombinedTRPlotConfig, ExperimentalTRData, plot_combined_tr_fit
from experiments.data import D_NM, R_EXP, T_EXP
from optimization.objective import evaluate
from physics.simulator import SimulationResult, simulate


VALID_P = np.array([9.5, 10.0, 5.5, 0.7, 2.0, 0.8])


def test_combined_plot_uses_one_untouched_dense_nominal_grid_and_same_p(tmp_path: Path) -> None:
    captured: list[tuple[np.ndarray, np.ndarray]] = []

    def recording_simulator(p: np.ndarray, thickness_nm: np.ndarray) -> SimulationResult:
        captured.append((p.copy(), thickness_nm.copy()))
        return simulate(p, thickness_nm)

    p_before = VALID_P.copy()
    thickness_before = D_NM.copy()
    transmission_before = T_EXP.copy()
    reflection_before = R_EXP.copy()
    result = plot_combined_tr_fit(
        VALID_P,
        ExperimentalTRData(D_NM, T_EXP, R_EXP),
        CombinedTRPlotConfig(tmp_path, filename_stem="combined"),
        algorithm="Infrastructure test vector",
        simulator=recording_simulator,
    )

    assert len(captured) == 1
    captured_p, captured_thickness = captured[0]
    np.testing.assert_array_equal(captured_p, p_before)
    np.testing.assert_array_equal(captured_thickness, result.thickness_plot_nm)
    assert result.thickness_plot_nm.size == 601
    assert result.thickness_plot_nm[0] == 0.0
    assert result.thickness_plot_nm[-1] == 600.0
    np.testing.assert_array_equal(np.diff(result.thickness_plot_nm), np.ones(600))
    assert result.T_theoretical.size == 601
    assert result.R_theoretical.size == 601
    assert result.experimental_point_count == D_NM.size == 10
    np.testing.assert_array_equal(VALID_P, p_before)
    np.testing.assert_array_equal(D_NM, thickness_before)
    np.testing.assert_array_equal(T_EXP, transmission_before)
    np.testing.assert_array_equal(R_EXP, reflection_before)
    assert result.png_path.is_file() and result.png_path.stat().st_size > 0
    assert result.pdf_path.is_file() and result.pdf_path.stat().st_size > 0


def test_plotting_does_not_double_apply_delta_or_change_objective_and_simulator(tmp_path: Path) -> None:
    objective_before = evaluate(VALID_P)
    dense_before = simulate(VALID_P, np.arange(0.0, 601.0, 1.0))

    result = plot_combined_tr_fit(
        VALID_P,
        ExperimentalTRData(D_NM, T_EXP, R_EXP),
        CombinedTRPlotConfig(tmp_path, filename_stem="unchanged-model"),
    )

    objective_after = evaluate(VALID_P)
    dense_after = simulate(VALID_P, np.arange(0.0, 601.0, 1.0))
    np.testing.assert_array_equal(result.T_theoretical, dense_before.T)
    np.testing.assert_array_equal(result.R_theoretical, dense_before.R)
    assert objective_after.J == objective_before.J
    assert objective_after.J_T == objective_before.J_T
    assert objective_after.J_R == objective_before.J_R
    np.testing.assert_array_equal(dense_after.T, dense_before.T)
    np.testing.assert_array_equal(dense_after.R, dense_before.R)
