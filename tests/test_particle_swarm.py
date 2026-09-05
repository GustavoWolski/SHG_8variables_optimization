"""Tests for exact-budget global-best PSO in Search-space version 2."""

from dataclasses import replace
import importlib
import inspect

import numpy as np
import pytest

from optimization.constraints import is_physically_valid
from optimization.objective import ObjectiveEvaluator, evaluate
particle_swarm_module = importlib.import_module("optimization.particle_swarm")
from optimization.particle_swarm import (
    DEFAULT_CONFIGURATION,
    ParticleSwarmConfiguration,
    _reflect_normalized,
    particle_swarm,
)


def test_same_seed_configuration_and_budget_are_reproducible() -> None:
    first = particle_swarm(seed=7, budget=43)
    second = particle_swarm(seed=7, budget=43)

    assert first.best_J == second.best_J
    assert first.best_J_T == second.best_J_T
    assert first.best_J_R == second.best_J_R
    np.testing.assert_array_equal(first.best_z, second.best_z)
    np.testing.assert_array_equal(first.best_p, second.best_p)
    assert first.convergence_history == second.convergence_history


def test_different_seeds_produce_different_trajectories() -> None:
    first = particle_swarm(seed=1, budget=43)
    second = particle_swarm(seed=2, budget=43)

    assert not np.array_equal(first.best_z, second.best_z)
    assert first.convergence_history != second.convergence_history


@pytest.mark.parametrize("budget", [3, 10, 23])
def test_budget_is_exact_for_smaller_and_non_multiple_swarm_budgets(budget: int) -> None:
    configuration = replace(DEFAULT_CONFIGURATION, swarm_size=10)
    result = particle_swarm(seed=5, budget=budget, configuration=configuration)

    assert result.n_evaluations == budget
    assert result.n_evaluations <= result.budget
    assert result.effective_swarm_size == min(configuration.swarm_size, budget)
    assert result.n_initial_evaluations == min(configuration.swarm_size, budget)
    assert result.n_particle_evaluations == budget - result.n_initial_evaluations
    assert len(result.convergence_history) == budget
    assert result.convergence_history[0].evaluation == 1
    assert result.convergence_history[-1].evaluation == budget


def test_reflective_normalized_boundary_handling_preserves_cube() -> None:
    positions = np.array([[-0.2, 1.2], [0.3, 0.7]], dtype=np.float64)
    velocities = np.array([[-0.2, 0.2], [0.1, -0.1]], dtype=np.float64)

    reflected_positions, reflected_velocities = _reflect_normalized(positions, velocities)

    np.testing.assert_allclose(reflected_positions, [[0.2, 0.8], [0.3, 0.7]])
    np.testing.assert_allclose(reflected_velocities, [[0.2, -0.2], [0.1, -0.1]])


def test_best_solution_coordinates_components_and_history_are_consistent() -> None:
    result = particle_swarm(seed=8, budget=137)
    history = np.asarray([record.best_J for record in result.convergence_history])
    detailed = evaluate(result.best_p)

    assert np.all((0.0 <= result.best_z) & (result.best_z <= 1.0))
    assert np.all((0.0 <= result.final_positions_z) & (result.final_positions_z <= 1.0))
    assert is_physically_valid(result.best_p)
    assert result.valid_physics
    assert result.best_J == result.best_J_T + result.best_J_R
    assert np.all(np.diff(history) <= 0.0)
    assert result.best_J == history[-1]
    assert detailed.J == result.best_J
    assert detailed.J_T == result.best_J_T
    assert detailed.J_R == result.best_J_R
    np.testing.assert_array_equal(detailed.T_theoretical, result.T_theoretical)
    np.testing.assert_array_equal(detailed.R_theoretical, result.R_theoretical)


def test_result_reconstruction_performs_no_extra_physical_evaluation(monkeypatch: pytest.MonkeyPatch) -> None:
    constructed: list[ObjectiveEvaluator] = []
    original = particle_swarm_module.ObjectiveEvaluator

    class TrackingEvaluator(original):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            constructed.append(self)

    monkeypatch.setattr(particle_swarm_module, "ObjectiveEvaluator", TrackingEvaluator)
    result = particle_swarm(seed=3, budget=17)

    assert len(constructed) == 1
    assert constructed[0].n_evaluations == result.n_evaluations == 17


def test_pso_module_has_no_internal_physical_model_logic() -> None:
    source = inspect.getsource(particle_swarm_module)

    assert "from physics" not in source
    assert "simulate(" not in source
    assert "to_physical" in source
    assert "ObjectiveEvaluator" in source


@pytest.mark.parametrize(
    "configuration",
    [
        replace(DEFAULT_CONFIGURATION, swarm_size=1),
        replace(DEFAULT_CONFIGURATION, inertia_weight=-0.1),
        replace(DEFAULT_CONFIGURATION, cognitive_coefficient=-0.1),
        replace(DEFAULT_CONFIGURATION, social_coefficient=float("nan")),
        replace(DEFAULT_CONFIGURATION, initial_velocity_limit=0.3),
        replace(DEFAULT_CONFIGURATION, velocity_limit=0.0),
        replace(DEFAULT_CONFIGURATION, boundary_handling="clip"),
        replace(DEFAULT_CONFIGURATION, topology="local_best"),
    ],
)
def test_invalid_configuration_is_rejected(configuration: ParticleSwarmConfiguration) -> None:
    with pytest.raises(ValueError):
        particle_swarm(seed=1, budget=10, configuration=configuration)


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_budget_is_rejected(budget: int | float | bool) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        particle_swarm(seed=1, budget=budget)
