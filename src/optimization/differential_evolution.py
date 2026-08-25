"""SciPy Differential Evolution baseline in the shared normalized search space."""

from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from time import perf_counter

import numpy as np
from numpy.typing import NDArray
from scipy.optimize._differentialevolution import DifferentialEvolutionSolver

from optimization.objective import ObjectiveEvaluator, ObjectiveResult
from optimization.parameterization import NORMALIZED_PARAMETER_COUNT, to_physical


NORMALIZED_BOUNDS: tuple[tuple[float, float], ...] = ((0.0, 1.0),) * NORMALIZED_PARAMETER_COUNT


@dataclass(frozen=True, slots=True)
class DifferentialEvolutionConfiguration:
    """Baseline DE settings shared by smoke and preliminary experiments."""

    strategy: str = "best1bin"
    popsize: int = 15
    mutation: tuple[float, float] = (0.5, 1.0)
    recombination: float = 0.7
    init: str = "latinhypercube"
    updating: str = "deferred"
    tol: float = 0.0
    atol: float = 0.0
    polish: bool = False


DEFAULT_CONFIGURATION = DifferentialEvolutionConfiguration()


@dataclass(frozen=True, slots=True)
class DifferentialEvolutionConvergenceRecord:
    """Best-so-far state after an individual physical objective evaluation."""

    evaluation: int
    best_J: float
    best_J_T: float
    best_J_R: float


@dataclass(frozen=True, slots=True)
class DifferentialEvolutionResult:
    """Complete result from one exact-budget serial Differential Evolution run."""

    algorithm: str
    seed: int
    budget: int
    n_evaluations: int
    runtime_s: float
    best_J: float
    best_J_T: float
    best_J_R: float
    best_z: NDArray[np.float64]
    best_p: NDArray[np.float64]
    T_theoretical: NDArray[np.float64]
    R_theoretical: NDArray[np.float64]
    valid_physics: bool
    convergence_history: tuple[DifferentialEvolutionConvergenceRecord, ...]
    configuration: DifferentialEvolutionConfiguration
    scipy_maxfun: int
    scipy_maxiter: int
    scipy_nfev: int


def _validate_budget(budget: int) -> int:
    """Accept only a positive number of physical objective evaluations."""

    if isinstance(budget, bool) or not isinstance(budget, Integral) or budget <= 0:
        raise ValueError("budget must be a positive integer number of physical evaluations.")
    return int(budget)


def _validate_configuration(configuration: DifferentialEvolutionConfiguration) -> None:
    """Validate the baseline settings required for exact serial evaluation accounting."""

    if configuration.strategy != "best1bin":
        raise ValueError("This baseline accepts only the documented 'best1bin' strategy.")
    if not isinstance(configuration.popsize, Integral) or configuration.popsize <= 0:
        raise ValueError("popsize must be a positive integer.")
    if len(configuration.mutation) != 2 or not 0.0 <= configuration.mutation[0] <= configuration.mutation[1] <= 2.0:
        raise ValueError("mutation must be an ordered pair within [0, 2].")
    if not 0.0 <= configuration.recombination <= 1.0:
        raise ValueError("recombination must be within [0, 1].")
    if configuration.init != "latinhypercube":
        raise ValueError("This baseline accepts only 'latinhypercube' initialization.")
    if configuration.updating != "deferred":
        raise ValueError("Exact maxfun accounting requires serial 'deferred' updating.")
    if configuration.tol != 0.0 or configuration.atol != 0.0:
        raise ValueError("This baseline fixes tol=0 and atol=0; stopping is controlled by maxfun.")
    if configuration.polish:
        raise ValueError("polish must be False for the pure DE comparison.")


class _TrackedNormalizedObjective:
    """Track exact physical calls while exposing the scalar objective SciPy expects."""

    def __init__(self, evaluator: ObjectiveEvaluator) -> None:
        self.evaluator = evaluator
        self.best_z: NDArray[np.float64] | None = None
        self.best_evaluation: ObjectiveResult | None = None
        self.history: list[DifferentialEvolutionConvergenceRecord] = []

    def __call__(self, normalized: NDArray[np.float64]) -> float:
        physical = to_physical(normalized)
        current = self.evaluator.evaluate(physical)
        if self.best_evaluation is None or current.J < self.best_evaluation.J:
            self.best_z = np.asarray(normalized, dtype=np.float64).copy()
            self.best_evaluation = current
        assert self.best_evaluation is not None
        self.history.append(
            DifferentialEvolutionConvergenceRecord(
                evaluation=self.evaluator.n_evaluations,
                best_J=self.best_evaluation.J,
                best_J_T=self.best_evaluation.J_T,
                best_J_R=self.best_evaluation.J_R,
            )
        )
        return current.J


def differential_evolution(
    *,
    budget: int,
    seed: int,
    configuration: DifferentialEvolutionConfiguration = DEFAULT_CONFIGURATION,
) -> DifferentialEvolutionResult:
    """Run pure DE in ``z ∈ [0, 1]^8`` with an exact physical-evaluation budget.

    SciPy's public convenience function does not expose ``maxfun``. This uses
    its DE solver with ``maxfun=budget`` and serial deferred updates, then
    advances it only until :class:`ObjectiveEvaluator` reaches the budget.
    The final partial generation is therefore evaluated only up to the
    remaining physical calls. ``polish`` is always disabled and no final
    re-evaluation is performed: the best detailed result is retained by the
    tracked objective.
    """

    evaluation_budget = _validate_budget(budget)
    _validate_configuration(configuration)
    evaluator = ObjectiveEvaluator()
    tracked_objective = _TrackedNormalizedObjective(evaluator)
    solver = DifferentialEvolutionSolver(
        tracked_objective,
        NORMALIZED_BOUNDS,
        strategy=configuration.strategy,
        maxiter=evaluation_budget,
        popsize=int(configuration.popsize),
        tol=configuration.tol,
        mutation=configuration.mutation,
        recombination=configuration.recombination,
        rng=np.random.default_rng(seed),
        maxfun=evaluation_budget,
        disp=False,
        polish=configuration.polish,
        init=configuration.init,
        atol=configuration.atol,
        updating=configuration.updating,
        workers=1,
        vectorized=False,
    )

    start = perf_counter()
    while evaluator.n_evaluations < evaluation_budget:
        try:
            next(solver)
        except StopIteration:
            break
    runtime_s = perf_counter() - start

    if evaluator.n_evaluations != evaluation_budget:
        raise RuntimeError(
            "SciPy DE stopped before the requested physical budget: "
            f"{evaluator.n_evaluations} != {evaluation_budget}."
        )
    if solver._nfev != evaluation_budget:
        raise RuntimeError(f"SciPy nfev mismatch: {solver._nfev} != {evaluation_budget}.")
    if tracked_objective.best_z is None or tracked_objective.best_evaluation is None:
        raise RuntimeError("SciPy DE made no physical objective evaluation.")

    best = tracked_objective.best_evaluation
    return DifferentialEvolutionResult(
        algorithm="Differential Evolution",
        seed=seed,
        budget=evaluation_budget,
        n_evaluations=evaluator.n_evaluations,
        runtime_s=runtime_s,
        best_J=best.J,
        best_J_T=best.J_T,
        best_J_R=best.J_R,
        best_z=tracked_objective.best_z.copy(),
        best_p=best.p.copy(),
        T_theoretical=best.T_theoretical.copy(),
        R_theoretical=best.R_theoretical.copy(),
        valid_physics=best.valid_physics,
        convergence_history=tuple(tracked_objective.history),
        configuration=configuration,
        scipy_maxfun=evaluation_budget,
        scipy_maxiter=evaluation_budget,
        scipy_nfev=int(solver._nfev),
    )
