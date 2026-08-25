"""Run the preliminary five-seed Random Search baseline experiment serially."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from experiments.data import D_NM, R_EXP, T_EXP  # noqa: E402
from optimization.constraints import PARAMETER_NAMES  # noqa: E402
from optimization.random_search import RandomSearchResult, random_search  # noqa: E402


DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_BUDGET = 50_000


def _statistics(values: np.ndarray) -> dict[str, float]:
    """Return descriptive statistics, using sample standard deviation for five seeds."""

    return {
        "best": float(np.min(values)),
        "worst": float(np.max(values)),
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values, ddof=1)),
        "iqr": float(np.percentile(values, 75) - np.percentile(values, 25)),
    }


def _write_runs(results: list[RandomSearchResult], output_path: Path) -> None:
    """Write one row per seed, including the final arrays as JSON."""

    fieldnames = [
        "algorithm", "seed", "budget", "n_evaluations", "runtime_s", "best_J", "best_J_T", "best_J_R",
        "best_z", "best_p", "T_theoretical", "R_theoretical", "valid_physics",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "algorithm": result.algorithm,
                    "seed": result.seed,
                    "budget": result.budget,
                    "n_evaluations": result.n_evaluations,
                    "runtime_s": result.runtime_s,
                    "best_J": result.best_J,
                    "best_J_T": result.best_J_T,
                    "best_J_R": result.best_J_R,
                    "best_z": json.dumps(result.best_z.tolist()),
                    "best_p": json.dumps(result.best_p.tolist()),
                    "T_theoretical": json.dumps(result.T_theoretical.tolist()),
                    "R_theoretical": json.dumps(result.R_theoretical.tolist()),
                    "valid_physics": result.valid_physics,
                }
            )


def _write_history(results: list[RandomSearchResult], output_path: Path) -> None:
    """Write all unmodified best-so-far points, one row per physical evaluation."""

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["seed", "evaluation", "best_J", "best_J_T", "best_J_R"])
        writer.writeheader()
        for result in results:
            for record in result.convergence_history:
                writer.writerow({"seed": result.seed, **asdict(record)})


def _write_summary(results: list[RandomSearchResult], output_path: Path) -> dict[str, dict[str, float]]:
    """Write aggregate descriptive statistics for all objective components."""

    statistics = {
        "best_J": _statistics(np.array([result.best_J for result in results])),
        "best_J_T": _statistics(np.array([result.best_J_T for result in results])),
        "best_J_R": _statistics(np.array([result.best_J_R for result in results])),
    }
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["metric", "best", "worst", "mean", "median", "std", "iqr"])
        writer.writeheader()
        for metric, values in statistics.items():
            writer.writerow({"metric": metric, **values})
    return statistics


def _write_parameters(results: list[RandomSearchResult], output_path: Path) -> None:
    """Write the eight best physical parameters obtained by each seed."""

    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["seed", "best_J", *PARAMETER_NAMES])
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "seed": result.seed,
                    "best_J": result.best_J,
                    **dict(zip(PARAMETER_NAMES, result.best_p, strict=True)),
                }
            )


def _plot_convergence(results: list[RandomSearchResult], output_path: Path) -> None:
    """Plot raw per-seed best-so-far curves plus the pointwise median and IQR."""

    histories = np.array([[record.best_J for record in result.convergence_history] for result in results])
    evaluations = np.array([record.evaluation for record in results[0].convergence_history])
    figure, axis = plt.subplots(figsize=(10, 6))
    for result, history in zip(results, histories, strict=True):
        axis.plot(evaluations, history, linewidth=1.0, alpha=0.75, label=f"seed {result.seed}")
    median = np.median(histories, axis=0)
    q25, q75 = np.percentile(histories, [25, 75], axis=0)
    axis.plot(evaluations, median, color="black", linewidth=1.4, label="mediana")
    axis.fill_between(evaluations, q25, q75, color="black", alpha=0.12, label="IQR")
    axis.set_xlabel("Avaliação física")
    axis.set_ylabel("Melhor J até a avaliação")
    axis.set_title("Random Search — convergência baseline preliminar")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def _plot_best_fit(best: RandomSearchResult, output_path: Path) -> None:
    """Plot experimental and theoretical transmission/reflection for the global best run."""

    figure, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    axes[0].plot(D_NM, T_EXP, "o", label="T experimental")
    axes[0].plot(D_NM, best.T_theoretical, "-o", label="T teórico")
    axes[0].set_ylabel("Transmissão normalizada")
    axes[0].set_title(f"Melhor Random Search: seed {best.seed}")
    axes[0].grid(alpha=0.25)
    axes[0].legend()
    axes[1].plot(D_NM, R_EXP, "o", label="R experimental")
    axes[1].plot(D_NM, best.R_theoretical, "-o", label="R teórico")
    axes[1].set_xlabel("Espessura medida (nm)")
    axes[1].set_ylabel("Reflexão normalizada")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def _write_report(
    results: list[RandomSearchResult],
    statistics: dict[str, dict[str, float]],
    total_runtime_s: float,
    output_path: Path,
) -> None:
    """Write a descriptive baseline report without interpreting algorithm quality."""

    best = min(results, key=lambda result: result.best_J)
    parameter_lines = "\n".join(
        f"- `{name}`: {value:.16g}" for name, value in zip(PARAMETER_NAMES, best.best_p, strict=True)
    )
    lines = [
        "# Random Search — baseline preliminar",
        "",
        "## Configuração",
        "",
        f"- algoritmo: `{best.algorithm}`",
        f"- seeds: `{', '.join(str(result.seed) for result in results)}`",
        f"- budget por seed: `{best.budget}` avaliações físicas",
        f"- total de avaliações físicas: `{sum(result.n_evaluations for result in results)}`",
        "- espaço: `z ∈ [0,1]^8`, mapeado pela transformação compartilhada `z → p`",
        "",
        "## Estatísticas dos resultados finais",
        "",
        "| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão amostral | IQR |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, values in statistics.items():
        lines.append(
            f"| {name} | {values['best']:.12g} | {values['worst']:.12g} | {values['mean']:.12g} | "
            f"{values['median']:.12g} | {values['std']:.12g} | {values['iqr']:.12g} |"
        )
    lines.extend(
        [
            "",
            "## Melhor execução global",
            "",
            f"- seed: `{best.seed}`",
            f"- J: `{best.best_J:.16g}`",
            f"- J_T: `{best.best_J_T:.16g}`",
            f"- J_R: `{best.best_J_R:.16g}`",
            "- vetor p:",
            parameter_lines,
            "",
            "## Tempo",
            "",
            f"- soma dos runtimes das cinco buscas: `{total_runtime_s:.6f} s` "
            f"(`{total_runtime_s / 60:.6f} min`)",
            "",
            "## Observações descritivas",
            "",
            "- As cinco seeds fornecem uma primeira medida de variabilidade de J e dos parâmetros; "
            "a tabela `best_parameters.csv` preserva os oito vetores para inspeção inicial.",
            "- As curvas usam valores best-so-far brutos, sem suavização.",
            "- Este experimento é apenas um baseline preliminar; ele não classifica a qualidade do "
            "Random Search e não constitui análise de identificabilidade.",
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the requested five-seed preliminary baseline and save all artifacts."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--output-dir", type=Path, default=REPOSITORY_ROOT / "results" / "random_search_baseline")
    arguments = parser.parse_args()

    if not arguments.seeds:
        raise ValueError("At least one seed is required.")
    arguments.output_dir.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    results: list[RandomSearchResult] = []
    for seed in arguments.seeds:
        result = random_search(seed=seed, budget=arguments.budget)
        results.append(result)
        print(f"seed={seed} best_J={result.best_J:.16g} runtime_s={result.runtime_s:.6f}")
    total_runtime_s = perf_counter() - start

    _write_runs(results, arguments.output_dir / "runs.csv")
    _write_history(results, arguments.output_dir / "convergence_history.csv")
    statistics = _write_summary(results, arguments.output_dir / "summary.csv")
    _write_parameters(results, arguments.output_dir / "best_parameters.csv")
    best = min(results, key=lambda result: result.best_J)
    _plot_convergence(results, arguments.output_dir / "convergence.png")
    _plot_best_fit(best, arguments.output_dir / "best_fit.png")
    _write_report(results, statistics, total_runtime_s, arguments.output_dir / "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
