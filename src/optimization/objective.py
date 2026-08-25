"""Official joint transmission/reflection objective for Projeto 3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from experiments.data import D_NM, R_EXP, R_EXP_MAX, T_EXP, T_EXP_MAX
from optimization.constraints import ConstraintViolation, constraint_violations, validate_parameter_vector
from physics.simulator import SimulationResult, simulate


@dataclass(frozen=True, slots=True)
class ObjectiveResult:
    """Detailed result of one valid physical-model evaluation."""

    J: float
    J_T: float
    J_R: float
    p: NDArray[np.float64]
    T_theoretical: NDArray[np.float64]
    R_theoretical: NDArray[np.float64]
    valid_physics: bool


class InvalidParameterError(ValueError):
    """Raised when an objective candidate fails optimization-space constraints."""

    def __init__(self, violations: tuple[ConstraintViolation, ...]) -> None:
        self.violations = violations
        message = "Invalid physical parameter vector: " + " ".join(item.message for item in violations)
        super().__init__(message)


Simulator = Callable[[NDArray[np.float64], NDArray[np.float64]], SimulationResult]


def _validated_parameters(p: ArrayLike) -> NDArray[np.float64]:
    """Validate optimization constraints without invoking the physical model."""

    violations = constraint_violations(p)
    if violations:
        raise InvalidParameterError(violations)
    return validate_parameter_vector(p)


def _theoretical_response(values: ArrayLike, name: str) -> NDArray[np.float64]:
    """Validate one simulator response against the ten official data points."""

    response = np.asarray(values, dtype=np.float64)
    if response.ndim != 1 or response.shape != T_EXP.shape:
        raise ValueError(f"{name} must be a one-dimensional array with {T_EXP.size} elements.")
    if not np.all(np.isfinite(response)):
        raise ValueError(f"{name} must contain only finite values.")
    return response


def calculate_error_components(
    T_theoretical: ArrayLike,
    R_theoretical: ArrayLike,
) -> tuple[float, float, float]:
    """Calculate the official separate normalized sums ``J_T``, ``J_R``, and ``J``.

    The calculation is deliberately a sum, rather than a mean, and uses a
    distinct experimental maximum for transmission and reflection.
    """

    theoretical_t = _theoretical_response(T_theoretical, "T_theoretical")
    theoretical_r = _theoretical_response(R_theoretical, "R_theoretical")
    j_t = float(np.sum(((T_EXP - theoretical_t) / T_EXP_MAX) ** 2))
    j_r = float(np.sum(((R_EXP - theoretical_r) / R_EXP_MAX) ** 2))
    return j_t, j_r, j_t + j_r


def _evaluate_valid_parameters(parameters: NDArray[np.float64], simulator: Simulator) -> ObjectiveResult:
    """Run one simulator call for already validated parameters and form the result."""

    simulation = simulator(parameters, D_NM)
    theoretical_t = _theoretical_response(simulation.T, "simulator.T")
    theoretical_r = _theoretical_response(simulation.R, "simulator.R")
    j_t, j_r, j = calculate_error_components(theoretical_t, theoretical_r)
    return ObjectiveResult(
        J=j,
        J_T=j_t,
        J_R=j_r,
        p=parameters.copy(),
        T_theoretical=theoretical_t.copy(),
        R_theoretical=theoretical_r.copy(),
        valid_physics=True,
    )


def evaluate(p: ArrayLike) -> ObjectiveResult:
    """Return the complete official objective evaluation for a physically valid ``p``.

    Invalid candidates raise :class:`InvalidParameterError` before the
    simulator is called.
    """

    return _evaluate_valid_parameters(_validated_parameters(p), simulate)


def objective(p: ArrayLike) -> float:
    """Return only the official scalar objective ``J`` for future optimizers."""

    return evaluate(p).J


class ObjectiveEvaluator:
    """Stateful facade that counts physical simulator calls without global state."""

    def __init__(self, simulator: Simulator = simulate) -> None:
        self._simulator = simulator
        self._n_evaluations = 0

    @property
    def n_evaluations(self) -> int:
        """Number of effective calls made to the physical simulator."""

        return self._n_evaluations

    def evaluate(self, p: ArrayLike) -> ObjectiveResult:
        """Evaluate ``p`` and increment the counter only for a simulator call."""

        parameters = _validated_parameters(p)
        self._n_evaluations += 1
        return _evaluate_valid_parameters(parameters, self._simulator)

    def objective(self, p: ArrayLike) -> float:
        """Evaluate ``p`` through this counter and return only ``J``."""

        return self.evaluate(p).J
