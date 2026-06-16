"""Matplotlib cross-section fallback for tokamak candidates."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, Rectangle

from mini_tokamak.schemas import Candidate


def export_cross_section(candidate: Candidate, output_dir: str | Path) -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    base = out / f"{candidate.candidate_id}_cross_section"

    fig, ax = plt.subplots(figsize=(7, 5), dpi=160)
    ax.set_title(f"{candidate.machine_type} low-fidelity cross-section")
    ax.set_xlabel("Radial coordinate R (m)")
    ax.set_ylabel("Vertical coordinate Z (m)")

    plasma = Ellipse(
        (candidate.R, 0.0),
        width=2.0 * candidate.a,
        height=2.0 * candidate.kappa * candidate.a,
        facecolor="#f4a261",
        edgecolor="#7f1d1d",
        alpha=0.55,
        linewidth=1.5,
        label="plasma boundary proxy",
    )
    wall = Ellipse(
        (candidate.R, 0.0),
        width=2.0 * (candidate.a + candidate.first_wall_thickness),
        height=2.0 * (candidate.kappa * candidate.a + candidate.first_wall_thickness),
        fill=False,
        edgecolor="#264653",
        linewidth=2.0,
        label="first wall proxy",
    )
    shield = Ellipse(
        (candidate.R, 0.0),
        width=2.0 * (candidate.a + candidate.first_wall_thickness + candidate.shield_thickness),
        height=2.0
        * (candidate.kappa * candidate.a + candidate.first_wall_thickness + candidate.shield_thickness),
        fill=False,
        edgecolor="#2a9d8f",
        linewidth=2.0,
        linestyle="--",
        label="shield envelope proxy",
    )
    center_column = Rectangle(
        (-candidate.center_column_radius, -candidate.machine_height / 2.0),
        2.0 * candidate.center_column_radius,
        candidate.machine_height,
        facecolor="#6c757d",
        edgecolor="#343a40",
        alpha=0.35,
        label="center column proxy",
    )

    for patch in [shield, wall, plasma, center_column]:
        ax.add_patch(patch)

    max_x = max(candidate.machine_length / 2.0, candidate.R + candidate.a + candidate.shield_thickness)
    max_z = max(candidate.machine_height / 2.0, candidate.kappa * candidate.a + candidate.shield_thickness)
    ax.set_xlim(-0.15 - candidate.center_column_radius, max_x + 0.25)
    ax.set_ylim(-max_z - 0.25, max_z + 0.25)
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", fontsize=7)
    ax.text(
        0.02,
        0.02,
        "LOW_FIDELITY_PLACEHOLDER CAD - not construction geometry",
        transform=ax.transAxes,
        fontsize=7,
        color="#8a1f11",
    )

    png_path = base.with_suffix(".png")
    svg_path = base.with_suffix(".svg")
    fig.tight_layout()
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)
    return {"png": str(png_path), "svg": str(svg_path)}

