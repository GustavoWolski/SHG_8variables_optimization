"""Tests for the exact-budget real-coded Genetic Algorithm baseline."""

from dataclasses import replace

import numpy as np
import pytest

from optimization.constraints import is_physically_valid
import optimization.genetic_algorithm as genetic_algorithm_module
from optimization.genetic_algorithm import (
    DEFAULT_CONFIGURATION,
    GeneticAlgorithmConfiguration,
    _clip_normalized,
    _polynomial_mutation,
    _simulated_binary_crossover,
    genetic_algorithm,
)
from optimization.objective import evaluate
from optimization.parameterization import to_physical


def test_same_seed_configuration_and_budget_are_reproducible() -> None:
    first = genetic_algorithm(seed=7, budget=43)
    second = genetic_algorithm(seed=7, budget=43)

    assert first.best_J == second.best_J
    assert first.best_J_T == second.best_J_T
    assert first.best_J_R == second.best_J_R
    np.testing.assert_array_equal(first.best_z, second.best_z)
    np.testing.assert_array_equal(first.best_p, second.best_p)
    assert first.convergence_history == second.convergence_history


def test_different_seeds_can_produce_different_trajectories() -> None:
    first = genetic_algorithm(seed=1, budget=21)
    second = genetic_algorithm(seed=2, budget=21)

    assert not np.array_equal(first.best_z, second.best_z)
    assert first.convergence_history != second.convergence_history


@pytest.mark.parametrize("budget", [1, 7, 100, 103])
def test_budget_is_exact_even_when_smaller_or_not_multiple_of_population(budget: int) -> None:
    result = genetic_algorithm(seed=5, budget=budget)

    assert result.n_evaluations == budget
    assert result.n_evaluations <= result.budget
    assert len(result.convergence_history) == budget
    assert result.convergence_history[0].evaluation == 1
    assert result.convergence_history[-1].evaluation == budget
    assert result.effective_population_size == min(DEFAULT_CONFIGURATION.population_size, budget)


def test_best_and_population_coordinates_remain_normalized_and_physical() -> None:
    result = genetic_algorithm(seed=8, budget=137)

    assert np.all((0.0 <= result.best_z) & (result.best_z <= 1.0))
    assert np.all((0.0 <= result.final_population_z) & (result.final_population_z <= 1.0))
    assert is_physically_valid(result.best_p)
    assert result.valid_physics
    assert result.best_J == result.best_J_T + result.best_J_R


def test_history_is_monotonic_and_best_matches_independent_evaluation() -> None:
    result = genetic_algorithm(seed=9, budget=153)
    history = np.asarray([record.best_J for record in result.convergence_history])
    detailed = evaluate(result.best_p)

    assert np.all(np.diff(history) <= 0.0)
    assert result.best_J == history[-1]
    assert detailed.J == result.best_J
    assert detailed.J_T == result.best_J_T
    assert detailed.J_R == result.best_J_R
    np.testing.assert_array_equal(detailed.T_theoretical, result.T_theoretical)
    np.testing.assert_array_equal(detailed.R_theoretical, result.R_theoretical)


def test_elitism_carries_stored_results_without_extra_evaluations() -> None:
    configuration = replace(DEFAULT_CONFIGURATION, population_size=5, elitism=1)
    result = genetic_algorithm(seed=4, budget=13, configuration=configuration)

    assert result.n_initial_evaluations == 5
    assert result.n_offspring_evaluations == 8
    assert result.n_initial_evaluations + result.n_offspring_evaluations == result.n_evaluations


def test_crossover_and_mutation_clip_to_normalized_bounds() -> None:
    first = np.array([0.0, 1.0, 0.2, 0.8, 0.4, 0.6, 0.3, 0.7])
    second = 1.0 - first
    rng = np.random.default_rng(12)
    child_one, child_two = _simulated_binary_crossover(
        first,
        second,
        probability=1.0,
        distribution_index=1.0,
        rng=rng,
    )
    mutated = _polynomial_mutation(
        child_one,
        probability=1.0,
        distribution_index=1.0,
        rng=rng,
    )

    assert np.all((0.0 <= child_one) & (child_one <= 1.0))
    assert np.all((0.0 <= child_two) & (child_two <= 1.0))
    assert np.all((0.0 <= mutated) & (mutated <= 1.0))


def test_boundary_handling_keeps_strict_triangle_vertices_representable() -> None:
    normalized = _clip_normalized(np.array([1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0]))
    physical = to_physical(normalized)

    assert np.all((0.0 <= normalized) & (normalized <= 1.0))
    assert is_physically_valid(physical)


def test_ga_module_does_not_depend_on_differential_evolution_results() -> None:
    assert not hasattr(genetic_algorithm_module, "differential_evolution")


@pytest.mark.parametrize(
    "configuration",
    [
        replace(DEFAULT_CONFIGURATION, population_size=1),
        replace(DEFAULT_CONFIGURATION, tournament_size=0),
        replace(DEFAULT_CONFIGURATION, crossover_probability=-0.1),
        replace(DEFAULT_CONFIGURATION, crossover_probability=1.1),
        replace(DEFAULT_CONFIGURATION, mutation_probability=-0.1),
        replace(DEFAULT_CONFIGURATION, mutation_probability=1.1),
        replace(DEFAULT_CONFIGURATION, elitism=100),
    ],
)
def test_invalid_configuration_is_rejected(configuration: GeneticAlgorithmConfiguration) -> None:
    with pytest.raises(ValueError):
        genetic_algorithm(seed=1, budget=10, configuration=configuration)


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_budget_is_rejected(budget: int | float | bool) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        genetic_algorithm(seed=1, budget=budget)
