"""Execute the reproducible Differential Evolution baseline experiment."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from optimization.constraints import PARAMETER_NAMES
from optimization.differential_evolution import (
    DEFAULT_CONFIGURATION,
    DifferentialEvolutionResult,
    differential_evolution,
)
from experiments.data import D_NM, R_EXP, T_EXP


DEFAULT_SEEDS = (1, 2, 3, 4, 5)
DEFAULT_BUDGET = 50_000


def _summary(values: Sequence[float]) -> dict[str, float]:
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


def _write_runs(path: Path, results: Sequence[DifferentialEvolutionResult]) -> None:
    fields = [
        "algorithm",
        "seed",
        "budget",
        "n_evaluations",
        "runtime_s",
        "best_J",
        "best_J_T",
        "best_J_R",
        "best_z",
        "best_p",
        "T_theoretical",
        "R_theoretical",
        "configuration",
        "scipy_maxfun",
        "scipy_maxiter",
        "scipy_nfev",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "algorithm": "differential_evolution",
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
                    "configuration": json.dumps(asdict(result.configuration)),
                    "scipy_maxfun": result.scipy_maxfun,
                    "scipy_maxiter": result.scipy_maxiter,
                    "scipy_nfev": result.scipy_nfev,
                }
            )


def _write_history(path: Path, results: Sequence[DifferentialEvolutionResult]) -> None:
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


def _write_summary(path: Path, results: Sequence[DifferentialEvolutionResult]) -> None:
    rows: list[dict[str, str]] = []
    for metric, values in (
        ("best_J", [result.best_J for result in results]),
        ("best_J_T", [result.best_J_T for result in results]),
        ("best_J_R", [result.best_J_R for result in results]),
    ):
        for statistic, value in _summary(values).items():
            rows.append({"metric": metric, "statistic": statistic, "value": f"{value:.16g}"})

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "statistic", "value"])
        writer.writeheader()
        writer.writerows(rows)


def _write_parameters(path: Path, results: Sequence[DifferentialEvolutionResult]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["seed", *PARAMETER_NAMES])
        for result in results:
            writer.writerow([result.seed, *[f"{value:.16g}" for value in result.best_p]])


def _history_matrix(results: Sequence[DifferentialEvolutionResult]) -> np.ndarray:
    return np.asarray(
        [[record.best_J for record in result.convergence_history] for result in results],
        dtype=float,
    )


def _plot_convergence(path: Path, results: Sequence[DifferentialEvolutionResult]) -> None:
    histories = _history_matrix(results)
    evaluations = np.arange(1, histories.shape[1] + 1)
    figure, axis = plt.subplots(figsize=(10, 6))
    for result, history in zip(results, histories, strict=True):
        axis.plot(evaluations, history, linewidth=0.8, alpha=0.7, label=f"Seed {result.seed}")

    median = np.median(histories, axis=0)
    q1, q3 = np.percentile(histories, [25, 75], axis=0)
    axis.plot(evaluations, median, color="black", linewidth=2.0, label="Mediana")
    axis.fill_between(evaluations, q1, q3, color="black", alpha=0.15, label="IQR")
    axis.set_xlabel("Avaliações da função objetivo")
    axis.set_ylabel("Melhor J até a avaliação")
    axis.set_title("Differential Evolution: convergência por avaliação")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _plot_best_fit(path: Path, best: DifferentialEvolutionResult) -> None:
    figure, (axis_t, axis_r) = plt.subplots(1, 2, figsize=(11, 4.5), sharex=True)
    axis_t.plot(D_NM, T_EXP, "o", label="T experimental")
    axis_t.plot(D_NM, best.T_theoretical, "-", label="T teórico")
    axis_t.set_title("Transmissão")
    axis_t.set_xlabel("Espessura experimental (nm)")
    axis_t.set_ylabel("T")
    axis_t.grid(True, alpha=0.3)
    axis_t.legend()

    axis_r.plot(D_NM, R_EXP, "o", label="R experimental")
    axis_r.plot(D_NM, best.R_theoretical, "-", label="R teórico")
    axis_r.set_title("Reflexão")
    axis_r.set_xlabel("Espessura experimental (nm)")
    axis_r.set_ylabel("R")
    axis_r.grid(True, alpha=0.3)
    axis_r.legend()
    figure.suptitle(f"Melhor ajuste DE — seed {best.seed}, J={best.best_J:.6g}")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def _read_random_history(path: Path) -> dict[int, np.ndarray] | None:
    if not path.exists():
        return None
    histories: dict[int, list[float]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            histories.setdefault(int(row["seed"]), []).append(float(row["best_J"]))
    return {seed: np.asarray(history, dtype=float) for seed, history in histories.items()}


def _plot_comparison(
    path: Path,
    results: Sequence[DifferentialEvolutionResult],
    random_history_path: Path,
) -> bool:
    random_histories = _read_random_history(random_history_path)
    if random_histories is None:
        return False

    de = _history_matrix(results)
    random = np.asarray(list(random_histories.values()), dtype=float)
    count = min(de.shape[1], random.shape[1])
    evaluations = np.arange(1, count + 1)

    figure, axis = plt.subplots(figsize=(10, 6))
    for label, histories, color in (
        ("Differential Evolution", de[:, :count], "tab:blue"),
        ("Random Search", random[:, :count], "tab:orange"),
    ):
        median = np.median(histories, axis=0)
        q1, q3 = np.percentile(histories, [25, 75], axis=0)
        axis.plot(evaluations, median, color=color, linewidth=2, label=f"{label}: mediana")
        axis.fill_between(evaluations, q1, q3, color=color, alpha=0.17, label=f"{label}: IQR")
    axis.set_xlabel("Avaliações da função objetivo")
    axis.set_ylabel("Melhor J até a avaliação")
    axis.set_title("Comparação descritiva: DE e Random Search")
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return True


def _format_vector(values: np.ndarray) -> str:
    return ", ".join(f"{value:.16g}" for value in values)


def _write_report(
    path: Path,
    results: Sequence[DifferentialEvolutionResult],
    total_runtime_seconds: float,
    random_reference_dir: Path,
    comparison_written: bool,
) -> None:
    best = min(results, key=lambda result: result.best_J)
    j_summary = _summary([result.best_J for result in results])
    jt_summary = _summary([result.best_J_T for result in results])
    jr_summary = _summary([result.best_J_R for result in results])
    random_runs = random_reference_dir / "runs.csv"
    random_note = (
        "O gráfico de mediana/IQR foi criado a partir do histórico do Random Search."
        if comparison_written
        else "A referência de Random Search não estava disponível; nenhum gráfico comparativo foi criado."
    )

    lines = [
        "# Baseline — Differential Evolution",
        "",
        "## Configuração",
        "",
        f"- Seeds: {', '.join(str(result.seed) for result in results)}",
        f"- Budget por seed: {results[0].budget} avaliações físicas",
        f"- Total de avaliações: {sum(result.n_evaluations for result in results)}",
        f"- SciPy: {scipy.__version__}",
        f"- Python: {platform.python_version()}",
        f"- Sistema: {platform.platform()}",
        f"- Estratégia: {best.configuration.strategy}",
        f"- População nominal: {best.configuration.popsize} × 8 = {best.configuration.popsize * 8}",
        f"- Mutation: {best.configuration.mutation}",
        f"- Recombination: {best.configuration.recombination}",
        f"- Inicialização: {best.configuration.init}",
        f"- Atualização: {best.configuration.updating}",
        f"- tol/atol: {best.configuration.tol}/{best.configuration.atol}",
        f"- polish: {best.configuration.polish}",
        "",
        "O orçamento é imposto pelo contador de avaliações físicas e por maxfun no solver "
        "do SciPy. Não há polish nem avaliação final adicional.",
        "",
        "## Estatísticas entre seeds",
        "",
        "| Métrica | Melhor | Pior | Média | Mediana | Desvio padrão | IQR |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| J | {j_summary['best']:.16g} | {j_summary['worst']:.16g} | "
            f"{j_summary['mean']:.16g} | {j_summary['median']:.16g} | "
            f"{j_summary['std']:.16g} | {j_summary['iqr']:.16g} |"
        ),
        (
            f"| J_T | {jt_summary['best']:.16g} | {jt_summary['worst']:.16g} | "
            f"{jt_summary['mean']:.16g} | {jt_summary['median']:.16g} | "
            f"{jt_summary['std']:.16g} | {jt_summary['iqr']:.16g} |"
        ),
        (
            f"| J_R | {jr_summary['best']:.16g} | {jr_summary['worst']:.16g} | "
            f"{jr_summary['mean']:.16g} | {jr_summary['median']:.16g} | "
            f"{jr_summary['std']:.16g} | {jr_summary['iqr']:.16g} |"
        ),
        "",
        "## Melhor execução global",
        "",
        f"- Seed: {best.seed}",
        f"- J: {best.best_J:.16g}",
        f"- J_T: {best.best_J_T:.16g}",
        f"- J_R: {best.best_J_R:.16g}",
        f"- Tempo desta execução: {best.runtime_s:.6f} s",
        f"- Tempo total das cinco execuções: {total_runtime_seconds:.6f} s",
        "",
        "| Parâmetro | Valor |",
        "| --- | ---: |",
        *[f"| {name} | {value:.16g} |" for name, value in zip(PARAMETER_NAMES, best.best_p, strict=True)],
        "",
        "## Observações descritivas",
        "",
        f"- {random_note}",
        f"- Referência usada para comparação: {random_runs}.",
        "- As curvas registram o melhor J observado após cada avaliação física; não houve suavização.",
        "- Este baseline é descritivo. Ele não estabelece ainda uma conclusão de superioridade entre algoritmos.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "differential_evolution_baseline",
    )
    parser.add_argument(
        "--random-reference-dir",
        type=Path,
        default=ROOT / "results" / "random_search_baseline",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.budget <= 0:
        raise SystemExit("--budget deve ser positivo.")
    if not arguments.seeds:
        raise SystemExit("Forneça pelo menos uma seed.")

    output_dir = arguments.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    started = perf_counter()
    results: list[DifferentialEvolutionResult] = []
    for seed in arguments.seeds:
        result = differential_evolution(
            budget=arguments.budget,
            seed=seed,
            configuration=DEFAULT_CONFIGURATION,
        )
        results.append(result)
        print(
            f"seed={seed} n={result.n_evaluations} J={result.best_J:.16g} "
            f"J_T={result.best_J_T:.16g} J_R={result.best_J_R:.16g} "
            f"runtime={result.runtime_s:.3f}s",
            flush=True,
        )
    total_runtime = perf_counter() - started

    best = min(results, key=lambda result: result.best_J)
    _write_runs(output_dir / "runs.csv", results)
    _write_history(output_dir / "convergence_history.csv", results)
    _write_summary(output_dir / "summary.csv", results)
    _write_parameters(output_dir / "best_parameters.csv", results)
    _plot_convergence(output_dir / "convergence.png", results)
    _plot_best_fit(output_dir / "best_fit.png", best)
    comparison_written = _plot_comparison(
        output_dir / "de_vs_random_convergence.png",
        results,
        arguments.random_reference_dir / "convergence_history.csv",
    )
    _write_report(
        output_dir / "report.md",
        results,
        total_runtime,
        arguments.random_reference_dir,
        comparison_written,
    )

    print(f"Resultados salvos em {output_dir}", flush=True)
    print(f"Melhor seed={best.seed}; p=[{_format_vector(best.best_p)}]", flush=True)
    print(f"Tempo total={total_runtime:.3f}s", flush=True)


if __name__ == "__main__":
    main()
