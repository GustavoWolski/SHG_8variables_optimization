"""Reproducible Random Search baseline in the shared normalized search space."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

from optimization.constraints import is_physically_valid
from optimization.objective import DEFAULT_OBJECTIVE_WEIGHTS, ObjectiveEvaluator, ObjectiveResult, ObjectiveWeights
from optimization.parameterization import to_physical


@dataclass(frozen=True, slots=True)
class ConvergenceRecord:
    """Best-so-far objective components after one physical evaluation."""

    evaluation: int
    best_J: float
    best_J_unweighted: float
    best_J_weighted: float
    best_J_T: float
    best_J_R: float


@dataclass(frozen=True, slots=True)
class RandomSearchResult:
    """Complete, reusable result from one serial Random Search execution."""

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
    convergence_history: tuple[ConvergenceRecord, ...]
    weights: ObjectiveWeights


def _validate_budget(budget: int) -> int:
    """Accept only positive integral budgets, measured in physical evaluations."""

    if isinstance(budget, bool) or not isinstance(budget, Integral) or budget <= 0:
        raise ValueError("budget must be a positive integer number of physical evaluations.")
    return int(budget)


def _result_from_best(
    *,
    seed: int,
    budget: int,
    evaluator: ObjectiveEvaluator,
    runtime_s: float,
    best_z: NDArray[np.float64],
    best_evaluation: ObjectiveResult,
    history: list[ConvergenceRecord],
    weights: ObjectiveWeights,
) -> RandomSearchResult:
    """Build an immutable result after asserting the official physical count."""

    if evaluator.n_evaluations != budget:
        raise RuntimeError(f"Random Search stopped at {evaluator.n_evaluations}, expected budget {budget}.")
    if not is_physically_valid(best_evaluation.p):
        raise RuntimeError("Internal Random Search error: best physical vector is invalid.")
    return RandomSearchResult(
        algorithm="Random Search",
        seed=seed,
        budget=budget,
        n_evaluations=evaluator.n_evaluations,
        runtime_s=runtime_s,
        best_J=best_evaluation.J_weighted,
        best_J_unweighted=best_evaluation.J,
        best_J_weighted=best_evaluation.J_weighted,
        best_J_T=best_evaluation.J_T,
        best_J_R=best_evaluation.J_R,
        best_z=best_z.copy(),
        best_p=best_evaluation.p.copy(),
        T_theoretical=best_evaluation.T_theoretical.copy(),
        R_theoretical=best_evaluation.R_theoretical.copy(),
        valid_physics=best_evaluation.valid_physics,
        convergence_history=tuple(history),
        weights=weights,
    )


def random_search(
    *, budget: int, seed: int, weights: ObjectiveWeights = DEFAULT_OBJECTIVE_WEIGHTS
) -> RandomSearchResult:
    """Run serial uniform Random Search in ``z ∈ [0, 1]^8``.

    Every candidate is mapped through :func:`to_physical` before evaluation,
    so no repair, rejection, penalty, or additional constraint handling is
    applied. A strict ``<`` comparison retains the first candidate when two
    objective values are exactly tied.
    """

    evaluation_budget = _validate_budget(budget)
    rng = np.random.default_rng(seed)
    evaluator = ObjectiveEvaluator(weights=weights)
    history: list[ConvergenceRecord] = []
    best_z: NDArray[np.float64] | None = None
    best_evaluation: ObjectiveResult | None = None

    start = perf_counter()
    while evaluator.n_evaluations < evaluation_budget:
        normalized = rng.uniform(0.0, 1.0, size=8)
        physical = to_physical(normalized)
        current = evaluator.evaluate(physical)
        if best_evaluation is None or current.J_weighted < best_evaluation.J_weighted:
            best_z = normalized.copy()
            best_evaluation = current
        assert best_evaluation is not None
        history.append(
            ConvergenceRecord(
                evaluation=evaluator.n_evaluations,
                best_J=best_evaluation.J_weighted,
                best_J_unweighted=best_evaluation.J,
                best_J_weighted=best_evaluation.J_weighted,
                best_J_T=best_evaluation.J_T,
                best_J_R=best_evaluation.J_R,
            )
        )
    runtime_s = perf_counter() - start

    assert best_z is not None
    assert best_evaluation is not None
    return _result_from_best(
        seed=seed,
        budget=evaluation_budget,
        evaluator=evaluator,
        runtime_s=runtime_s,
        best_z=best_z,
        best_evaluation=best_evaluation,
        history=history,
        weights=weights,
    )
