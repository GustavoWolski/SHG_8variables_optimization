"""Run the controlled Search-space v2 weighted-reflection screening study."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from optimization.differential_evolution import differential_evolution  # noqa: E402
from optimization.genetic_algorithm import genetic_algorithm  # noqa: E402
from optimization.objective import ObjectiveWeights  # noqa: E402
from optimization.particle_swarm import particle_swarm  # noqa: E402
from optimization.random_search import random_search  # noqa: E402


DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_WEIGHTS = (1.0, 2.0, 5.0, 10.0)
DEFAULT_BUDGET = 50_000
SEARCH_SPACE_VERSION = 2

AlgorithmRunner = Callable[..., object]
ALGORITHMS: tuple[tuple[str, AlgorithmRunner], ...] = (
    ("random_search", random_search),
    ("differential_evolution", differential_evolution),
    ("genetic_algorithm", genetic_algorithm),
    ("particle_swarm", particle_swarm),
)


def _weight_label(weight: float) -> str:
    return f"wR_{weight:g}".replace(".", "p")


def _configuration_json(result: object) -> str:
    configuration = getattr(result, "configuration", None)
    if configuration is None:
        return "{}"
    return json.dumps(asdict(configuration) if is_dataclass(configuration) else configuration)


def _write_runs(path: Path, results: Sequence[object], weights: ObjectiveWeights) -> None:
    fields = [
        "algorithm", "search_space_version", "w_T", "w_R", "seed", "budget", "n_evaluations", "runtime_s",
        "J_T", "J_R", "J_unweighted", "J_weighted", "best_z", "best_p", "T_theoretical", "R_theoretical",
        "valid_physics", "configuration",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "algorithm": result.algorithm,
                    "search_space_version": SEARCH_SPACE_VERSION,
                    "w_T": f"{weights.transmission:.17g}",
                    "w_R": f"{weights.reflection:.17g}",
                    "seed": result.seed,
                    "budget": result.budget,
                    "n_evaluations": result.n_evaluations,
                    "runtime_s": f"{result.runtime_s:.12f}",
                    "J_T": f"{result.best_J_T:.16g}",
                    "J_R": f"{result.best_J_R:.16g}",
                    "J_unweighted": f"{result.best_J_unweighted:.16g}",
                    "J_weighted": f"{result.best_J_weighted:.16g}",
                    "best_z": json.dumps(result.best_z.tolist()),
                    "best_p": json.dumps(result.best_p.tolist()),
                    "T_theoretical": json.dumps(result.T_theoretical.tolist()),
                    "R_theoretical": json.dumps(result.R_theoretical.tolist()),
                    "valid_physics": result.valid_physics,
                    "configuration": _configuration_json(result),
                }
            )


def _write_history(path: Path, results: Sequence[object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "evaluation", "best_J_weighted", "best_J_unweighted", "best_J_T", "best_J_R"])
        for result in results:
            writer.writerows(
                (
                    result.seed,
                    record.evaluation,
                    f"{record.best_J_weighted:.16g}",
                    f"{record.best_J_unweighted:.16g}",
                    f"{record.best_J_T:.16g}",
                    f"{record.best_J_R:.16g}",
                )
                for record in result.convergence_history
            )


def _write_summary(path: Path, results: Sequence[object]) -> None:
    fields = ("J_T", "J_R", "J_unweighted", "J_weighted")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "median", "Q1", "Q3", "IQR", "best", "worst"])
        writer.writeheader()
        for field in fields:
            values = np.asarray([getattr(result, f"best_{field}") for result in results], dtype=np.float64)
            q1, q3 = np.percentile(values, [25.0, 75.0])
            writer.writerow(
                {
                    "metric": field,
                    "median": f"{np.median(values):.16g}",
                    "Q1": f"{q1:.16g}",
                    "Q3": f"{q3:.16g}",
                    "IQR": f"{q3 - q1:.16g}",
                    "best": f"{np.min(values):.16g}",
                    "worst": f"{np.max(values):.16g}",
                }
            )


def _run_group(
    algorithm: str,
    runner: AlgorithmRunner,
    weights: ObjectiveWeights,
    seeds: Sequence[int],
    budget: int,
    output_directory: Path,
) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    results: list[object] = []
    for seed in seeds:
        result = runner(seed=seed, budget=budget, weights=weights)
        results.append(result)
        print(
            f"algorithm={algorithm} w_R={weights.reflection:g} seed={seed} n={result.n_evaluations} "
            f"J_weighted={result.best_J_weighted:.16g} J_unweighted={result.best_J_unweighted:.16g}",
            flush=True,
        )
    _write_runs(output_directory / "runs.csv", results, weights)
    _write_history(output_directory / "convergence_history.csv", results)
    _write_summary(output_directory / "summary.csv", results)
    metadata = {
        "study": "Weighted-reflection sensitivity experiment",
        "search_space_version": SEARCH_SPACE_VERSION,
        "algorithm": algorithm,
        "w_T": weights.transmission,
        "w_R": weights.reflection,
        "seeds": list(seeds),
        "budget_per_seed": budget,
        "total_runtime_s": perf_counter() - started,
        "objective_note": "J_unweighted = J_T + J_R remains the scientific primary objective.",
    }
    (output_directory / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=float, nargs="+", default=list(DEFAULT_WEIGHTS), metavar="W_R")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--output-root", type=Path, default=ROOT / "results" / "weighted_reflection")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.budget <= 0 or not arguments.seeds:
        raise SystemExit("Provide a positive budget and at least one seed.")
    if not arguments.weights or any(weight <= 0.0 or not np.isfinite(weight) for weight in arguments.weights):
        raise SystemExit("Reflection weights must be finite and positive.")

    for algorithm, runner in ALGORITHMS:
        for reflection_weight in arguments.weights:
            weights = ObjectiveWeights(transmission=1.0, reflection=float(reflection_weight))
            _run_group(
                algorithm,
                runner,
                weights,
                arguments.seeds,
                arguments.budget,
                arguments.output_root / algorithm / _weight_label(reflection_weight),
            )
    print("Run scripts/analyze_weighted_reflection.py to generate figures and report.", flush=True)


if __name__ == "__main__":
    main()
