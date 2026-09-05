"""Shared weighted-objective behavior for all existing search methods."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pytest

from optimization.differential_evolution import differential_evolution
from optimization.genetic_algorithm import genetic_algorithm
from optimization.objective import ObjectiveWeights, evaluate
from optimization.particle_swarm import particle_swarm
from optimization.random_search import random_search


WeightedRunner = Callable[..., object]


@pytest.mark.parametrize(
    "runner",
    [random_search, differential_evolution, genetic_algorithm, particle_swarm],
    ids=["random_search", "differential_evolution", "genetic_algorithm", "particle_swarm"],
)
def test_algorithms_optimize_and_retain_weighted_and_unweighted_metrics(runner: WeightedRunner) -> None:
    weights = ObjectiveWeights(transmission=1.0, reflection=5.0)
    result = runner(seed=4, budget=31, weights=weights)
    history = np.asarray([record.best_J for record in result.convergence_history])
    detailed = evaluate(result.best_p, weights=weights)

    assert result.n_evaluations == 31
    assert result.best_J == result.best_J_weighted
    assert result.best_J_unweighted == result.best_J_T + result.best_J_R
    assert result.best_J_weighted == result.best_J_T + 5.0 * result.best_J_R
    assert result.best_J == history[-1]
    assert np.all(np.diff(history) <= 0.0)
    assert detailed.J == result.best_J_unweighted
    assert detailed.J_weighted == result.best_J_weighted
