"""Reusable one-at-a-time sensitivity sweeps for the official objective."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from optimization.constraints import PARAMETER_DEFINITIONS, validate_physical_parameters
from optimization.objective import ObjectiveResult, evaluate


FloatArray = NDArray[np.float64]
SweepScale = Literal["local", "global"]
EvaluationFunction = Callable[[ArrayLike], ObjectiveResult]


@dataclass(frozen=True, slots=True)
class SensitivitySweep:
    """Objective components evaluated while changing exactly one coordinate."""

    parameter_index: int
    parameter_name: str
    scale: SweepScale
    values: FloatArray
    J: FloatArray
    J_T: FloatArray
    J_R: FloatArray

    @property
    def n_evaluations(self) -> int:
        return int(self.values.size)


def sensitivity_grid(
    p_reference: ArrayLike,
    parameter_index: int,
    scale: SweepScale,
    *,
    point_count: int = 101,
    local_fraction_of_bound_span: float = 0.10,
) -> FloatArray:
    """Build an inclusive uniform global or bound-clipped local grid."""

    parameters = validate_physical_parameters(p_reference)
    if not 0 <= parameter_index < len(PARAMETER_DEFINITIONS):
        raise IndexError("parameter_index is outside the physical parameter vector.")
    if point_count < 3:
        raise ValueError("point_count must be at least 3.")
    if not 0.0 < local_fraction_of_bound_span <= 0.5:
        raise ValueError("local_fraction_of_bound_span must satisfy 0 < fraction <= 0.5.")
    if scale not in {"local", "global"}:
        raise ValueError("scale must be 'local' or 'global'.")

    definition = PARAMETER_DEFINITIONS[parameter_index]
    lower = definition.lower
    upper = definition.upper
    if scale == "global":
        return np.linspace(lower, upper, point_count, dtype=np.float64)

    reference = float(parameters[parameter_index])
    half_width = local_fraction_of_bound_span * (upper - lower)
    lower = max(lower, reference - half_width)
    upper = min(upper, reference + half_width)
    left_span = reference - lower
    right_span = upper - reference
    if left_span == 0.0:
        return np.linspace(reference, upper, point_count, dtype=np.float64)
    if right_span == 0.0:
        return np.linspace(lower, reference, point_count, dtype=np.float64)

    interval_count = point_count - 1
    left_intervals = int(round(interval_count * left_span / (left_span + right_span)))
    left_intervals = min(max(left_intervals, 1), interval_count - 1)
    right_intervals = interval_count - left_intervals
    left = np.linspace(lower, reference, left_intervals + 1, dtype=np.float64)
    right = np.linspace(reference, upper, right_intervals + 1, dtype=np.float64)
    return np.concatenate((left, right[1:]))


def sweep_parameter(
    p_reference: ArrayLike,
    parameter_index: int,
    scale: SweepScale,
    *,
    point_count: int = 101,
    local_fraction_of_bound_span: float = 0.10,
    evaluator: EvaluationFunction = evaluate,
) -> SensitivitySweep:
    """Vary one parameter and keep every other coordinate fixed."""

    parameters = validate_physical_parameters(p_reference)
    values = sensitivity_grid(
        parameters,
        parameter_index,
        scale,
        point_count=point_count,
        local_fraction_of_bound_span=local_fraction_of_bound_span,
    )
    total = np.empty(values.size, dtype=np.float64)
    transmission = np.empty(values.size, dtype=np.float64)
    reflection = np.empty(values.size, dtype=np.float64)
    for index, value in enumerate(values):
        candidate = parameters.copy()
        candidate[parameter_index] = value
        result = evaluator(candidate)
        total[index] = result.J
        transmission[index] = result.J_T
        reflection[index] = result.J_R
    definition = PARAMETER_DEFINITIONS[parameter_index]
    return SensitivitySweep(
        parameter_index=parameter_index,
        parameter_name=definition.name,
        scale=scale,
        values=values,
        J=total,
        J_T=transmission,
        J_R=reflection,
    )


def approximate_curvature(sweep: SensitivitySweep, reference_value: float) -> float:
    """Estimate d²J/dx² with a quadratic fit to the three nearest local points."""

    if sweep.values.size < 3:
        return float("nan")
    nearest = np.argsort(np.abs(sweep.values - reference_value))[:3]
    nearest.sort()
    x = sweep.values[nearest]
    y = sweep.J[nearest]
    if np.unique(x).size != 3:
        return float("nan")
    coefficient = np.polyfit(x, y, deg=2)[0]
    return float(2.0 * coefficient)


def threshold_region_width(
    sweep: SensitivitySweep,
    reference_value: float,
    reference_J: float,
    relative_increase: float,
) -> float:
    """Approximate the contiguous sampled valley width around the reference."""

    if relative_increase < 0.0:
        raise ValueError("relative_increase must be non-negative.")
    threshold = reference_J * (1.0 + relative_increase)
    inside = sweep.J <= threshold
    anchor = int(np.argmin(np.abs(sweep.values - reference_value)))
    if not inside[anchor]:
        qualifying = np.flatnonzero(inside)
        if qualifying.size == 0:
            return 0.0
        anchor = int(qualifying[np.argmin(np.abs(sweep.values[qualifying] - reference_value))])
    left = anchor
    right = anchor
    while left > 0 and inside[left - 1]:
        left -= 1
    while right + 1 < inside.size and inside[right + 1]:
        right += 1

    left_boundary = float(sweep.values[left])
    if left > 0:
        x_out, x_in = sweep.values[left - 1], sweep.values[left]
        j_out, j_in = sweep.J[left - 1], sweep.J[left]
        if j_out != j_in:
            left_boundary = float(x_out + (threshold - j_out) * (x_in - x_out) / (j_in - j_out))

    right_boundary = float(sweep.values[right])
    if right + 1 < inside.size:
        x_in, x_out = sweep.values[right], sweep.values[right + 1]
        j_in, j_out = sweep.J[right], sweep.J[right + 1]
        if j_out != j_in:
            right_boundary = float(x_in + (threshold - j_in) * (x_out - x_in) / (j_out - j_in))
    return max(0.0, right_boundary - left_boundary)


def local_minimum_indices(sweep: SensitivitySweep) -> NDArray[np.int64]:
    """Return grid-resolved local minima, including a lower endpoint minimum."""

    values = sweep.J
    minima: list[int] = []
    if values[0] < values[1]:
        minima.append(0)
    minima.extend(
        index
        for index in range(1, values.size - 1)
        if values[index] <= values[index - 1]
        and values[index] <= values[index + 1]
        and (values[index] < values[index - 1] or values[index] < values[index + 1])
    )
    if values[-1] < values[-2]:
        minima.append(values.size - 1)
    return np.asarray(minima, dtype=np.int64)
