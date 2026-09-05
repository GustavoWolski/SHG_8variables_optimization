"""Exact-budget global-best Particle Swarm Optimization in normalized space.

The optimizer contains no physical-model logic. It evolves particles only in
``z ∈ [0, 1]^8`` and delegates the shared mapping and every physical call to
``to_physical`` and ``ObjectiveEvaluator``, respectively.
"""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from optimization.constraints import is_physically_valid
from optimization.objective import DEFAULT_OBJECTIVE_WEIGHTS, ObjectiveEvaluator, ObjectiveResult, ObjectiveWeights
from optimization.parameterization import NORMALIZED_PARAMETER_COUNT, to_physical


@dataclass(frozen=True, slots=True)
class ParticleSwarmConfiguration:
    """Fixed, classical global-best PSO configuration for the v2 baseline.

    The inertia and acceleration coefficients are the standard constricted-PSO
    values commonly used with global-best topology. Velocity clamping and
    reflection are applied only to normalized coordinates.
    """

    swarm_size: int = 100
    inertia_weight: float = 0.7298
    cognitive_coefficient: float = 1.49618
    social_coefficient: float = 1.49618
    velocity_initialization: str = "uniform"
    initial_velocity_limit: float = 0.1
    velocity_limit: float = 0.2
    boundary_handling: str = "reflect"
    topology: str = "global_best"


DEFAULT_CONFIGURATION = ParticleSwarmConfiguration()


@dataclass(frozen=True, slots=True)
class ParticleSwarmConvergenceRecord:
    """Global best after one effective physical evaluation."""

    evaluation: int
    best_J: float
    best_J_unweighted: float
    best_J_weighted: float
    best_J_T: float
    best_J_R: float


@dataclass(frozen=True, slots=True)
class ParticleSwarmResult:
    """Complete serial, reproducible, exact-budget global-best PSO result."""

    algorithm: str
    seed: int
    budget: int
    n_evaluations: int
    runtime_s: float
    best_J: float
    best_J_unweighted: float
    best_J_weighted: float
    best_J_T: float
    best_J_R: float
    best_z: NDArray[np.float64]
    best_p: NDArray[np.float64]
    T_theoretical: NDArray[np.float64]
    R_theoretical: NDArray[np.float64]
    valid_physics: bool
    convergence_history: tuple[ParticleSwarmConvergenceRecord, ...]
    weights: ObjectiveWeights
    configuration: ParticleSwarmConfiguration
    effective_swarm_size: int
    n_initial_evaluations: int
    n_particle_evaluations: int
    final_positions_z: NDArray[np.float64]
    final_velocities: NDArray[np.float64]


def _validate_budget(budget: int) -> int:
    if isinstance(budget, bool) or not isinstance(budget, Integral) or budget <= 0:
        raise ValueError("budget must be a positive integer number of physical evaluations.")
    return int(budget)


def _validate_configuration(configuration: ParticleSwarmConfiguration) -> None:
    if not isinstance(configuration.swarm_size, Integral) or configuration.swarm_size < 2:
        raise ValueError("swarm_size must be an integer of at least 2.")
    for name, value in (
        ("inertia_weight", configuration.inertia_weight),
        ("cognitive_coefficient", configuration.cognitive_coefficient),
        ("social_coefficient", configuration.social_coefficient),
        ("initial_velocity_limit", configuration.initial_velocity_limit),
        ("velocity_limit", configuration.velocity_limit),
    ):
        if not np.isfinite(value) or value < 0.0:
            raise ValueError(f"{name} must be a finite non-negative value.")
    if configuration.velocity_initialization != "uniform":
        raise ValueError("This baseline accepts only uniform velocity initialization.")
    if configuration.initial_velocity_limit > configuration.velocity_limit:
        raise ValueError("initial_velocity_limit cannot exceed velocity_limit.")
    if configuration.velocity_limit <= 0.0:
        raise ValueError("velocity_limit must be positive.")
    if configuration.boundary_handling != "reflect":
        raise ValueError("This baseline accepts only reflect boundary handling.")
    if configuration.topology != "global_best":
        raise ValueError("This baseline accepts only global_best topology.")


def _reflect_normalized(
    positions: NDArray[np.float64], velocities: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Reflect candidates at normalized-space cube faces without physical repair."""

    reflected_positions = np.asarray(positions, dtype=np.float64).copy()
    reflected_velocities = np.asarray(velocities, dtype=np.float64).copy()
    lower = reflected_positions < 0.0
    if np.any(lower):
        reflected_positions[lower] = -reflected_positions[lower]
        reflected_velocities[lower] = -reflected_velocities[lower]
    upper = reflected_positions > 1.0
    if np.any(upper):
        reflected_positions[upper] = 2.0 - reflected_positions[upper]
        reflected_velocities[upper] = -reflected_velocities[upper]
    if np.any(reflected_positions < 0.0) or np.any(reflected_positions > 1.0):
        raise RuntimeError("Normalized reflection failed to return positions to [0, 1].")
    return reflected_positions, reflected_velocities


class _Tracker:
    """Store global best and the evaluation-indexed history without extra calls."""

    def __init__(self, evaluator: ObjectiveEvaluator) -> None:
        self.evaluator = evaluator
        self.best_z: NDArray[np.float64] | None = None
        self.best_evaluation: ObjectiveResult | None = None
        self.history: list[ParticleSwarmConvergenceRecord] = []

    def evaluate(self, z: NDArray[np.float64]) -> ObjectiveResult:
        normalized = np.asarray(z, dtype=np.float64)
        physical = to_physical(normalized)
        current = self.evaluator.evaluate(physical)
        if self.best_evaluation is None or current.J_weighted < self.best_evaluation.J_weighted:
            self.best_z = normalized.copy()
            self.best_evaluation = current
        assert self.best_evaluation is not None
        self.history.append(
            ParticleSwarmConvergenceRecord(
                evaluation=self.evaluator.n_evaluations,
                best_J=self.best_evaluation.J_weighted,
                best_J_unweighted=self.best_evaluation.J,
                best_J_weighted=self.best_evaluation.J_weighted,
                best_J_T=self.best_evaluation.J_T,
                best_J_R=self.best_evaluation.J_R,
            )
        )
        return current


def particle_swarm(
    *,
    budget: int,
    seed: int,
    configuration: ParticleSwarmConfiguration = DEFAULT_CONFIGURATION,
    weights: ObjectiveWeights = DEFAULT_OBJECTIVE_WEIGHTS,
) -> ParticleSwarmResult:
    """Run normalized global-best PSO with an exact physical-call budget.

    The initial swarm consumes the budget. Full updates evaluate every particle;
    the final update evaluates only the remaining prefix when the budget is not
    divisible by the effective swarm size. The cached global-best evaluation is
    copied into the result, so result reconstruction never performs a physical
    evaluation.
    """

    evaluation_budget = _validate_budget(budget)
    _validate_configuration(configuration)
    rng = np.random.default_rng(seed)
    evaluator = ObjectiveEvaluator(weights=weights)
    tracker = _Tracker(evaluator)
    effective_swarm_size = min(int(configuration.swarm_size), evaluation_budget)

    start = perf_counter()
    positions = rng.uniform(0.0, 1.0, size=(effective_swarm_size, NORMALIZED_PARAMETER_COUNT))
    velocities = rng.uniform(
        -configuration.initial_velocity_limit,
        configuration.initial_velocity_limit,
        size=(effective_swarm_size, NORMALIZED_PARAMETER_COUNT),
    )
    personal_best_positions = positions.copy()
    personal_best_values = np.full(effective_swarm_size, np.inf, dtype=np.float64)

    for index in range(effective_swarm_size):
        current = tracker.evaluate(positions[index])
        personal_best_values[index] = current.J_weighted
    n_initial_evaluations = evaluator.n_evaluations
    assert tracker.best_z is not None

    while evaluator.n_evaluations < evaluation_budget:
        random_cognitive = rng.random(size=positions.shape)
        random_social = rng.random(size=positions.shape)
        velocities = (
            configuration.inertia_weight * velocities
            + configuration.cognitive_coefficient * random_cognitive * (personal_best_positions - positions)
            + configuration.social_coefficient * random_social * (tracker.best_z - positions)
        )
        velocities = np.clip(velocities, -configuration.velocity_limit, configuration.velocity_limit)
        positions, velocities = _reflect_normalized(positions + velocities, velocities)

        n_to_evaluate = min(effective_swarm_size, evaluation_budget - evaluator.n_evaluations)
        for index in range(n_to_evaluate):
            current = tracker.evaluate(positions[index])
            if current.J_weighted < personal_best_values[index]:
                personal_best_values[index] = current.J_weighted
                personal_best_positions[index] = positions[index].copy()

    runtime_s = perf_counter() - start
    if evaluator.n_evaluations != evaluation_budget:
        raise RuntimeError(f"PSO stopped at {evaluator.n_evaluations}, expected {evaluation_budget}.")
    if tracker.best_z is None or tracker.best_evaluation is None:
        raise RuntimeError("PSO made no physical objective evaluation.")
    best = tracker.best_evaluation
    if not is_physically_valid(best.p):
        raise RuntimeError("Internal PSO error: best physical vector is invalid.")

    return ParticleSwarmResult(
        algorithm="Particle Swarm Optimization",
        seed=seed,
        budget=evaluation_budget,
        n_evaluations=evaluator.n_evaluations,
        runtime_s=runtime_s,
        best_J=best.J_weighted,
        best_J_unweighted=best.J,
        best_J_weighted=best.J_weighted,
        best_J_T=best.J_T,
        best_J_R=best.J_R,
        best_z=tracker.best_z.copy(),
        best_p=best.p.copy(),
        T_theoretical=best.T_theoretical.copy(),
        R_theoretical=best.R_theoretical.copy(),
        valid_physics=best.valid_physics,
        convergence_history=tuple(tracker.history),
        weights=weights,
        configuration=configuration,
        effective_swarm_size=effective_swarm_size,
        n_initial_evaluations=n_initial_evaluations,
        n_particle_evaluations=evaluator.n_evaluations - n_initial_evaluations,
        final_positions_z=positions.copy(),
        final_velocities=velocities.copy(),
    )
