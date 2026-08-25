"""Tests for the normalized, reproducible Random Search baseline."""

import numpy as np
import pytest

from optimization.constraints import is_physically_valid
from optimization.objective import evaluate
from optimization.random_search import random_search


def test_same_seed_and_budget_produce_the_same_search_result() -> None:
    first = random_search(seed=7, budget=12)
    second = random_search(seed=7, budget=12)

    assert first.seed == second.seed
    assert first.best_J == second.best_J
    assert first.best_J_T == second.best_J_T
    assert first.best_J_R == second.best_J_R
    np.testing.assert_array_equal(first.best_z, second.best_z)
    np.testing.assert_array_equal(first.best_p, second.best_p)
    assert first.convergence_history == second.convergence_history


def test_different_seeds_generate_different_candidate_sequences() -> None:
    first = random_search(seed=1, budget=1)
    second = random_search(seed=2, budget=1)

    assert not np.array_equal(first.best_z, second.best_z)


@pytest.mark.parametrize("budget", [1, 3, 11])
def test_search_stops_exactly_at_the_physical_evaluation_budget(budget: int) -> None:
    result = random_search(seed=4, budget=budget)

    assert result.n_evaluations == budget
    assert result.n_evaluations <= result.budget
    assert len(result.convergence_history) == budget
    assert result.convergence_history[0].evaluation == 1
    assert result.convergence_history[-1].evaluation == budget


def test_best_solution_uses_valid_normalized_and_physical_coordinates() -> None:
    result = random_search(seed=12, budget=10)

    assert np.all((0.0 <= result.best_z) & (result.best_z <= 1.0))
    assert is_physically_valid(result.best_p)
    assert result.valid_physics


def test_best_objective_components_and_convergence_are_consistent() -> None:
    result = random_search(seed=10, budget=15)
    best_values = np.array([record.best_J for record in result.convergence_history])

    assert result.best_J == result.best_J_T + result.best_J_R
    assert result.best_J == result.convergence_history[-1].best_J
    assert np.all(np.diff(best_values) <= 0.0)


def test_final_result_matches_a_fresh_detailed_objective_evaluation() -> None:
    result = random_search(seed=14, budget=9)
    detailed = evaluate(result.best_p)

    assert detailed.J == result.best_J
    assert detailed.J_T == result.best_J_T
    assert detailed.J_R == result.best_J_R
    np.testing.assert_array_equal(detailed.T_theoretical, result.T_theoretical)
    np.testing.assert_array_equal(detailed.R_theoretical, result.R_theoretical)


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_budget_is_rejected(budget: int | float | bool) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        random_search(seed=1, budget=budget)
