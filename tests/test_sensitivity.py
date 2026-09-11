"""Tests for reusable one-at-a-time sensitivity analysis."""

from types import SimpleNamespace

import numpy as np

from analysis.sensitivity import (
    SensitivitySweep,
    approximate_curvature,
    sensitivity_grid,
    sweep_parameter,
    threshold_region_width,
)


REFERENCE = np.array([0.0, -20.0, 2.0, 1.0, 3.0, 2.0])


def test_global_grid_is_uniform_and_uses_complete_inclusive_bounds() -> None:
    grid = sensitivity_grid(REFERENCE, 2, "global")
    assert grid.size == 101
    assert grid[0] == 0.1
    assert grid[-1] == 10.0
    np.testing.assert_allclose(np.diff(grid), np.diff(grid)[0])


def test_local_grid_uses_ten_percent_of_expanded_bound_span() -> None:
    grid = sensitivity_grid(REFERENCE, 1, "local")
    assert grid.size == 101
    assert grid[0] == -30.0
    assert grid[-1] == -10.0


def test_asymmetric_local_grid_contains_reference_exactly() -> None:
    grid = sensitivity_grid(REFERENCE, 2, "local")
    assert grid.size == 101
    assert np.any(grid == REFERENCE[2])
    assert np.all(np.diff(grid) > 0.0)


def test_sweep_changes_only_requested_coordinate_and_records_components() -> None:
    candidates: list[np.ndarray] = []

    def fake_evaluate(p: np.ndarray) -> SimpleNamespace:
        candidates.append(np.asarray(p).copy())
        j_t = float(p[2] ** 2)
        j_r = 1.0
        return SimpleNamespace(J=j_t + j_r, J_T=j_t, J_R=j_r)

    sweep = sweep_parameter(REFERENCE, 2, "local", point_count=5, evaluator=fake_evaluate)  # type: ignore[arg-type]

    assert sweep.n_evaluations == 5
    assert len(candidates) == 5
    for candidate, value in zip(candidates, sweep.values, strict=True):
        expected = REFERENCE.copy()
        expected[2] = value
        np.testing.assert_array_equal(candidate, expected)
    np.testing.assert_array_equal(sweep.J, sweep.J_T + sweep.J_R)


def test_quadratic_curvature_and_threshold_width_are_recovered() -> None:
    x = np.linspace(-2.0, 2.0, 101)
    j = 1.0 + x**2
    sweep = SensitivitySweep(0, "x", "global", x, j, j.copy(), np.zeros_like(j))

    assert np.isclose(approximate_curvature(sweep, 0.0), 2.0, atol=1e-10)
    assert np.isclose(threshold_region_width(sweep, 0.0, 1.0, 0.05), 2.0 * np.sqrt(0.05), atol=0.003)
