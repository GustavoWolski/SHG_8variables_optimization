"""Tests for exact-budget normalized SciPy Differential Evolution."""

from dataclasses import replace

import numpy as np
import pytest

from optimization.constraints import is_physically_valid
from optimization.differential_evolution import DEFAULT_CONFIGURATION, differential_evolution
from optimization.objective import evaluate


def test_same_seed_and_configuration_produce_the_same_result() -> None:
    first = differential_evolution(seed=7, budget=41)
    second = differential_evolution(seed=7, budget=41)

    assert first.best_J == second.best_J
    assert first.best_J_T == second.best_J_T
    assert first.best_J_R == second.best_J_R
    np.testing.assert_array_equal(first.best_z, second.best_z)
    np.testing.assert_array_equal(first.best_p, second.best_p)
    assert first.convergence_history == second.convergence_history


def test_different_seeds_can_produce_different_results() -> None:
    first = differential_evolution(seed=1, budget=1)
    second = differential_evolution(seed=2, budget=1)

    assert not np.array_equal(first.best_z, second.best_z)


@pytest.mark.parametrize("budget", [1, 9, 121])
def test_budget_is_exact_and_never_exceeded(budget: int) -> None:
    result = differential_evolution(seed=5, budget=budget)

    assert result.n_evaluations == budget
    assert result.n_evaluations <= result.budget
    assert result.scipy_nfev == budget
    assert result.scipy_maxfun == budget
    assert len(result.convergence_history) == budget
    assert result.convergence_history[0].evaluation == 1
    assert result.convergence_history[-1].evaluation == budget


def test_best_solution_is_normalized_physically_valid_and_component_consistent() -> None:
    result = differential_evolution(seed=8, budget=37)

    assert np.all((0.0 <= result.best_z) & (result.best_z <= 1.0))
    assert is_physically_valid(result.best_p)
    assert result.valid_physics
    assert result.best_J == result.best_J_T + result.best_J_R


def test_history_is_best_so_far_and_final_result_matches_independent_evaluation() -> None:
    result = differential_evolution(seed=9, budget=53)
    best_history = np.array([record.best_J for record in result.convergence_history])
    detailed = evaluate(result.best_p)

    assert np.all(np.diff(best_history) <= 0.0)
    assert result.best_J == best_history[-1]
    assert detailed.J == result.best_J
    assert detailed.J_T == result.best_J_T
    assert detailed.J_R == result.best_J_R
    np.testing.assert_array_equal(detailed.T_theoretical, result.T_theoretical)
    np.testing.assert_array_equal(detailed.R_theoretical, result.R_theoretical)


@pytest.mark.parametrize(
    "budget, configuration",
    [
        (0, DEFAULT_CONFIGURATION),
        (-1, DEFAULT_CONFIGURATION),
        (1.5, DEFAULT_CONFIGURATION),
        (1, replace(DEFAULT_CONFIGURATION, polish=True)),
        (1, replace(DEFAULT_CONFIGURATION, popsize=0)),
        (1, replace(DEFAULT_CONFIGURATION, updating="immediate")),
    ],
)
def test_invalid_budget_or_configuration_is_rejected(
    budget: int | float,
    configuration: object,
) -> None:
    with pytest.raises(ValueError):
        differential_evolution(seed=1, budget=budget, configuration=configuration)  # type: ignore[arg-type]


def test_pure_de_explicitly_disables_polishing() -> None:
    result = differential_evolution(seed=3, budget=11)

    assert result.configuration.polish is False
