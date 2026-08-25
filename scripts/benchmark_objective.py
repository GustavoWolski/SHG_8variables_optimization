"""Measure the serial baseline cost of the validated Projeto 3 objective.

The script samples only physically valid vectors, performs a separate warm-up,
and writes machine-readable and human-readable reports under ``results/``.
It does not implement an optimizer or alter the physical model.
"""

from __future__ import annotations

import argparse
import csv
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
from numpy.typing import NDArray


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from optimization.constraints import is_physically_valid  # noqa: E402
from optimization.objective import ObjectiveEvaluator  # noqa: E402


DEFAULT_SEED = 20260824
DEFAULT_WARMUP_EVALUATIONS = 50
DEFAULT_COUNTS = (100, 1_000, 10_000)
DEFAULT_MAX_LARGEST_SECONDS = 120.0


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Timing statistics for one independently counted objective batch."""

    evaluations: int
    total_seconds: float
    mean_seconds: float
    median_seconds: float
    std_seconds: float
    min_seconds: float
    max_seconds: float
    evaluations_per_second: float


def _ordered_pair(rng: np.random.Generator) -> tuple[float, float]:
    """Sample a strictly ordered pair within the inclusive index box bounds."""

    lower = float(rng.uniform(1.5, 6.0))
    upper_lower_bound = float(np.nextafter(lower, 6.0))
    upper = float(rng.uniform(upper_lower_bound, 6.0))
    return lower, upper


def generate_valid_vectors(count: int, seed: int) -> NDArray[np.float64]:
    """Generate reproducible, valid benchmark vectors without rejection sampling."""

    if count < 1:
        raise ValueError("count must be positive.")

    rng = np.random.default_rng(seed)
    vectors = np.empty((count, 8), dtype=np.float64)
    vectors[:, 0] = rng.uniform(-10.0, 10.0, size=count)
    vectors[:, 1] = rng.uniform(0.0, 20.0, size=count)
    vectors[:, 5] = rng.uniform(0.0, 4.0, size=count)
    vectors[:, 7] = rng.uniform(0.0, 4.0, size=count)
    for index in range(count):
        vectors[index, 2], vectors[index, 3] = _ordered_pair(rng)
        vectors[index, 4], vectors[index, 6] = _ordered_pair(rng)

    if not all(is_physically_valid(vector) for vector in vectors):
        raise RuntimeError("The benchmark generator produced an invalid candidate.")
    return vectors


def warm_up(vectors: Iterable[NDArray[np.float64]]) -> int:
    """Execute unmeasured calls in a separate evaluator and return their count."""

    evaluator = ObjectiveEvaluator()
    for vector in vectors:
        evaluator.objective(vector)
    return evaluator.n_evaluations


def benchmark(vectors: NDArray[np.float64]) -> BenchmarkResult:
    """Time one serial objective call per vector and verify the official counter."""

    evaluator = ObjectiveEvaluator()
    durations = np.empty(vectors.shape[0], dtype=np.float64)
    total_start = time.perf_counter()
    for index, vector in enumerate(vectors):
        start = time.perf_counter()
        evaluator.objective(vector)
        durations[index] = time.perf_counter() - start
    total_seconds = time.perf_counter() - total_start

    if evaluator.n_evaluations != vectors.shape[0]:
        raise RuntimeError(
            f"ObjectiveEvaluator count mismatch: {evaluator.n_evaluations} != {vectors.shape[0]}."
        )
    return BenchmarkResult(
        evaluations=evaluator.n_evaluations,
        total_seconds=total_seconds,
        mean_seconds=float(np.mean(durations)),
        median_seconds=float(np.median(durations)),
        std_seconds=float(np.std(durations)),
        min_seconds=float(np.min(durations)),
        max_seconds=float(np.max(durations)),
        evaluations_per_second=float(vectors.shape[0] / total_seconds),
    )


def _duration(seconds: float) -> str:
    """Format one serial duration in seconds, minutes, and hours."""

    return f"{seconds:.6f} s / {seconds / 60:.6f} min / {seconds / 3600:.6f} h"


def _environment() -> dict[str, str | int]:
    """Collect standard-library environment details without new dependencies."""

    processor = platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "not detected")
    return {
        "python": sys.version.replace("\n", " "),
        "python_implementation": platform.python_implementation(),
        "operating_system": platform.platform(),
        "processor": processor,
        "cpu_count_logical": os.cpu_count() or "not detected",
        "parallelization": "none (serial baseline)",
    }


def _write_csv(results: list[BenchmarkResult], output_path: Path) -> None:
    """Write primary timing data in a compact machine-readable form."""

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(BenchmarkResult.__dataclass_fields__))
        writer.writeheader()
        for result in results:
            writer.writerow({name: getattr(result, name) for name in BenchmarkResult.__dataclass_fields__})


def _write_report(
    results: list[BenchmarkResult],
    environment: dict[str, str | int],
    seed: int,
    warmup_evaluations: int,
    skipped: list[str],
    output_path: Path,
) -> None:
    """Write the serial benchmark report and projections from the largest batch."""

    baseline = results[-1]
    budgets = (10_000, 25_000, 50_000, 100_000)
    lines = [
        "# Benchmark serial da função objetivo",
        "",
        "Este é o baseline serial da avaliação completa `p → validação → simulador → T/R → J_T/J_R → J`. "
        "Não usa paralelização, multiprocessing, GPU, cache ou vetorização adicional.",
        "",
        "## Ambiente",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in environment.items())
    lines.extend(
        [
            f"- seed dos vetores: {seed}",
            f"- warm-up não medido: {warmup_evaluations} avaliações físicas válidas",
            "- geração: amostragem uniforme dos bounds e geração condicional dos pares dispersivos estritos",
            "",
            "## Medições primárias",
            "",
            "| Avaliações | Tempo total (s) | Média (s) | Mediana (s) | Desvio padrão (s) | Mínimo (s) | Máximo (s) | Avaliações/s |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for result in results:
        lines.append(
            "| {evaluations} | {total_seconds:.6f} | {mean_seconds:.9f} | {median_seconds:.9f} | "
            "{std_seconds:.9f} | {min_seconds:.9f} | {max_seconds:.9f} | {evaluations_per_second:.3f} |".format(
                **result.__dict__ if hasattr(result, "__dict__") else {
                    name: getattr(result, name) for name in BenchmarkResult.__dataclass_fields__
                }
            )
        )
    if skipped:
        lines.extend(["", "## Etapas não executadas", ""])
        lines.extend(f"- {reason}" for reason in skipped)

    lines.extend(
        [
            "",
            "## Projeções seriais",
            "",
            "As projeções usam a média por avaliação da maior etapa executada "
            f"({baseline.evaluations} avaliações: {baseline.mean_seconds:.9f} s/avaliação). "
            "Elas excluem startup, I/O e overhead de algoritmos.",
            "",
            "| Budget por execução | Uma execução serial | 5 algoritmos × 30 seeds | 5 algoritmos × 50 seeds |",
            "|---:|---:|---:|---:|",
        ]
    )
    for budget in budgets:
        single = baseline.mean_seconds * budget
        thirty = single * 5 * 30
        fifty = single * 5 * 50
        lines.append(f"| {budget:,} | {_duration(single)} | {_duration(thirty)} | {_duration(fifty)} |")
    lines.extend(
        [
            "",
            "## Definição de avaliação",
            "",
            "Cada medição usa `ObjectiveEvaluator`; seu `n_evaluations` foi verificado exatamente "
            "contra o tamanho de cada lote. Rejeições não ocorrem: todos os vetores já satisfazem "
            "as constraints antes do benchmark.",
            "",
            "Este relatório não seleciona o budget definitivo; ele apenas fornece o custo serial de referência.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the benchmark with reproducible defaults and save both reports."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--warmup", type=int, default=DEFAULT_WARMUP_EVALUATIONS)
    parser.add_argument("--counts", nargs="+", type=int, default=list(DEFAULT_COUNTS))
    parser.add_argument("--max-largest-seconds", type=float, default=DEFAULT_MAX_LARGEST_SECONDS)
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "results")
    arguments = parser.parse_args()

    counts = tuple(sorted(set(arguments.counts)))
    if not counts or min(counts) < 1:
        raise ValueError("--counts must contain positive integers.")
    if arguments.warmup < 0:
        raise ValueError("--warmup must be non-negative.")

    warmup_vectors = generate_valid_vectors(arguments.warmup, arguments.seed + 1) if arguments.warmup else []
    warmup_count = warm_up(warmup_vectors) if arguments.warmup else 0
    vectors = generate_valid_vectors(max(counts), arguments.seed)

    results: list[BenchmarkResult] = []
    skipped: list[str] = []
    for count in counts:
        if results and count == max(counts):
            estimated_seconds = results[-1].mean_seconds * count
            if estimated_seconds > arguments.max_largest_seconds:
                skipped.append(
                    f"{count:,} avaliações: estimativa de {estimated_seconds:.3f} s excede "
                    f"o limite configurado de {arguments.max_largest_seconds:.3f} s."
                )
                continue
        result = benchmark(vectors[:count])
        results.append(result)
        print(
            f"{result.evaluations:,} evaluations: {result.mean_seconds:.9f} s/evaluation, "
            f"{result.evaluations_per_second:.3f} evaluations/s"
        )

    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(results, arguments.output_dir / "benchmark_objective.csv")
    _write_report(
        results, _environment(), arguments.seed, warmup_count, skipped, arguments.output_dir / "benchmark_objective.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
