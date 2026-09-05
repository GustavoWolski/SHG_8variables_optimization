"""Exact-budget real-coded Genetic Algorithm in the shared normalized space."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from optimization.constraints import is_physically_valid
from optimization.objective import DEFAULT_OBJECTIVE_WEIGHTS, ObjectiveEvaluator, ObjectiveResult, ObjectiveWeights
from optimization.parameterization import NORMALIZED_PARAMETER_COUNT, to_physical


NORMALIZED_BOUNDARY_MARGIN = 1e-8


@dataclass(frozen=True, slots=True)
class GeneticAlgorithmConfiguration:
    """Fixed, classical real-coded GA settings for the preliminary baseline."""

    population_size: int = 100
    tournament_size: int = 3
    crossover: str = "simulated_binary"
    crossover_probability: float = 0.9
    crossover_distribution_index: float = 15.0
    mutation: str = "polynomial"
    mutation_probability: float = 1.0 / NORMALIZED_PARAMETER_COUNT
    mutation_distribution_index: float = 20.0
    elitism: int = 1
    initialization: str = "uniform"
    boundary_handling: str = "clip"


DEFAULT_CONFIGURATION = GeneticAlgorithmConfiguration()


@dataclass(frozen=True, slots=True)
class GeneticAlgorithmConvergenceRecord:
    """Best-so-far state after one actual physical evaluation."""

    evaluation: int
    best_J: float
    best_J_unweighted: float
    best_J_weighted: float
    best_J_T: float
    best_J_R: float


@dataclass(frozen=True, slots=True)
class GeneticAlgorithmResult:
    """Complete result for one reproducible, serial, exact-budget GA run."""

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
    convergence_history: tuple[GeneticAlgorithmConvergenceRecord, ...]
    weights: ObjectiveWeights
    configuration: GeneticAlgorithmConfiguration
    effective_population_size: int
    n_initial_evaluations: int
    n_offspring_evaluations: int
    final_population_z: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class _Individual:
    """One already evaluated normalized candidate."""

    z: NDArray[np.float64]
    evaluation: ObjectiveResult


def _validate_budget(budget: int) -> int:
    if isinstance(budget, bool) or not isinstance(budget, Integral) or budget <= 0:
        raise ValueError("budget must be a positive integer number of physical evaluations.")
    return int(budget)


def _validate_configuration(configuration: GeneticAlgorithmConfiguration) -> None:
    if not isinstance(configuration.population_size, Integral) or configuration.population_size < 2:
        raise ValueError("population_size must be an integer of at least 2.")
    if not isinstance(configuration.tournament_size, Integral) or configuration.tournament_size < 1:
        raise ValueError("tournament_size must be a positive integer.")
    if configuration.crossover != "simulated_binary":
        raise ValueError("This baseline accepts only simulated_binary crossover.")
    if not 0.0 <= configuration.crossover_probability <= 1.0:
        raise ValueError("crossover_probability must be within [0, 1].")
    if configuration.crossover_distribution_index <= 0.0:
        raise ValueError("crossover_distribution_index must be positive.")
    if configuration.mutation != "polynomial":
        raise ValueError("This baseline accepts only polynomial mutation.")
    if not 0.0 <= configuration.mutation_probability <= 1.0:
        raise ValueError("mutation_probability must be within [0, 1].")
    if configuration.mutation_distribution_index <= 0.0:
        raise ValueError("mutation_distribution_index must be positive.")
    if not isinstance(configuration.elitism, Integral) or configuration.elitism < 1:
        raise ValueError("elitism must be a positive integer.")
    if configuration.elitism >= configuration.population_size:
        raise ValueError("elitism must be smaller than population_size.")
    if configuration.initialization != "uniform":
        raise ValueError("This baseline accepts only uniform initialization.")
    if configuration.boundary_handling != "clip":
        raise ValueError("This baseline accepts only clip boundary handling.")


def _clip_normalized(values: NDArray[np.float64]) -> NDArray[np.float64]:
    """Keep candidates inside the representable normalized unit cube interior.

    Polynomial mutation or SBX can land at, or sufficiently near, 0 or 1 for
    float64 rounding to collapse a strict-order triangle vertex. The GA clips
    to a named 1e-8 normalized margin. This is normalized-space boundary
    handling only; it is not physical repair.
    """

    return np.clip(
        values,
        NORMALIZED_BOUNDARY_MARGIN,
        1.0 - NORMALIZED_BOUNDARY_MARGIN,
    ).astype(np.float64, copy=False)


def _simulated_binary_crossover(
    first: NDArray[np.float64],
    second: NDArray[np.float64],
    *,
    probability: float,
    distribution_index: float,
    rng: np.random.Generator,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return SBX offspring, with clipping as normalized-space boundary handling."""

    if rng.random() >= probability:
        return first.copy(), second.copy()
    random_values = rng.random(first.size)
    beta = np.where(
        random_values <= 0.5,
        (2.0 * random_values) ** (1.0 / (distribution_index + 1.0)),
        (1.0 / (2.0 * (1.0 - random_values))) ** (1.0 / (distribution_index + 1.0)),
    )
    child_one = 0.5 * ((1.0 + beta) * first + (1.0 - beta) * second)
    child_two = 0.5 * ((1.0 - beta) * first + (1.0 + beta) * second)
    return _clip_normalized(child_one), _clip_normalized(child_two)


def _polynomial_mutation(
    candidate: NDArray[np.float64],
    *,
    probability: float,
    distribution_index: float,
    rng: np.random.Generator,
) -> NDArray[np.float64]:
    """Apply bounded polynomial mutation independently to normalized genes."""

    mutated = candidate.copy()
    selected = rng.random(mutated.size) < probability
    if not np.any(selected):
        return mutated
    values = mutated[selected]
    random_values = rng.random(values.size)
    lower_distance = values
    upper_distance = 1.0 - values
    inverse = 1.0 / (distribution_index + 1.0)
    delta = np.empty_like(values)
    lower_side = random_values <= 0.5
    if np.any(lower_side):
        xy = 1.0 - lower_distance[lower_side]
        val = 2.0 * random_values[lower_side] + (1.0 - 2.0 * random_values[lower_side]) * xy ** (
            distribution_index + 1.0
        )
        delta[lower_side] = val**inverse - 1.0
    if np.any(~lower_side):
        xy = 1.0 - upper_distance[~lower_side]
        val = (
            2.0 * (1.0 - random_values[~lower_side])
            + 2.0 * (random_values[~lower_side] - 0.5) * xy ** (distribution_index + 1.0)
        )
        delta[~lower_side] = 1.0 - val**inverse
    mutated[selected] = values + delta
    return _clip_normalized(mutated)


def _tournament_selection(
    population: list[_Individual],
    *,
    tournament_size: int,
    rng: np.random.Generator,
) -> _Individual:
    """Select the lowest-J sampled individual; ties retain its first draw."""

    indices = rng.integers(0, len(population), size=tournament_size)
    winner = population[int(indices[0])]
    for raw_index in indices[1:]:
        candidate = population[int(raw_index)]
        if candidate.evaluation.J_weighted < winner.evaluation.J_weighted:
            winner = candidate
    return winner


class _Tracker:
    """Centralize physical calls, first-tie policy and evaluation-based history."""

    def __init__(self, evaluator: ObjectiveEvaluator) -> None:
        self.evaluator = evaluator
        self.best_z: NDArray[np.float64] | None = None
        self.best_evaluation: ObjectiveResult | None = None
        self.history: list[GeneticAlgorithmConvergenceRecord] = []

    def evaluate(self, z: NDArray[np.float64]) -> _Individual:
        normalized = _clip_normalized(np.asarray(z, dtype=np.float64))
        try:
            physical = to_physical(normalized)
        except RuntimeError as error:
            raise RuntimeError(f"GA generated an unrepresentable normalized vector: {normalized!r}") from error
        current = self.evaluator.evaluate(physical)
        if self.best_evaluation is None or current.J_weighted < self.best_evaluation.J_weighted:
            self.best_z = normalized.copy()
            self.best_evaluation = current
        assert self.best_evaluation is not None
        self.history.append(
            GeneticAlgorithmConvergenceRecord(
                evaluation=self.evaluator.n_evaluations,
                best_J=self.best_evaluation.J_weighted,
                best_J_unweighted=self.best_evaluation.J,
                best_J_weighted=self.best_evaluation.J_weighted,
                best_J_T=self.best_evaluation.J_T,
                best_J_R=self.best_evaluation.J_R,
            )
        )
        return _Individual(normalized, current)


def _ranked(population: list[_Individual]) -> list[_Individual]:
    """Stable ordering preserves earlier encountered individuals on exact ties."""

    return sorted(population, key=lambda individual: individual.evaluation.J_weighted)


def genetic_algorithm(
    *,
    budget: int,
    seed: int,
    configuration: GeneticAlgorithmConfiguration = DEFAULT_CONFIGURATION,
    weights: ObjectiveWeights = DEFAULT_OBJECTIVE_WEIGHTS,
) -> GeneticAlgorithmResult:
    """Run a real-coded GA in z ∈ [0,1]^8 with an exact physical-call budget.

    Uniform initialization, tournament selection, simulated binary crossover,
    polynomial mutation and one-individual elitism operate only in normalized
    coordinates. Elites are carried with their stored objective results and
    are never re-evaluated. A final partial offspring batch is evaluated only
    up to the remaining budget. The strict best comparison retains the first
    solution observed on exact ties, and no final physical re-evaluation occurs.
    """

    evaluation_budget = _validate_budget(budget)
    _validate_configuration(configuration)
    rng = np.random.default_rng(seed)
    evaluator = ObjectiveEvaluator(weights=weights)
    tracker = _Tracker(evaluator)
    effective_population_size = min(int(configuration.population_size), evaluation_budget)

    start = perf_counter()
    population = [
        tracker.evaluate(rng.uniform(0.0, 1.0, size=NORMALIZED_PARAMETER_COUNT))
        for _ in range(effective_population_size)
    ]
    n_initial_evaluations = evaluator.n_evaluations

    while evaluator.n_evaluations < evaluation_budget and effective_population_size > 1:
        elite_count = min(int(configuration.elitism), effective_population_size - 1)
        elites = _ranked(population)[:elite_count]
        requested_offspring = min(
            effective_population_size - elite_count,
            evaluation_budget - evaluator.n_evaluations,
        )
        offspring: list[_Individual] = []
        while len(offspring) < requested_offspring:
            parent_one = _tournament_selection(
                population,
                tournament_size=int(configuration.tournament_size),
                rng=rng,
            )
            parent_two = _tournament_selection(
                population,
                tournament_size=int(configuration.tournament_size),
                rng=rng,
            )
            child_one, child_two = _simulated_binary_crossover(
                parent_one.z,
                parent_two.z,
                probability=configuration.crossover_probability,
                distribution_index=configuration.crossover_distribution_index,
                rng=rng,
            )
            for child in (child_one, child_two):
                if len(offspring) == requested_offspring:
                    break
                mutated = _polynomial_mutation(
                    child,
                    probability=configuration.mutation_probability,
                    distribution_index=configuration.mutation_distribution_index,
                    rng=rng,
                )
                offspring.append(tracker.evaluate(mutated))
        if len(offspring) < effective_population_size - elite_count:
            break
        population = elites + _ranked(offspring)[: effective_population_size - elite_count]

    runtime_s = perf_counter() - start
    if evaluator.n_evaluations != evaluation_budget:
        raise RuntimeError(f"GA stopped at {evaluator.n_evaluations}, expected {evaluation_budget}.")
    if tracker.best_z is None or tracker.best_evaluation is None:
        raise RuntimeError("GA made no physical objective evaluation.")
    best = tracker.best_evaluation
    if not is_physically_valid(best.p):
        raise RuntimeError("Internal GA error: best physical vector is invalid.")

    return GeneticAlgorithmResult(
        algorithm="Genetic Algorithm",
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
        effective_population_size=effective_population_size,
        n_initial_evaluations=n_initial_evaluations,
        n_offspring_evaluations=evaluator.n_evaluations - n_initial_evaluations,
        final_population_z=np.asarray([individual.z for individual in population], dtype=np.float64),
    )
