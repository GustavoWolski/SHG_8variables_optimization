"""Run local and global one-at-a-time sensitivity sweeps for a fixed solution."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis.sensitivity import (  # noqa: E402
    SensitivitySweep,
    approximate_curvature,
    local_minimum_indices,
    sweep_parameter,
    threshold_region_width,
)
from optimization.constraints import PARAMETER_DEFINITIONS  # noqa: E402
from optimization.objective import evaluate  # noqa: E402


DEFAULT_REFERENCE_P = np.asarray(
    [
        9.421418687715693,
        -20.0,
        0.9195367992456922,
        1.340568195726079,
        3.042988463684585,
        0.4162676918468047,
    ],
    dtype=np.float64,
)
DEFAULT_EXPECTED_J = 0.4197060799905111
SCIENTIFIC_LABELS = (
    r"$\log_{10}(\chi)$",
    r"$\Delta d_3$ (nm)",
    r"Re$(n_{31\omega})$",
    r"Im$(n_{31\omega})$",
    r"Re$(n_{32\omega})$",
    r"Im$(n_{32\omega})$",
)


def _write_sweep_csv(path: Path, sweeps: tuple[SensitivitySweep, SensitivitySweep]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("scale", "grid_index", "parameter_value", "J", "J_T", "J_R"),
        )
        writer.writeheader()
        for sweep in sweeps:
            for index, (value, j, j_t, j_r) in enumerate(
                zip(sweep.values, sweep.J, sweep.J_T, sweep.J_R, strict=True)
            ):
                writer.writerow(
                    {
                        "scale": sweep.scale,
                        "grid_index": index,
                        "parameter_value": f"{value:.17g}",
                        "J": f"{j:.17g}",
                        "J_T": f"{j_t:.17g}",
                        "J_R": f"{j_r:.17g}",
                    }
                )


def _plot_sweeps(
    sweeps: list[SensitivitySweep],
    p_reference: np.ndarray,
    reference_J: float,
    output_stem: Path,
) -> None:
    figure, axes = plt.subplots(2, 3, figsize=(14.0, 8.2), layout="constrained")
    for index, (axis, sweep) in enumerate(zip(axes.flat, sweeps, strict=True)):
        reference_value = float(p_reference[index])
        minimum_index = int(np.argmin(sweep.J))
        axis.plot(sweep.values, sweep.J, color="#0072B2", linewidth=1.5)
        axis.scatter(sweep.values, sweep.J, color="#0072B2", s=9, alpha=0.60, zorder=3)
        axis.axvline(reference_value, color="#D55E00", linestyle="--", linewidth=1.1)
        axis.scatter([reference_value], [reference_J], marker="*", s=110, color="#D55E00", zorder=5)
        axis.scatter(
            [sweep.values[minimum_index]],
            [sweep.J[minimum_index]],
            marker="X",
            s=65,
            color="#111111",
            zorder=6,
        )
        definition = PARAMETER_DEFINITIONS[index]
        if np.isclose(reference_value, definition.lower) or np.isclose(reference_value, definition.upper):
            axis.text(
                0.03,
                0.95,
                "reference at bound",
                transform=axis.transAxes,
                ha="left",
                va="top",
                fontsize=8,
                color="#D55E00",
            )
        axis.set_xlabel(SCIENTIFIC_LABELS[index])
        axis.set_ylabel("Objective J")
        axis.grid(True, alpha=0.30)
    figure.legend(
        [axes.flat[0].lines[0], axes.flat[0].collections[1], axes.flat[0].collections[2]],
        ["Sensitivity sweep", "Reference value", "Sweep minimum"],
        loc="outside lower center",
        ncol=3,
    )
    figure.suptitle(f"One-at-a-time sensitivity — {sweeps[0].scale} scale")
    figure.savefig(output_stem.with_suffix(".png"), dpi=320, facecolor="white", bbox_inches="tight")
    figure.savefig(output_stem.with_suffix(".pdf"), facecolor="white", bbox_inches="tight")
    plt.close(figure)


def _classifications(rows: list[dict[str, object]]) -> dict[str, str]:
    ordered = sorted(
        rows,
        key=lambda row: (
            float(row["normalized_width_1pct"]),
            -float(row["global_J_range"]),
        ),
    )
    labels = ("mais sensível", "mais sensível", "intermediário", "intermediário", "menos sensível", "menos sensível")
    return {str(row["parameter"]): label for row, label in zip(ordered, labels, strict=True)}


def _summary_rows(
    local_sweeps: list[SensitivitySweep],
    global_sweeps: list[SensitivitySweep],
    p_reference: np.ndarray,
    reference_J: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, (local, global_) in enumerate(zip(local_sweeps, global_sweeps, strict=True)):
        definition = PARAMETER_DEFINITIONS[index]
        global_minimum = int(np.argmin(global_.J))
        local_minimum = int(np.argmin(local.J))
        width_1 = threshold_region_width(local, p_reference[index], reference_J, 0.01)
        width_5 = threshold_region_width(local, p_reference[index], reference_J, 0.05)
        span = definition.upper - definition.lower
        minima = local_minimum_indices(global_)
        rows.append(
            {
                "parameter": definition.name,
                "scientific_label": SCIENTIFIC_LABELS[index],
                "reference_value": float(p_reference[index]),
                "J_reference": reference_J,
                "local_min_value": float(local.values[local_minimum]),
                "local_J_min": float(local.J[local_minimum]),
                "local_delta_J_min": float(local.J[local_minimum] - reference_J),
                "global_min_value": float(global_.values[global_minimum]),
                "global_J_min": float(global_.J[global_minimum]),
                "global_delta_J_min": float(global_.J[global_minimum] - reference_J),
                "local_curvature": approximate_curvature(local, float(p_reference[index])),
                "width_1pct": width_1,
                "width_5pct": width_5,
                "normalized_width_1pct": width_1 / span,
                "normalized_width_5pct": width_5 / span,
                "global_J_range": float(np.ptp(global_.J)),
                "reference_at_bound": bool(
                    np.isclose(p_reference[index], definition.lower)
                    or np.isclose(p_reference[index], definition.upper)
                ),
                "grid_local_minima_count": int(minima.size),
                "grid_local_minima_values": ";".join(f"{global_.values[item]:.17g}" for item in minima),
            }
        )
    classifications = _classifications(rows)
    for row in rows:
        row["qualitative_sensitivity"] = classifications[str(row["parameter"])]
    return rows


def _write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_report(
    path: Path,
    rows: list[dict[str, object]],
    reference_result: object,
    reference_label: str,
) -> None:
    by_classification: dict[str, list[str]] = {}
    for row in rows:
        by_classification.setdefault(str(row["qualitative_sensitivity"]), []).append(str(row["parameter"]))
    multiple = [row for row in rows if int(row["grid_local_minima_count"]) > 1]
    lines = [
        "# Análise de sensibilidade 1D da solução de referência", "",
        "## Validação", "",
        f"- `J(p*) = {reference_result.J:.17g}`.",
        f"- `J_T = {reference_result.J_T:.17g}`; `J_R = {reference_result.J_R:.17g}`.",
        "- A identidade `J = J_T + J_R` foi preservada.",
        f"- Vetor analisado: `{reference_label}`.", "",
        "## Grids e custo", "",
        "- Global: 101 pontos uniformes entre os bounds completos de cada parâmetro.",
        "- Local: 101 pontos em uma janela de ±10% da amplitude do bound, truncada pelos bounds e contendo exatamente p*. Em janelas assimétricas truncadas, os dois lados usam espaçamento aproximadamente uniforme.",
        "- Total: 1.212 avaliações físicas, sem reotimização e sem execução de RS, DE, GA ou PSO.", "",
        "## Sensibilidade relativa", "",
    ]
    for category in ("mais sensível", "intermediário", "menos sensível"):
        lines.append(f"- {category.capitalize()}: `{', '.join(by_classification.get(category, []))}`.")
    lines.extend([
        "", "A classificação ordena primeiro a largura normalizada do vale local até 1% acima de J(p*) e usa a amplitude global de J como desempate. É um indicador prático, não um intervalo de confiança.", "",
        "## Métricas", "",
        "| Parâmetro | Classe | Curvatura local | Largura 1% | Largura 5% | J mínimo global | x no mínimo |",
        "|---|---|---:|---:|---:|---:|---:|",
    ])
    for row in rows:
        lines.append(
            f"| {row['parameter']} | {row['qualitative_sensitivity']} | {float(row['local_curvature']):.6g} | "
            f"{float(row['width_1pct']):.6g} | {float(row['width_5pct']):.6g} | "
            f"{float(row['global_J_min']):.12g} | {float(row['global_min_value']):.12g} |"
        )
    delta = next(row for row in rows if row["parameter"] == "delta_d3_nm")
    delta_at_bound = bool(delta["reference_at_bound"])
    delta_boundary_text = (
        f"- `delta_d3_nm = {float(delta['reference_value']):.12g} nm` está em um bound do espaço oficial; "
        "a varredura não extrapola o espaço e não sustenta a afirmação de mínimo local interior."
        if delta_at_bound
        else f"- `delta_d3_nm = {float(delta['reference_value']):.12g} nm` está no interior do espaço oficial."
    )
    lines.extend([
        "", "## Boundary e múltiplos mínimos", "",
        delta_boundary_text,
        f"- Na grade global, `delta_d3_nm` teve mínimo em `{float(delta['global_min_value']):.12g}` nm.",
    ])
    if multiple:
        for row in multiple:
            lines.append(
                f"- `{row['parameter']}` apresentou {row['grid_local_minima_count']} mínimos locais resolvidos pela grade, em `{row['grid_local_minima_values']}`. Isso é apenas indício 1D dependente da resolução."
            )
    else:
        lines.append("- Nenhum parâmetro apresentou mais de um mínimo local resolvido pela grade global de 101 pontos.")
    lines.extend([
        "", "## Limitações", "",
        "Esta análise varia um parâmetro por vez e mantém os demais exatamente fixos. Ela não detecta compensações ou correlações entre parâmetros, não incorpora incerteza experimental e não estabelece identificabilidade formal.", "",
        "Os CSVs individuais contêm as duas escalas e registram `scale`, `parameter_value`, `J`, `J_T` e `J_R` para cada avaliação.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "results" / "benchmark_bounds_0p1_10_run01" / "sensitivity",
    )
    parser.add_argument(
        "--reference-p",
        type=float,
        nargs=6,
        default=None,
        metavar=("LOG10_CHI", "DELTA_D3", "N3_W", "K3_W", "N3_2W", "K3_2W"),
        help="Physical reference vector. Defaults to the historical PSO seed 4 vector.",
    )
    parser.add_argument(
        "--reference-label",
        default="PSO seed 4 do benchmark bounds_0p1_10_run01",
        help="Human-readable reference identification written to the report.",
    )
    parser.add_argument(
        "--expected-j",
        type=float,
        default=None,
        help="Optional exact-reference guard checked with absolute tolerance 1e-12.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace sensitivity artifacts in the output directory.")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    p_reference = np.asarray(
        DEFAULT_REFERENCE_P if arguments.reference_p is None else arguments.reference_p,
        dtype=np.float64,
    )
    expected_j = DEFAULT_EXPECTED_J if arguments.reference_p is None and arguments.expected_j is None else arguments.expected_j
    reference_result = evaluate(p_reference)
    if expected_j is not None and not np.isclose(reference_result.J, expected_j, rtol=0.0, atol=1e-12):
        raise RuntimeError(f"Reference validation failed: {reference_result.J} != {expected_j}")
    if arguments.output_dir.exists() and any(arguments.output_dir.iterdir()) and not arguments.overwrite:
        raise FileExistsError(f"Refusing to overwrite non-empty output directory: {arguments.output_dir}")
    arguments.output_dir.mkdir(parents=True, exist_ok=True)

    local_sweeps = [sweep_parameter(p_reference, index, "local") for index in range(6)]
    global_sweeps = [sweep_parameter(p_reference, index, "global") for index in range(6)]
    for index, definition in enumerate(PARAMETER_DEFINITIONS):
        _write_sweep_csv(
            arguments.output_dir / f"sensitivity_{definition.name}.csv",
            (local_sweeps[index], global_sweeps[index]),
        )
    _plot_sweeps(global_sweeps, p_reference, reference_result.J, arguments.output_dir / "sensitivity_global")
    _plot_sweeps(local_sweeps, p_reference, reference_result.J, arguments.output_dir / "sensitivity_local")
    rows = _summary_rows(local_sweeps, global_sweeps, p_reference, reference_result.J)
    _write_summary(arguments.output_dir / "sensitivity_summary.csv", rows)
    _write_report(arguments.output_dir / "sensitivity_report.md", rows, reference_result, arguments.reference_label)

    print(f"J_reference={reference_result.J:.17g}")
    print(f"sweep_evaluations={sum(item.n_evaluations for item in local_sweeps + global_sweeps)}")
    print(f"output={arguments.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
