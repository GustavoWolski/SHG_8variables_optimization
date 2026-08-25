"""Run the five-seed exact-budget Genetic Algorithm baseline."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from experiments.data import D_NM, R_EXP, T_EXP
from optimization.constraints import PARAMETER_NAMES
from optimization.genetic_algorithm import (
    DEFAULT_CONFIGURATION,
    GeneticAlgorithmResult,
    genetic_algorithm,
)


DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_BUDGET = 50_000


def _statistics(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(array, [25, 75])
    return {
        "best": float(np.min(array)),
        "worst": float(np.max(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "std": float(np.std(array, ddof=1)) if array.size > 1 else 0.0,
        "iqr": float(q3 - q1),
    }


def _histories(results: Sequence[GeneticAlgorithmResult]) -> np.ndarray:
    return np.asarray(
        [[record.best_J for record in result.convergence_history] for result in results],
        dtype=float,
    )


def _write_runs(path: Path, results: Sequence[GeneticAlgorithmResult]) -> None:
    fields = [
        "algorithm", "seed", "budget", "n_evaluations", "runtime_s",
        "best_J", "best_J_T", "best_J_R", "best_z", "best_p",
        "T_theoretical", "R_theoretical", "valid_physics", "configuration",
        "effective_population_size", "n_initial_evaluations", "n_offspring_evaluations",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "algorithm": result.algorithm,
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
                    "effective_population_size": result.effective_population_size,
                    "n_initial_evaluations": result.n_initial_evaluations,
                    "n_offspring_evaluations": result.n_offspring_evaluations,
                }
            )


def _write_history(path: Path, results: Sequence[GeneticAlgorithmResult]) -> None:
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


def _write_summary(path: Path, results: Sequence[GeneticAlgorithmResult]) -> dict[str, dict[str, float]]:
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


def _write_parameters(path: Path, results: Sequence[GeneticAlgorithmResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", "best_J", *PARAMETER_NAMES])
        for result in results:
            writer.writerow([result.seed, f"{result.best_J:.16g}", *[f"{value:.16g}" for value in result.best_p]])


def _plot_convergence(path: Path, results: Sequence[GeneticAlgorithmResult]) -> None:
    history = _histories(results)
    evaluations = np.arange(1, history.shape[1] + 1)
    figure, axis = plt.subplots(figsize=(10, 6))
    for result, values in zip(results, history, strict=True):
        axis.plot(evaluations, values, linewidth=0.8, alpha=0.75, label=f"Seed {result.seed}")
    median = np.median(history, axis=0)
    q1, q3 = np.percentile(history, [25, 75], axis=0)
    axis.plot(evaluations, median, color="black", linewidth=2, label="Mediana")
    axis.fill_between(evaluations, q1, q3, color="black", alpha=0.14, label="IQR")
    axis.set(xlabel="Avaliações físicas", ylabel="Melhor J até a avaliação", title="Genetic Algorithm: convergência")
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _plot_best_fit(path: Path, result: GeneticAlgorithmResult) -> None:
    figure, (axis_t, axis_r) = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    axis_t.plot(D_NM, T_EXP, "o", label="T experimental")
    axis_t.plot(D_NM, result.T_theoretical, "-", label="T teórico")
    axis_t.set(title="Transmissão", xlabel="Espessura experimental (nm)", ylabel="T")
    axis_t.grid(alpha=0.3)
    axis_t.legend()
    axis_r.plot(D_NM, R_EXP, "o", label="R experimental")
    axis_r.plot(D_NM, result.R_theoretical, "-", label="R teórico")
    axis_r.set(title="Reflexão", xlabel="Espessura experimental (nm)", ylabel="R")
    axis_r.grid(alpha=0.3)
    axis_r.legend()
    figure.suptitle(f"Melhor ajuste GA — seed {result.seed}, J={result.best_J:.6g}")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _read_history(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    values: dict[int, list[float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            values.setdefault(int(row["seed"]), []).append(float(row["best_J"]))
    return np.asarray(list(values.values()), dtype=float)


def _plot_comparison(path: Path, ga: np.ndarray, random_path: Path, de_path: Path) -> bool:
    random = _read_history(random_path)
    de = _read_history(de_path)
    if random is None or de is None:
        return False
    count = min(ga.shape[1], random.shape[1], de.shape[1])
    figure, axis = plt.subplots(figsize=(10, 6))
    for label, history, color in (
        ("Random Search", random[:, :count], "tab:orange"),
        ("Differential Evolution", de[:, :count], "tab:blue"),
        ("Genetic Algorithm", ga[:, :count], "tab:green"),
    ):
        evaluations = np.arange(1, count + 1)
        median = np.median(history, axis=0)
        q1, q3 = np.percentile(history, [25, 75], axis=0)
        axis.plot(evaluations, median, color=color, linewidth=2, label=f"{label}: mediana")
        axis.fill_between(evaluations, q1, q3, color=color, alpha=0.12, label=f"{label}: IQR")
    axis.set(
        xlabel="Avaliações físicas",
        ylabel="Melhor J até a avaliação",
        title="Comparação descritiva: Random Search, DE e GA",
    )
    axis.grid(alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return True


def _write_report(
    path: Path,
    results: Sequence[GeneticAlgorithmResult],
    summary: dict[str, dict[str, float]],
    total_runtime_s: float,
    comparison_written: bool,
) -> None:
    best = min(results, key=lambda item: item.best_J)
    configuration = best.configuration
    lines = [
        "# Baseline — Genetic Algorithm",
        "",
        "## Configuração",
        "",
        f"- Seeds: {', '.join(str(result.seed) for result in results)}",
        f"- Budget por seed: {best.budget} avaliações físicas",
        f"- Total de avaliações: {sum(result.n_evaluations for result in results)}",
        f"- population_size: {configuration.population_size}",
        f"- selection: tournament (tamanho {configuration.tournament_size})",
        f"- crossover: {configuration.crossover}; probabilidade {configuration.crossover_probability}; eta {configuration.crossover_distribution_index}",
        f"- mutation: {configuration.mutation}; probabilidade {configuration.mutation_probability}; eta {configuration.mutation_distribution_index}",
        f"- elitism: {configuration.elitism}",
        f"- initialization: {configuration.initialization} em z",
        f"- boundary handling: {configuration.boundary_handling} em z",
        "",
        "Elites carregam o resultado físico já obtido e não são reavaliados. A última geração pode ser parcial para encerrar exatamente no budget.",
        "",
        "## Estatísticas finais",
        "",
        "| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão | IQR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for metric, values in summary.items():
        lines.append(
            f"| {metric} | {values['best']:.16g} | {values['worst']:.16g} | {values['mean']:.16g} | "
            f"{values['median']:.16g} | {values['std']:.16g} | {values['iqr']:.16g} |"
        )
    lines.extend(
        [
            "",
            "## Execuções individuais",
            "",
            "| Seed | J | J_T | J_R | Tempo (s) |",
            "| ---: | ---: | ---: | ---: | ---: |",
            *[
                f"| {result.seed} | {result.best_J:.16g} | {result.best_J_T:.16g} | {result.best_J_R:.16g} | {result.runtime_s:.6f} |"
                for result in results
            ],
            "",
            "## Melhor execução global",
            "",
            f"- Seed: {best.seed}",
            f"- J: {best.best_J:.16g}",
            f"- J_T: {best.best_J_T:.16g}",
            f"- J_R: {best.best_J_R:.16g}",
            f"- Runtime: {best.runtime_s:.6f} s",
            f"- Runtime total: {total_runtime_s:.6f} s",
            "",
            "| Parâmetro | Valor |",
            "| --- | ---: |",
            *[f"| {name} | {value:.16g} |" for name, value in zip(PARAMETER_NAMES, best.best_p, strict=True)],
            "",
            "## Comparação descritiva",
            "",
            "- Random Search, DE e GA receberam 50.000 avaliações físicas por seed e as mesmas cinco seeds.",
            "- As curvas mostram medianas e IQR brutos por avaliação física, sem suavização.",
            "- " + (
                "O gráfico de três algoritmos foi gerado a partir dos históricos existentes."
                if comparison_written
                else "Os históricos de referência não estavam disponíveis para gerar o gráfico comparativo."
            ),
            "- Cinco seeds não permitem inferência estatística ou afirmação de superioridade entre algoritmos.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "genetic_algorithm_baseline")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.budget <= 0 or not arguments.seeds:
        raise SystemExit("Forneça budget positivo e ao menos uma seed.")
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    results = [genetic_algorithm(seed=seed, budget=arguments.budget) for seed in arguments.seeds]
    total_runtime_s = perf_counter() - start
    for result in results:
        print(f"seed={result.seed} n={result.n_evaluations} J={result.best_J:.16g} runtime={result.runtime_s:.3f}s", flush=True)
    _write_runs(arguments.output_dir / "runs.csv", results)
    _write_history(arguments.output_dir / "convergence_history.csv", results)
    summary = _write_summary(arguments.output_dir / "summary.csv", results)
    _write_parameters(arguments.output_dir / "best_parameters.csv", results)
    _plot_convergence(arguments.output_dir / "convergence.png", results)
    best = min(results, key=lambda item: item.best_J)
    _plot_best_fit(arguments.output_dir / "best_fit.png", best)
    comparison_written = _plot_comparison(
        arguments.output_dir / "ga_vs_random_vs_de_convergence.png",
        _histories(results),
        ROOT / "results" / "random_search_baseline" / "convergence_history.csv",
        ROOT / "results" / "differential_evolution_baseline" / "convergence_history.csv",
    )
    _write_report(arguments.output_dir / "report.md", results, summary, total_runtime_s, comparison_written)
    print(f"Resultados salvos em {arguments.output_dir}", flush=True)


if __name__ == "__main__":
    main()
