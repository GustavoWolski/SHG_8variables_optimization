"""Create figures and report for the weighted-reflection sensitivity experiment."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from analysis.plotting import (  # noqa: E402
    ALGORITHM_COLORS,
    AlgorithmResults,
    AlgorithmSpec,
    BenchmarkRun,
    determine_best_fit_axis_limits,
    plot_best_fit,
    plot_best_fits_comparison,
)


ALGORITHM_NAMES = {
    "random_search": ("Random Search", "RS"),
    "differential_evolution": ("Differential Evolution", "DE"),
    "genetic_algorithm": ("Genetic Algorithm", "GA"),
    "particle_swarm": ("Particle Swarm Optimization", "PSO"),
}
ALGORITHM_MARKERS = {"random_search": "o", "differential_evolution": "s", "genetic_algorithm": "^", "particle_swarm": "D"}
WEIGHT_MARKERS = {1.0: "o", 2.0: "s", 5.0: "^", 10.0: "D"}
PLOT_RC = {"font.family": "DejaVu Sans", "font.size": 9.5, "axes.linewidth": 0.8, "grid.alpha": 0.35}


@dataclass(frozen=True)
class WeightedRun:
    algorithm_key: str
    weight: float
    seed: int
    budget: int
    n_evaluations: int
    runtime_s: float
    j_t: float
    j_r: float
    j_unweighted: float
    j_weighted: float
    best_p: np.ndarray
    best_z: np.ndarray
    t_theoretical: np.ndarray
    r_theoretical: np.ndarray


@dataclass(frozen=True)
class WeightedGroup:
    algorithm_key: str
    weight: float
    directory: Path
    runs: tuple[WeightedRun, ...]

    @property
    def best(self) -> WeightedRun:
        return min(self.runs, key=lambda run: run.j_weighted)

    def values(self, name: str) -> np.ndarray:
        return np.asarray([getattr(run, name) for run in self.runs], dtype=np.float64)


def _array(value: str, field: str, path: Path) -> np.ndarray:
    array = np.asarray(json.loads(value), dtype=np.float64)
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise ValueError(f"Invalid {field} in {path}.")
    return array


def load_groups(root: Path) -> tuple[WeightedGroup, ...]:
    groups: list[WeightedGroup] = []
    for path in sorted(root.glob("*/wR_*/runs.csv")):
        algorithm_key = path.parents[1].name
        if algorithm_key not in ALGORITHM_NAMES:
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError(f"Empty runs file: {path}")
        required = {"w_T", "w_R", "J_T", "J_R", "J_unweighted", "J_weighted", "best_z", "best_p", "T_theoretical", "R_theoretical"}
        if missing := required.difference(rows[0]):
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
        weight = float(rows[0]["w_R"])
        if any(float(row["w_R"]) != weight or float(row["w_T"]) != 1.0 for row in rows):
            raise ValueError(f"Inconsistent weights in {path}")
        runs = tuple(
            WeightedRun(
                algorithm_key=algorithm_key,
                weight=weight,
                seed=int(row["seed"]),
                budget=int(row["budget"]),
                n_evaluations=int(row["n_evaluations"]),
                runtime_s=float(row["runtime_s"]),
                j_t=float(row["J_T"]),
                j_r=float(row["J_R"]),
                j_unweighted=float(row["J_unweighted"]),
                j_weighted=float(row["J_weighted"]),
                best_z=_array(row["best_z"], "best_z", path),
                best_p=_array(row["best_p"], "best_p", path),
                t_theoretical=_array(row["T_theoretical"], "T_theoretical", path),
                r_theoretical=_array(row["R_theoretical"], "R_theoretical", path),
            )
            for row in rows
        )
        if any(run.n_evaluations != run.budget for run in runs):
            raise ValueError(f"Non-exact budget in {path}")
        groups.append(WeightedGroup(algorithm_key, weight, path.parent, runs))
    if not groups:
        raise FileNotFoundError(f"No weighted result groups found below {root}")
    return tuple(groups)


def _save(figure: plt.Figure, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, dpi=320, facecolor="white", bbox_inches="tight")
    figure.savefig(output.with_suffix(".pdf"), facecolor="white", bbox_inches="tight")
    plt.close(figure)


def _grouped(groups: Iterable[WeightedGroup]) -> dict[str, list[WeightedGroup]]:
    grouped: dict[str, list[WeightedGroup]] = {key: [] for key in ALGORITHM_NAMES}
    for group in groups:
        grouped[group.algorithm_key].append(group)
    for values in grouped.values():
        values.sort(key=lambda item: item.weight)
    return {key: values for key, values in grouped.items() if values}


def plot_tradeoff(groups: Sequence[WeightedGroup], root: Path) -> None:
    with plt.rc_context(PLOT_RC):
        figure, axis = plt.subplots(figsize=(8.2, 5.6), layout="constrained")
        for group in groups:
            name, _ = ALGORITHM_NAMES[group.algorithm_key]
            color = ALGORITHM_COLORS[name]
            values_t = group.values("j_t")
            values_r = group.values("j_r")
            axis.scatter(values_t, values_r, color=color, marker=WEIGHT_MARKERS.get(group.weight, "o"), alpha=0.28, s=25)
            best = group.best
            axis.scatter(best.j_t, best.j_r, color=color, marker=WEIGHT_MARKERS.get(group.weight, "o"), s=76, edgecolor="black", linewidth=0.45)
            axis.annotate(f"{ALGORITHM_NAMES[group.algorithm_key][1]} W{group.weight:g}", (best.j_t, best.j_r), xytext=(4, 4), textcoords="offset points", fontsize=7)
        axis.set(xlabel="$J_T$ (unweighted component)", ylabel="$J_R$ (unweighted component)", title="Weighted-reflection sensitivity: trade-off")
        axis.grid(True)
        _save(figure, root / "tradeoff_JT_JR.png")


def plot_weight_metric(groups: Sequence[WeightedGroup], metric: str, output: Path) -> None:
    label = {"j_t": "$J_T$", "j_r": "$J_R$", "j_unweighted": "$J_T + J_R$"}[metric]
    with plt.rc_context(PLOT_RC):
        figure, axis = plt.subplots(figsize=(7.8, 5.0), layout="constrained")
        for algorithm_key, algorithm_groups in _grouped(groups).items():
            name, _ = ALGORITHM_NAMES[algorithm_key]
            weights = np.asarray([group.weight for group in algorithm_groups])
            medians = np.asarray([np.median(group.values(metric)) for group in algorithm_groups])
            q1 = np.asarray([np.percentile(group.values(metric), 25.0) for group in algorithm_groups])
            q3 = np.asarray([np.percentile(group.values(metric), 75.0) for group in algorithm_groups])
            axis.plot(weights, medians, marker=ALGORITHM_MARKERS[algorithm_key], color=ALGORITHM_COLORS[name], label=name)
            axis.fill_between(weights, q1, q3, color=ALGORITHM_COLORS[name], alpha=0.18)
        axis.set_xscale("log")
        axis.set_xticks([1, 2, 5, 10], labels=["1", "2", "5", "10"])
        axis.set(xlabel="$w_R$ (log scale)", ylabel=label, title=f"Reflection weight versus {label}")
        axis.grid(True)
        axis.legend(title="Median (band: IQR)", loc="best")
        _save(figure, output)


def _as_algorithm_results(group: WeightedGroup) -> AlgorithmResults:
    name, short_name = ALGORITHM_NAMES[group.algorithm_key]
    runs = tuple(
        BenchmarkRun(
            seed=run.seed,
            budget=run.budget,
            n_evaluations=run.n_evaluations,
            best_J=run.j_weighted,
            best_J_T=run.j_t,
            best_J_R=run.j_r,
            best_p=run.best_p,
            T_theoretical=run.t_theoretical,
            R_theoretical=run.r_theoretical,
        )
        for run in group.runs
    )
    return AlgorithmResults(
        AlgorithmSpec(f"{name} — $w_R={group.weight:g}$", f"{short_name} W{group.weight:g}", group.directory, ALGORITHM_COLORS[name]),
        runs,
        {},
    )


def generate_best_fits(groups: Sequence[WeightedGroup], root: Path) -> None:
    results = tuple(_as_algorithm_results(group) for group in groups)
    limits = determine_best_fit_axis_limits(results)
    for group, result in zip(groups, results, strict=True):
        plot_best_fit(result, root / "best_fits" / f"{group.algorithm_key}_wR_{group.weight:g}.png", limits)
    for algorithm_key, algorithm_groups in _grouped(groups).items():
        comparable = tuple(_as_algorithm_results(group) for group in algorithm_groups)
        plot_best_fits_comparison(
            comparable,
            root / "best_fit_weight_effect" / f"{algorithm_key}_weight_effect.png",
            limits,
        )


def _median_line(group: WeightedGroup, metric: str) -> str:
    values = group.values(metric)
    q1, q3 = np.percentile(values, [25.0, 75.0])
    return f"{np.median(values):.9g} [{q1:.9g}, {q3:.9g}]"


def write_best_solutions(groups: Sequence[WeightedGroup], root: Path) -> None:
    fields = ["algorithm", "w_R", "seed", "J_T", "J_R", "J_unweighted", "J_weighted", "best_p", "best_z"]
    with (root / "best_solutions.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for group in sorted(groups, key=lambda item: (item.algorithm_key, item.weight)):
            best = group.best
            writer.writerow(
                {
                    "algorithm": ALGORITHM_NAMES[group.algorithm_key][0],
                    "w_R": f"{group.weight:.17g}",
                    "seed": best.seed,
                    "J_T": f"{best.j_t:.16g}",
                    "J_R": f"{best.j_r:.16g}",
                    "J_unweighted": f"{best.j_unweighted:.16g}",
                    "J_weighted": f"{best.j_weighted:.16g}",
                    "best_p": json.dumps(best.best_p.tolist()),
                    "best_z": json.dumps(best.best_z.tolist()),
                }
            )


def write_report(groups: Sequence[WeightedGroup], root: Path) -> None:
    rows = []
    for group in sorted(groups, key=lambda item: (item.algorithm_key, item.weight)):
        name, _ = ALGORITHM_NAMES[group.algorithm_key]
        rows.append(
            f"| {name} | {group.weight:g} | {_median_line(group, 'j_t')} | {_median_line(group, 'j_r')} | {_median_line(group, 'j_unweighted')} | {_median_line(group, 'j_weighted')} |"
        )
    change_lines: list[str] = []
    parameter_lines: list[str] = []
    parameter_names = ("log10_chi", "d2_nm", "n2_w", "n2_2w", "re_n3_w", "im_n3_w", "re_n3_2w", "im_n3_2w")
    for algorithm_key, algorithm_groups in _grouped(groups).items():
        baseline, highest = algorithm_groups[0], algorithm_groups[-1]
        name, _ = ALGORITHM_NAMES[algorithm_key]
        base_jt, high_jt = np.median(baseline.values("j_t")), np.median(highest.values("j_t"))
        base_jr, high_jr = np.median(baseline.values("j_r")), np.median(highest.values("j_r"))
        base_j, high_j = np.median(baseline.values("j_unweighted")), np.median(highest.values("j_unweighted"))
        change_lines.append(
            f"- **{name}:** W{baseline.weight:g} → W{highest.weight:g}: `J_R` {base_jr:.6g} → {high_jr:.6g} "
            f"({(high_jr / base_jr - 1.0) * 100.0:+.1f}%), `J_T` {base_jt:.6g} → {high_jt:.6g} "
            f"({(high_jt / base_jt - 1.0) * 100.0:+.1f}%), `J_unweighted` {base_j:.6g} → {high_j:.6g} "
            f"({(high_j / base_j - 1.0) * 100.0:+.1f}%)."
        )
        base_p = np.median(np.stack([run.best_p for run in baseline.runs]), axis=0)
        high_p = np.median(np.stack([run.best_p for run in highest.runs]), axis=0)
        shifts = ", ".join(
            f"{parameter_names[index]}: {base_p[index]:.4g}→{high_p[index]:.4g}"
            for index in range(base_p.size)
        )
        parameter_lines.append(f"- **{name}:** {shifts}.")
    lines = [
        "# Weighted-reflection sensitivity experiment",
        "",
        "This complementary screening preserves the scientific primary objective `J = J_T + J_R`. Each optimization uses `J_weighted = J_T + w_R J_R`; all conclusions below compare the unweighted components separately. Results are five-seed descriptive summaries, not formal statistical inference.",
        "",
        "## Median [Q1, Q3] by algorithm and reflection weight",
        "",
        "| Algorithm | w_R | J_T | J_R | J_unweighted | J_weighted |",
        "|---|---:|---:|---:|---:|---:|",
        *rows,
        "",
        "## W1 to highest-weight trade-off",
        "",
        *change_lines,
        "",
        "Across the converged DE and PSO runs, W2 already reduces median `J_R` by about 10% relative to W1 with a much smaller `J_T` cost than W5/W10. GA also shows a lower median unweighted error at W2, but with wider run-to-run spread; Random Search remains much more variable. Therefore W2 is a provisional compromise worth follow-up, not a definitive choice.",
        "",
        "## Physical parameter migration",
        "",
        *parameter_lines,
        "",
        "The W1→W10 summaries and `best_solutions.csv` make parameter migration and possible boundary behavior explicit. The trade-off plot marks each group’s lowest weighted solution and shows every seed lightly; the standard best-fit panels permit curve-level inspection. None of these five-seed observations is formal statistical inference.",
    ]
    (root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=ROOT / "results" / "weighted_reflection")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    groups = load_groups(arguments.results_root)
    plot_tradeoff(groups, arguments.results_root)
    plot_weight_metric(groups, "j_t", arguments.results_root / "weight_vs_JT.png")
    plot_weight_metric(groups, "j_r", arguments.results_root / "weight_vs_JR.png")
    plot_weight_metric(groups, "j_unweighted", arguments.results_root / "weight_vs_unweighted_J.png")
    generate_best_fits(groups, arguments.results_root)
    write_best_solutions(groups, arguments.results_root)
    write_report(groups, arguments.results_root)
    print(f"groups={len(groups)} figures_and_report_written_to={arguments.results_root}")


if __name__ == "__main__":
    main()
