"""Plot generation for run reports."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mini_tokamak.reporting.failure_report import dominant_failure_counts
from mini_tokamak.schemas import CandidateResult


def plot_score_scatter(results: list[CandidateResult], output_dir: str | Path) -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "score_vs_major_radius.png"

    fig, ax = plt.subplots(figsize=(7, 4), dpi=160)
    xs = [result.candidate.R for result in results]
    ys = [result.objective_score for result in results]
    colors = ["#2a9d8f" if not any(c.status == "FAIL" for c in r.constraints.checks) else "#e76f51" for r in results]
    ax.scatter(xs, ys, c=colors, alpha=0.75, s=24)
    ax.set_xlabel("Major radius R (m)")
    ax.set_ylabel("Objective score")
    ax.set_title("Random search score distribution")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def plot_failure_counts(results: list[CandidateResult], output_dir: str | Path) -> str:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "dominant_failure_counts.png"
    counts = dominant_failure_counts(results)
    labels = list(counts.keys())
    values = [counts[label] for label in labels]

    fig, ax = plt.subplots(figsize=(8, 4), dpi=160)
    ax.bar(labels, values, color="#457b9d")
    ax.set_ylabel("Candidates")
    ax.set_title("Dominant low-fidelity failure reasons")
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def plot_torax_transport_comparison(results: list[CandidateResult], output_dir: str | Path) -> str | None:
    rows = _executed_torax_rows(results)
    if not rows:
        return None

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "torax_transport_comparison.png"

    labels = [f"#{row['rank']} {row['candidate_id']}" for row in rows]
    q95_values = [row["q95"] for row in rows]
    heat_values = [row["heat_load"] for row in rows]
    fgw_values = [row["fgw_line"] for row in rows]

    fig, axes = plt.subplots(3, 1, figsize=(8, 7), dpi=160, sharex=True)
    _bar_with_thresholds(
        axes[0],
        labels,
        q95_values,
        ylabel="q95",
        title="TORAX top-candidate transport comparison",
        warning=3.0,
        fail=2.0,
        lower_is_worse=True,
    )
    _bar_with_thresholds(
        axes[1],
        labels,
        heat_values,
        ylabel="P_SOL/A (MW/m2)",
        warning=10.0,
        fail=25.0,
        lower_is_worse=False,
    )
    _bar_with_thresholds(
        axes[2],
        labels,
        fgw_values,
        ylabel="fGW line",
        warning=0.8,
        fail=1.0,
        lower_is_worse=False,
    )
    axes[2].tick_params(axis="x", labelrotation=25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)


def _executed_torax_rows(results: list[CandidateResult]) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for rank, result in enumerate(results, start=1):
        solver = next(
            (
                item
                for item in result.solver_results
                if item.solver == "TORAX" and item.metrics.get("stage") == "run_torax"
            ),
            None,
        )
        if solver is None:
            continue
        metrics = solver.metrics
        rows.append(
            {
                "rank": int(metrics.get("top_candidate_rank") or rank),
                "candidate_id": result.candidate.candidate_id[:8],
                "q95": _float_or_nan(metrics.get("torax_final_q95")),
                "heat_load": _float_or_nan(metrics.get("torax_final_SOL_heat_load_MW_m2")),
                "fgw_line": _float_or_nan(metrics.get("torax_final_fgw_n_e_line_avg")),
            }
        )
    return sorted(rows, key=lambda row: int(row["rank"]))


def _bar_with_thresholds(
    ax: object,
    labels: list[str],
    values: list[float],
    *,
    ylabel: str,
    title: str | None = None,
    warning: float,
    fail: float,
    lower_is_worse: bool,
) -> None:
    colors = [_status_color(value, warning=warning, fail=fail, lower_is_worse=lower_is_worse) for value in values]
    ax.bar(labels, values, color=colors)
    ax.axhline(warning, color="#f4a261", linestyle="--", linewidth=1.0, alpha=0.9)
    ax.axhline(fail, color="#e76f51", linestyle="--", linewidth=1.0, alpha=0.9)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(axis="y", alpha=0.25)


def _status_color(value: float, *, warning: float, fail: float, lower_is_worse: bool) -> str:
    if lower_is_worse:
        if value < fail:
            return "#e76f51"
        if value < warning:
            return "#f4a261"
        return "#2a9d8f"
    if value > fail:
        return "#e76f51"
    if value > warning:
        return "#f4a261"
    return "#2a9d8f"


def _float_or_nan(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def generate_plots(results: list[CandidateResult], output_dir: str | Path) -> list[str]:
    if not results:
        return []
    paths = [plot_score_scatter(results, output_dir), plot_failure_counts(results, output_dir)]
    torax_path = plot_torax_transport_comparison(results, output_dir)
    if torax_path is not None:
        paths.append(torax_path)
    return paths
