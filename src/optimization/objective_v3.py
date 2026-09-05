"""Unweighted V3 objective: the unchanged scientific definition J = J_T + J_R."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from experiments.data import D_NM
from optimization.constraints import ConstraintViolation
from optimization.constraints_v3 import constraint_violations_v3, validate_parameter_vector_v3
from optimization.objective import calculate_error_components
from physics.simulator_v3 import SimulationResultV3, simulate_v3


@dataclass(frozen=True, slots=True)
class ObjectiveResultV3:
    """Detailed output of one valid V3 physical-model evaluation."""

    J: float
    J_T: float
    J_R: float
    p: NDArray[np.float64]
    T_theoretical: NDArray[np.float64]
    R_theoretical: NDArray[np.float64]
    valid_physics: bool


class InvalidParameterErrorV3(ValueError):
    """Raised when a V3 candidate fails the V3 vector or box constraints."""

    def __init__(self, violations: tuple[ConstraintViolation, ...]) -> None:
        self.violations = violations
        super().__init__("Invalid V3 physical parameter vector: " + " ".join(item.message for item in violations))


SimulatorV3 = Callable[[NDArray[np.float64], NDArray[np.float64]], SimulationResultV3]


def _validated_parameters_v3(p: ArrayLike) -> NDArray[np.float64]:
    """Validate V3 constraints before a call to the physical simulator."""

    violations = constraint_violations_v3(p)
    if violations:
        raise InvalidParameterErrorV3(violations)
    return validate_parameter_vector_v3(p)


def _evaluate_valid_parameters_v3(
    parameters: NDArray[np.float64], simulator: SimulatorV3
) -> ObjectiveResultV3:
    """Call a V3 simulator and calculate the unchanged separate error sums."""

    simulation = simulator(parameters, D_NM)
    j_t, j_r, j = calculate_error_components(simulation.T, simulation.R)
    return ObjectiveResultV3(
        J=j,
        J_T=j_t,
        J_R=j_r,
        p=parameters.copy(),
        T_theoretical=simulation.T.copy(),
        R_theoretical=simulation.R.copy(),
        valid_physics=True,
    )


def evaluate_v3(p: ArrayLike) -> ObjectiveResultV3:
    """Return the full V3 evaluation under exactly ``J = J_T + J_R``."""

    return _evaluate_valid_parameters_v3(_validated_parameters_v3(p), simulate_v3)


def objective_v3(p: ArrayLike) -> float:
    """Return V3's unweighted scientific objective."""

    return evaluate_v3(p).J


class ObjectiveEvaluatorV3:
    """V3 facade that counts effective physical simulator calls."""

    def __init__(self, simulator: SimulatorV3 = simulate_v3) -> None:
        self._simulator = simulator
        self._n_evaluations = 0

    @property
    def n_evaluations(self) -> int:
        """Number of effective V3 simulator calls."""

        return self._n_evaluations

    def evaluate(self, p: ArrayLike) -> ObjectiveResultV3:
        """Evaluate a valid V3 vector and increment only for a simulator call."""

        parameters = _validated_parameters_v3(p)
        self._n_evaluations += 1
        return _evaluate_valid_parameters_v3(parameters, self._simulator)

    def objective(self, p: ArrayLike) -> float:
        """Evaluate and return V3's scalar J."""

        return self.evaluate(p).J
