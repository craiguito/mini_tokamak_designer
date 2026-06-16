"""Filesystem run-store helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pandas as pd

from mini_tokamak.schemas import CandidateResult


def make_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid4().hex[:8]}"


def ensure_run_dirs(project_root: str | Path, run_id: str) -> dict[str, Path]:
    root = Path(project_root)
    run_dir = root / "data" / "runs" / run_id
    dirs = {
        "run": run_dir,
        "results": run_dir / "results",
        "plots": run_dir / "plots",
        "cad": root / "data" / "cad" / run_id,
        "reports": root / "data" / "reports" / run_id,
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def write_candidate_json(result: CandidateResult, results_dir: str | Path) -> Path:
    path = Path(results_dir) / f"{result.candidate.candidate_id}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(result.model_dump(mode="json"), handle, indent=2)
    return path


def write_all_results(results: list[CandidateResult], path: str | Path) -> Path:
    out = Path(path)
    with out.open("w", encoding="utf-8") as handle:
        json.dump([r.model_dump(mode="json") for r in results], handle, indent=2)
    return out


def results_dataframe(results: list[CandidateResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        c = result.candidate
        rows.append(
            {
                "run_id": result.run_id,
                "candidate_id": c.candidate_id,
                "objective_score": result.objective_score,
                "feasibility_score": result.constraints.feasibility_score,
                "dominant_failure_reason": result.constraints.dominant_failure_reason,
                "machine_type": c.machine_type,
                "fuel_mode": c.fuel_mode,
                "R": c.R,
                "a": c.a,
                "aspect_ratio": c.aspect_ratio,
                "kappa": c.kappa,
                "delta": c.delta,
                "Bt": c.Bt,
                "Ip": c.Ip,
                "heating_power": c.heating_power,
                "shield_thickness": c.shield_thickness,
                "first_wall_thickness": c.first_wall_thickness,
                "center_column_radius": c.center_column_radius,
                "machine_width": c.machine_width,
                "machine_height": c.machine_height,
                "estimated_plasma_volume": c.estimated_plasma_volume,
                **{
                    f"metric_{key}": value
                    for key, value in result.constraints.metrics.items()
                    if isinstance(value, int | float | str | bool)
                },
            }
        )
    return pd.DataFrame(rows)


def write_top_csv(results: list[CandidateResult], output_path: str | Path, limit: int = 20) -> Path:
    df = results_dataframe(results).sort_values("objective_score", ascending=False).head(limit)
    out = Path(output_path)
    df.to_csv(out, index=False)
    return out

