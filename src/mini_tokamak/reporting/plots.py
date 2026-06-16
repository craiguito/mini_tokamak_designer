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


def generate_plots(results: list[CandidateResult], output_dir: str | Path) -> list[str]:
    if not results:
        return []
    return [plot_score_scatter(results, output_dir), plot_failure_counts(results, output_dir)]

