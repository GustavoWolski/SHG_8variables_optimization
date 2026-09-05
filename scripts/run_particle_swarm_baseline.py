"""Run the Search-space version 2 exact-budget global-best PSO baseline."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from optimization.constraints import PARAMETER_NAMES  # noqa: E402
from optimization.particle_swarm import (  # noqa: E402
    DEFAULT_CONFIGURATION,
    ParticleSwarmResult,
    particle_swarm,
)


DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_BUDGET = 50_000
SEARCH_SPACE_VERSION = 2


def _statistics(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(array, [25.0, 75.0])
    return {
        "best": float(np.min(array)),
        "worst": float(np.max(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std": float(np.std(array, ddof=1)) if array.size > 1 else 0.0,
        "iqr": float(q3 - q1),
    }


def _write_runs(path: Path, results: Sequence[ParticleSwarmResult]) -> None:
    fields = [
        "algorithm", "search_space_version", "seed", "budget", "n_evaluations", "runtime_s",
        "best_J", "best_J_T", "best_J_R", "best_z", "best_p", "T_theoretical", "R_theoretical",
        "valid_physics", "configuration", "effective_swarm_size", "n_initial_evaluations",
        "n_particle_evaluations",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "algorithm": result.algorithm,
                    "search_space_version": SEARCH_SPACE_VERSION,
                    "seed": result.seed,
                    "budget": result.budget,
                    "n_evaluations": result.n_evaluations,
                    "runtime_s": f"{result.runtime_s:.12f}",
                    "best_J": f"{result.best_J:.16g}",
                    "best_J_T": f"{result.best_J_T:.16g}",
                    "best_J_R": f"{result.best_J_R:.16g}",
                    "best_z": json.dumps(result.best_z.tolist()),
                    "best_p": json.dumps(result.best_p.tolist()),
                    "T_theoretical": json.dumps(result.T_theoretical.tolist()),
                    "R_theoretical": json.dumps(result.R_theoretical.tolist()),
                    "valid_physics": result.valid_physics,
                    "configuration": json.dumps(asdict(result.configuration)),
                    "effective_swarm_size": result.effective_swarm_size,
                    "n_initial_evaluations": result.n_initial_evaluations,
                    "n_particle_evaluations": result.n_particle_evaluations,
                }
            )


def _write_history(path: Path, results: Sequence[ParticleSwarmResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "evaluation", "best_J", "best_J_T", "best_J_R"])
        for result in results:
            writer.writerows(
                (
                    result.seed,
                    record.evaluation,
                    f"{record.best_J:.16g}",
                    f"{record.best_J_T:.16g}",
                    f"{record.best_J_R:.16g}",
                )
                for record in result.convergence_history
            )


def _write_summary(path: Path, results: Sequence[ParticleSwarmResult]) -> dict[str, dict[str, float]]:
    summary = {
        "best_J": _statistics([result.best_J for result in results]),
        "best_J_T": _statistics([result.best_J_T for result in results]),
        "best_J_R": _statistics([result.best_J_R for result in results]),
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "statistic", "value"])
        writer.writeheader()
        for metric, statistics in summary.items():
            for name, value in statistics.items():
                writer.writerow({"metric": metric, "statistic": name, "value": f"{value:.16g}"})
    return summary


def _write_parameters(path: Path, results: Sequence[ParticleSwarmResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "best_J", *PARAMETER_NAMES])
        for result in results:
            writer.writerow([result.seed, f"{result.best_J:.16g}", *[f"{value:.16g}" for value in result.best_p]])


def _write_report(
    path: Path,
    results: Sequence[ParticleSwarmResult],
    summary: dict[str, dict[str, float]],
    total_runtime_s: float,
) -> None:
    best = min(results, key=lambda item: item.best_J)
    configuration = best.configuration
    lines = [
        "# Baseline — Particle Swarm Optimization",
        "",
        "## Configuration",
        "",
        f"- Search-space version: {SEARCH_SPACE_VERSION}",
        f"- Seeds: {', '.join(str(result.seed) for result in results)}",
        f"- Budget per seed: {best.budget} physical evaluations",
        f"- Total physical evaluations: {sum(result.n_evaluations for result in results)}",
        f"- Topology: {configuration.topology}",
        f"- swarm_size: {configuration.swarm_size}",
        f"- inertia weight: {configuration.inertia_weight}",
        f"- cognitive coefficient c1: {configuration.cognitive_coefficient}",
        f"- social coefficient c2: {configuration.social_coefficient}",
        f"- velocity initialization: {configuration.velocity_initialization} in ±{configuration.initial_velocity_limit}",
        f"- velocity limit per coordinate: ±{configuration.velocity_limit}",
        f"- boundary handling: {configuration.boundary_handling} in normalized z space",
        "",
        "The initial swarm consumes physical evaluations. A final partial particle batch is evaluated only up to the exact remaining budget; no physical-space repair is used.",
        "",
        "## Final statistics",
        "",
        "| Metric | Best | Worst | Mean | Median | Sample standard deviation | IQR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for metric, values in summary.items():
        lines.append(
            f"| {metric} | {values['best']:.16g} | {values['worst']:.16g} | {values['mean']:.16g} | "
            f"{values['median']:.16g} | {values['std']:.16g} | {values['iqr']:.16g} |"
        )
    lines.extend(
        [
            "",
            "## Individual runs",
            "",
            "| Seed | J | J_T | J_R | Runtime (s) |",
            "|---:|---:|---:|---:|---:|",
            *[
                f"| {result.seed} | {result.best_J:.16g} | {result.best_J_T:.16g} | "
                f"{result.best_J_R:.16g} | {result.runtime_s:.6f} |"
                for result in results
            ],
            "",
            "## Best global run",
            "",
            f"- Seed: {best.seed}",
            f"- J: {best.best_J:.16g}",
            f"- J_T: {best.best_J_T:.16g}",
            f"- J_R: {best.best_J_R:.16g}",
            f"- Runtime: {best.runtime_s:.6f} s",
            f"- Total runtime: {total_runtime_s:.6f} s",
            "",
            "| Parameter | Value |",
            "|---|---:|",
            *[f"| {name} | {value:.16g} |" for name, value in zip(PARAMETER_NAMES, best.best_p, strict=True)],
            "",
            "## Descriptive comparison",
            "",
            "- RS, DE, GA and PSO use Search-space version 2, the same seeds and 50,000 physical evaluations per seed.",
            "- Standardized comparison figures are regenerated exclusively by `scripts/regenerate_benchmark_figures.py`.",
            "- Five seeds are descriptive only and do not support statistical superiority claims.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "search_space_v2" / "particle_swarm")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.budget <= 0 or not arguments.seeds:
        raise SystemExit("Provide a positive budget and at least one seed.")
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    results = [particle_swarm(seed=seed, budget=arguments.budget) for seed in arguments.seeds]
    total_runtime_s = perf_counter() - started
    for result in results:
        print(
            f"seed={result.seed} n={result.n_evaluations} J={result.best_J:.16g} "
            f"runtime={result.runtime_s:.3f}s",
            flush=True,
        )
    _write_runs(arguments.output_dir / "runs.csv", results)
    _write_history(arguments.output_dir / "convergence_history.csv", results)
    summary = _write_summary(arguments.output_dir / "summary.csv", results)
    _write_parameters(arguments.output_dir / "best_parameters.csv", results)
    _write_report(arguments.output_dir / "report.md", results, summary, total_runtime_s)
    print(f"Results saved to {arguments.output_dir}", flush=True)
    print("Regenerate standardized figures with scripts/regenerate_benchmark_figures.py", flush=True)


if __name__ == "__main__":
    main()
