"""Validate and analyze the final six-parameter optimization benchmark."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis.plotting import CombinedTRPlotConfig, ExperimentalTRData, plot_combined_tr_fit  # noqa: E402
from experiments.data import D_NM, R_EXP, T_EXP  # noqa: E402
from optimization.constraints import PARAMETER_DEFINITIONS, PARAMETER_NAMES, is_physically_valid  # noqa: E402
from optimization.objective import evaluate  # noqa: E402


RESULTS_ROOT = ROOT / "results" / "final_6parameter_model"
ALGORITHMS = (
    ("Random Search", "random_search"),
    ("Differential Evolution", "differential_evolution"),
    ("Genetic Algorithm", "genetic_algorithm"),
    ("Particle Swarm Optimization", "particle_swarm"),
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty artifact: {path}")
    return rows


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite derived artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _run_values(row: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    return np.asarray(json.loads(row["best_z"]), dtype=float), np.asarray(json.loads(row["best_p"]), dtype=float)


def _validate_runs(all_runs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    validation: list[dict[str, object]] = []
    seen = 0
    for algorithm, rows in all_runs.items():
        if [int(row["seed"]) for row in rows] != [1, 2, 3, 4, 5]:
            raise ValueError(f"Unexpected seeds for {algorithm}")
        for row in rows:
            seen += 1
            z, p = _run_values(row)
            budget = int(row["budget"])
            n_evaluations = int(row["n_evaluations"])
            j = float(row["best_J"])
            jt = float(row["best_J_T"])
            jr = float(row["best_J_R"])
            rebuilt = evaluate(p)
            checks = {
                "budget_exact": n_evaluations == budget == 50_000,
                "normalized_vector_valid": z.shape == (6,) and bool(np.all((z >= 0.0) & (z <= 1.0))),
                "physical_vector_valid": p.shape == (6,) and is_physically_valid(p),
                "components_consistent": bool(np.isclose(j, jt + jr, rtol=0.0, atol=2e-12)),
                "reevaluation_consistent": bool(
                    np.allclose([j, jt, jr], [rebuilt.J, rebuilt.J_T, rebuilt.J_R], rtol=2e-12, atol=2e-12)
                ),
            }
            if not all(checks.values()):
                raise ValueError(f"Validation failed for {algorithm}, seed {row['seed']}: {checks}")
            validation.append({"algorithm": algorithm, "seed": int(row["seed"]), **checks})
    if seen != 20:
        raise ValueError(f"Expected 20 runs, found {seen}")
    return validation


def _configuration_rows() -> list[dict[str, object]]:
    return [
        {
            "algorithm": "Random Search", "seeds": "1,2,3,4,5", "n_seeds": 5, "budget_per_seed": 50_000,
            "population_size": "", "specific_parameters": "uniform z in [0,1]^6; numpy default_rng(seed)",
        },
        {
            "algorithm": "Differential Evolution", "seeds": "1,2,3,4,5", "n_seeds": 5,
            "budget_per_seed": 50_000, "population_size": 90,
            "specific_parameters": "best1bin; popsize=15; mutation=(0.5,1.0); recombination=0.7; init=latinhypercube; updating=deferred; tol=0; atol=0; polish=False; workers=1",
        },
        {
            "algorithm": "Genetic Algorithm", "seeds": "1,2,3,4,5", "n_seeds": 5,
            "budget_per_seed": 50_000, "population_size": 100,
            "specific_parameters": "tournament=3; SBX p=0.9 eta=15; polynomial mutation p=1/6 eta=20; elitism=1; uniform init; clip boundary",
        },
        {
            "algorithm": "Particle Swarm Optimization", "seeds": "1,2,3,4,5", "n_seeds": 5,
            "budget_per_seed": 50_000, "population_size": 100,
            "specific_parameters": "inertia=0.7298; c1=c2=1.49618; initial velocity limit=0.1; velocity limit=0.2; reflective boundary; global_best",
        },
    ]


def _aggregate_convergence(directory: Path) -> None:
    histories = _read_csv(directory / "convergence_history.csv")
    by_seed: dict[int, np.ndarray] = {}
    for seed in range(1, 6):
        values = np.asarray([float(row["best_J"]) for row in histories if int(row["seed"]) == seed], dtype=float)
        if values.shape != (50_000,):
            raise ValueError(f"Incomplete history in {directory}, seed {seed}: {values.shape}")
        by_seed[seed] = values
    matrix = np.vstack([by_seed[seed] for seed in range(1, 6)])
    q1, median, q3 = np.percentile(matrix, [25.0, 50.0, 75.0], axis=0)
    rows = [
        {"evaluation": index + 1, "q1_best_J": q1[index], "median_best_J": median[index], "q3_best_J": q3[index]}
        for index in range(50_000)
    ]
    _write_csv(directory / "convergence_aggregate.csv", list(rows[0]), rows)


def _statistics(all_runs: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    comparison: list[dict[str, object]] = []
    variability: list[dict[str, object]] = []
    for algorithm, rows in all_runs.items():
        js = np.asarray([float(row["best_J"]) for row in rows])
        runtimes = np.asarray([float(row["runtime_s"]) for row in rows])
        best_row = min(rows, key=lambda row: float(row["best_J"]))
        comparison.append(
            {
                "algorithm": algorithm,
                "best_J": float(np.min(js)), "median_J": float(np.median(js)), "mean_J": float(np.mean(js)),
                "std_J_sample": float(np.std(js, ddof=1)), "worst_J": float(np.max(js)),
                "best_seed": int(best_row["seed"]), "J_T_at_best_J": float(best_row["best_J_T"]),
                "J_R_at_best_J": float(best_row["best_J_R"]), "mean_runtime_s": float(np.mean(runtimes)),
                "total_runtime_s": float(np.sum(runtimes)), "n_runs": len(rows),
                "budget_per_seed": int(best_row["budget"]),
                "total_evaluations": sum(int(row["n_evaluations"]) for row in rows),
            }
        )
        matrix = np.vstack([_run_values(row)[1] for row in rows])
        for index, name in enumerate(PARAMETER_NAMES):
            values = matrix[:, index]
            variability.append(
                {
                    "algorithm": algorithm, "parameter": name,
                    "median": float(np.median(values)), "mean": float(np.mean(values)),
                    "std_sample": float(np.std(values, ddof=1)), "min": float(np.min(values)),
                    "max": float(np.max(values)),
                }
            )
    return comparison, variability


def _combined_plots(all_runs: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, str]]:
    experimental = ExperimentalTRData(D_NM, T_EXP, R_EXP)
    best_rows: dict[str, dict[str, str]] = {}
    directory_by_name = dict(ALGORITHMS)
    for algorithm, rows in all_runs.items():
        best = min(rows, key=lambda row: float(row["best_J"]))
        best_rows[algorithm] = best
        plot_combined_tr_fit(
            _run_values(best)[1], experimental,
            CombinedTRPlotConfig(RESULTS_ROOT / directory_by_name[algorithm], "best_fit_combined_tr"),
            algorithm=algorithm, seed=int(best["seed"]),
        )
    global_algorithm, global_row = min(
        ((algorithm, row) for algorithm, rows in all_runs.items() for row in rows),
        key=lambda item: float(item[1]["best_J"]),
    )
    plot_combined_tr_fit(
        _run_values(global_row)[1], experimental,
        CombinedTRPlotConfig(RESULTS_ROOT / "comparisons", "global_best_combined_tr"),
        algorithm=global_algorithm, seed=int(global_row["seed"]),
    )
    best_rows["GLOBAL"] = {**global_row, "selected_algorithm": global_algorithm}
    return best_rows


def _report(
    comparison: list[dict[str, object]], variability: list[dict[str, object]], best_rows: dict[str, dict[str, str]]
) -> str:
    global_best = best_rows["GLOBAL"]
    global_p = _run_values(global_best)[1]
    total_runtime = sum(float(row["total_runtime_s"]) for row in comparison)
    lines = [
        "# Benchmark final — modelo físico de 6 parâmetros", "",
        "## Protocolo", "",
        "- Modelo: `p = [log10_chi, delta_d3_nm, n3_w, k3_w, n3_2w, k3_2w]`.",
        "- Óxido fixo: `d2 = 10 nm`, `n2_w = n2_2w = 1`.",
        "- Espessura efetiva: `d3_eff = max(d3_nominal + delta_d3_nm, 0)`.",
        "- Objetivo oficial: `J = J_T + J_R`, pesos unitários e sem ordenação de dispersão.",
        "- Seeds: `1, 2, 3, 4, 5`; orçamento: `50.000` avaliações físicas por seed.",
        "- Total: `20` runs e `1.000.000` avaliações físicas.", "",
        "## Comparação final", "",
        "| Algoritmo | Melhor J | Mediana | Média | DP amostral | Pior | Seed | J_T no melhor | J_R no melhor | Tempo médio (s) | Tempo total (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison:
        lines.append(
            f"| {row['algorithm']} | {row['best_J']:.12g} | {row['median_J']:.12g} | {row['mean_J']:.12g} | "
            f"{row['std_J_sample']:.6g} | {row['worst_J']:.12g} | {row['best_seed']} | "
            f"{row['J_T_at_best_J']:.12g} | {row['J_R_at_best_J']:.12g} | "
            f"{row['mean_runtime_s']:.3f} | {row['total_runtime_s']:.3f} |"
        )
    lines.extend([
        "", "## Melhor solução global", "",
        f"- Algoritmo: `{global_best['selected_algorithm']}`; seed: `{global_best['seed']}`.",
        f"- `J = {float(global_best['best_J']):.16g}`; `J_T = {float(global_best['best_J_T']):.16g}`; `J_R = {float(global_best['best_J_R']):.16g}`.",
        "- Vetor físico:",
    ])
    for definition, value in zip(PARAMETER_DEFINITIONS, global_p, strict=True):
        lines.append(f"  - `{definition.name}` = `{value:.16g}` {definition.unit}")
    lines.extend([
        "", "## Validação e comportamento observado", "",
        "- Todos os 20 runs consumiram exatamente 50.000 avaliações e passaram na reavaliação independente de `J`, `J_T` e `J_R`.",
        "- DE e três seeds de PSO chegaram à mesma bacia numérica; a diferença entre os melhores DE e PSO é da ordem de `10^-13`.",
        "- A melhor solução está nos limites inferiores de `delta_d3_nm` e `n3_w`, sinal de solução de fronteira e possível baixa identificabilidade nesses eixos.",
        "- O GA mostrou uma seed claramente pior (seed 5), preservada sem repetição ou ajuste.",
        "- O runner de DE continha apenas um rótulo antigo `15 × 8`; ele foi corrigido para refletir a população realmente usada, `15 × 6 = 90`, sem alterar o algoritmo.",
        f"- Soma dos runtimes internos: `{total_runtime:.3f} s` (`{total_runtime / 60.0:.3f} min`).", "",
        "## Artefatos", "",
        "- `configurations.csv`: protocolo completo dos algoritmos.",
        "- `comparisons/final_comparison.csv`: estatísticas comparativas e tempos.",
        "- `comparisons/parameter_variability.csv`: mediana, média, DP, mínimo e máximo por algoritmo/parâmetro.",
        "- `comparisons/global_best.csv`: melhor solução global com nomes físicos explícitos.",
        "- Cada pasta de algoritmo contém runs, parâmetros por seed, histórico bruto, agregado Q1/mediana/Q3, convergência e ajuste combinado T/R em PNG/PDF.",
        "- Os resultados históricos fora de `results/final_6parameter_model/` não foram modificados nem sobrescritos.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    if not RESULTS_ROOT.is_dir():
        raise FileNotFoundError(RESULTS_ROOT)
    all_runs = {name: _read_csv(RESULTS_ROOT / directory / "runs.csv") for name, directory in ALGORITHMS}
    validation = _validate_runs(all_runs)
    comparison, variability = _statistics(all_runs)
    for _, directory in ALGORITHMS:
        _aggregate_convergence(RESULTS_ROOT / directory)
    _write_csv(
        RESULTS_ROOT / "configurations.csv",
        ["algorithm", "seeds", "n_seeds", "budget_per_seed", "population_size", "specific_parameters"],
        _configuration_rows(),
    )
    _write_csv(RESULTS_ROOT / "comparisons" / "validation.csv", list(validation[0]), validation)
    _write_csv(RESULTS_ROOT / "comparisons" / "final_comparison.csv", list(comparison[0]), comparison)
    _write_csv(RESULTS_ROOT / "comparisons" / "parameter_variability.csv", list(variability[0]), variability)
    best_rows = _combined_plots(all_runs)
    global_best = best_rows["GLOBAL"]
    global_z, global_p = _run_values(global_best)
    global_row: dict[str, object] = {
        "algorithm": global_best["selected_algorithm"], "seed": int(global_best["seed"]),
        "budget": int(global_best["budget"]), "n_evaluations": int(global_best["n_evaluations"]),
        "runtime_s": float(global_best["runtime_s"]), "best_J": float(global_best["best_J"]),
        "best_J_T": float(global_best["best_J_T"]), "best_J_R": float(global_best["best_J_R"]),
        "best_z": json.dumps(global_z.tolist()), "best_p": json.dumps(global_p.tolist()),
        **dict(zip(PARAMETER_NAMES, global_p, strict=True)),
    }
    _write_csv(RESULTS_ROOT / "comparisons" / "global_best.csv", list(global_row), [global_row])
    report_path = RESULTS_ROOT / "final_report.md"
    if report_path.exists():
        raise FileExistsError(report_path)
    report_path.write_text(_report(comparison, variability, best_rows), encoding="utf-8")
    print(f"validated_runs={len(validation)} total_evaluations={sum(int(row['n_evaluations']) for rows in all_runs.values() for row in rows)}")
    print(f"global_best={global_best['selected_algorithm']} seed={global_best['seed']} J={global_best['best_J']}")
    print(f"report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
