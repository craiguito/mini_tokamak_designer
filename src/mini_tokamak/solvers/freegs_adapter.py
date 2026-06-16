"""FreeGS equilibrium adapter."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter, module_available


GRID_ENV_VAR = "MINI_TOKAMAK_FREEGS_GRID"
MAXITS_ENV_VAR = "MINI_TOKAMAK_FREEGS_MAXITS"
RTOL_ENV_VAR = "MINI_TOKAMAK_FREEGS_RTOL"


class FreeGSAdapter(SolverAdapter):
    name = "FreeGS"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._run_root: Path | None = None

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        self._run_root = Path(output_dir)
        self._run_root.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        if self._available is None:
            self._available = module_available(["freegs"])
        return self._available

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, "FreeGS is not importable in this environment.")

        run_dir = self._candidate_run_dir(candidate)
        candidate_path = run_dir / "candidate.json"
        boundary_path = run_dir / "miller_boundary.json"
        result_path = run_dir / "freegs_result.json"
        field_path = run_dir / "freegs_fields.npz"
        plot_path = run_dir / "freegs_equilibrium.png"

        candidate_path.write_text(
            json.dumps(candidate.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

        try:
            metrics = self._run_fixed_boundary_sanity(
                candidate=candidate,
                boundary_path=boundary_path,
                field_path=field_path,
                plot_path=plot_path,
            )
        except Exception as exc:
            metrics = {
                "candidate_id": candidate.candidate_id,
                "julia_status": "NOT_APPLICABLE",
                "freegs_status": "FAIL",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "candidate_path": str(candidate_path),
                "boundary_path": str(boundary_path) if boundary_path.exists() else None,
            }
            result_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
            return SolverResult(
                solver=self.name,
                status="FAIL",
                available=True,
                metrics=metrics,
                message="FreeGS fixed-boundary sanity check failed; inspect result JSON.",
                raw_output_path=str(result_path),
            )

        metrics.update(
            {
                "candidate_id": candidate.candidate_id,
                "candidate_path": str(candidate_path),
                "boundary_path": str(boundary_path),
                "field_path": str(field_path) if field_path.exists() else None,
                "plot_path": str(plot_path) if plot_path.exists() else None,
                "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
            }
        )
        result_path.write_text(json.dumps(_json_ready(metrics), indent=2), encoding="utf-8")

        failed = metrics.get("freegs_status") == "FAIL"
        return SolverResult(
            solver=self.name,
            status="FAIL" if failed else "WARNING",
            available=True,
            metrics=metrics,
            message=(
                "FreeGS equilibrium sanity check failed; inspect generated artifacts."
                if failed
                else (
                    "FreeGS fixed-boundary equilibrium sanity check completed. Treat as "
                    "plasma-boundary consistency evidence, not a free-boundary design."
                )
            ),
            raw_output_path=str(result_path),
        )

    def parse_results(self, raw: object) -> dict[str, object]:
        path = Path(raw)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"parse_error": str(exc)}
        return data if isinstance(data, dict) else {"raw": data}

    def _run_fixed_boundary_sanity(
        self,
        candidate: Candidate,
        boundary_path: Path,
        field_path: Path,
        plot_path: Path,
    ) -> dict[str, Any]:
        from freegs import boundary, critical, equilibrium, jtor, picard

        _install_fixed_boundary_critical_fallback(critical, equilibrium, jtor)

        boundary_points = miller_boundary_points(candidate)
        geometry = boundary_geometry_metrics(candidate, boundary_points)
        coil_layout = rough_pf_coil_layout(candidate, boundary_points)
        boundary_path.write_text(
            json.dumps(
                {
                    "candidate_id": candidate.candidate_id,
                    "boundary_model": "Miller-like target boundary",
                    "R": boundary_points["R"].tolist(),
                    "Z": boundary_points["Z"].tolist(),
                    "geometry_metrics": geometry,
                    "rough_pf_coil_layout": coil_layout,
                    "note": "Research geometry only; not construction coil geometry.",
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        geometry_failures = _geometry_failures(candidate, geometry, coil_layout)
        if geometry_failures:
            return {
                "freegs_status": "FAIL",
                "stage": "geometry_precheck",
                "geometry_failures": geometry_failures,
                **geometry,
                **_prefixed("rough_pf_", coil_layout),
            }

        grid = _grid_size()
        rmin, rmax, zmin, zmax = _domain(candidate, boundary_points)
        eq = equilibrium.Equilibrium(
            Rmin=rmin,
            Rmax=rmax,
            Zmin=zmin,
            Zmax=zmax,
            nx=grid,
            ny=grid,
            boundary=boundary.fixedBoundary,
            current=candidate.Ip * 1.0e6,
            order=2,
        )

        fvac = max(1.0e-6, candidate.R * candidate.Bt)
        p_axis = _pressure_axis_proxy(candidate)
        profiles = jtor.ConstrainPaxisIp(eq, p_axis, candidate.Ip * 1.0e6, fvac)

        picard.solve(eq, profiles, rtol=_rtol(), maxits=_maxits())

        psi = np.asarray(eq.psi())
        if not np.all(np.isfinite(psi)):
            raise ValueError("FreeGS returned non-finite psi values.")
        if float(np.ptp(psi)) <= 0.0:
            raise ValueError("FreeGS returned a zero-range psi field.")

        np.savez_compressed(
            field_path,
            R=np.asarray(eq.R),
            Z=np.asarray(eq.Z),
            psi=psi,
            target_R=boundary_points["R"],
            target_Z=boundary_points["Z"],
        )
        _plot_equilibrium(eq, boundary_points, coil_layout, plot_path)

        solved_metrics = _safe_equilibrium_metrics(eq)
        return {
            "freegs_status": "PASS",
            "stage": "fixed_boundary_picard",
            "freegs_model": "fixed-boundary Grad-Shafranov sanity check",
            "critical_point_finder": "adapter_local_fixed_boundary_fallback",
            "grid": grid,
            "rtol": _rtol(),
            "maxits": _maxits(),
            "Rmin": rmin,
            "Rmax": rmax,
            "Zmin": zmin,
            "Zmax": zmax,
            "fvac_RBt": fvac,
            "p_axis_proxy_Pa": p_axis,
            "psi_min": float(np.min(psi)),
            "psi_max": float(np.max(psi)),
            "psi_range": float(np.ptp(psi)),
            **geometry,
            **_prefixed("rough_pf_", coil_layout),
            **solved_metrics,
        }

    def _candidate_run_dir(self, candidate: Candidate) -> Path:
        root = self._run_root or (Path.cwd() / "data" / "runs" / "freegs_standalone")
        run_dir = root / candidate.candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


def miller_boundary_points(candidate: Candidate, n: int = 181) -> dict[str, np.ndarray]:
    theta = np.linspace(0.0, 2.0 * math.pi, n)
    r = candidate.R + candidate.a * np.cos(theta + candidate.delta * np.sin(theta))
    z = candidate.kappa * candidate.a * np.sin(theta)
    return {"theta": theta, "R": r, "Z": z}


def boundary_geometry_metrics(
    candidate: Candidate,
    boundary_points: dict[str, np.ndarray],
) -> dict[str, float | bool]:
    r = boundary_points["R"]
    z = boundary_points["Z"]
    min_r = float(np.min(r))
    max_r = float(np.max(r))
    min_z = float(np.min(z))
    max_z = float(np.max(z))
    inboard_gap = candidate.R - candidate.a - candidate.center_column_radius
    return {
        "target_min_R_m": min_r,
        "target_max_R_m": max_r,
        "target_min_Z_m": min_z,
        "target_max_Z_m": max_z,
        "target_width_m": max_r - min_r,
        "target_height_m": max_z - min_z,
        "target_inboard_gap_m": inboard_gap,
        "target_min_R_positive": min_r > 0.0,
        "center_column_clearance_ok": inboard_gap > 0.0,
        "elongation_target": candidate.kappa,
        "triangularity_target": candidate.delta,
    }


def rough_pf_coil_layout(
    candidate: Candidate,
    boundary_points: dict[str, np.ndarray],
) -> dict[str, Any]:
    r_boundary_max = float(np.max(boundary_points["R"]))
    z_abs_max = float(np.max(np.abs(boundary_points["Z"])))
    radial_clearance = max(0.08, 0.20 * candidate.a)
    vertical_clearance = max(0.08, 0.20 * candidate.a)
    coil_r = r_boundary_max + radial_clearance
    coil_z = z_abs_max + vertical_clearance
    outer_radius_with_pf = coil_r + max(0.04, 0.10 * candidate.a)
    machine_radius = candidate.machine_width / 2.0
    return {
        "coil_centers": [
            {"name": "PF_UPPER_PROXY", "R": coil_r, "Z": coil_z},
            {"name": "PF_LOWER_PROXY", "R": coil_r, "Z": -coil_z},
        ],
        "radial_clearance_m": radial_clearance,
        "vertical_clearance_m": vertical_clearance,
        "outer_radius_with_pf_m": outer_radius_with_pf,
        "machine_radius_proxy_m": machine_radius,
        "pf_radial_fit_ok": outer_radius_with_pf <= machine_radius + 1.0e-9,
    }


def _geometry_failures(
    candidate: Candidate,
    geometry: dict[str, Any],
    coil_layout: dict[str, Any],
) -> list[str]:
    failures: list[str] = []
    if not geometry["target_min_R_positive"]:
        failures.append("target_boundary_crosses_R_axis")
    if not geometry["center_column_clearance_ok"]:
        failures.append("target_boundary_overlaps_center_column")
    if candidate.a <= 0.0 or candidate.R <= 0.0:
        failures.append("non_positive_major_or_minor_radius")
    if candidate.kappa <= 0.0:
        failures.append("non_positive_elongation")
    if not coil_layout["pf_radial_fit_ok"]:
        failures.append("rough_pf_coils_exceed_machine_radius_proxy")
    return failures


def _domain(candidate: Candidate, boundary_points: dict[str, np.ndarray]) -> tuple[float, float, float, float]:
    radial_pad = max(0.12, 0.35 * candidate.a, candidate.first_wall_thickness + 0.05)
    vertical_pad = max(0.12, 0.25 * candidate.kappa * candidate.a)
    rmin = max(0.02, float(np.min(boundary_points["R"])) - radial_pad)
    rmax = float(np.max(boundary_points["R"])) + radial_pad
    zmin = float(np.min(boundary_points["Z"])) - vertical_pad
    zmax = float(np.max(boundary_points["Z"])) + vertical_pad
    return rmin, rmax, zmin, zmax


def _pressure_axis_proxy(candidate: Candidate) -> float:
    return float(min(2.0e5, max(1.0e3, 5.0e3 * candidate.heating_power)))


def _safe_equilibrium_metrics(eq: Any) -> dict[str, float | str]:
    metrics: dict[str, float | str] = {}
    for name, func in {
        "plasma_current_A": eq.plasmaCurrent,
        "plasma_volume_m3": eq.plasmaVolume,
        "poloidal_beta": eq.poloidalBeta,
        "magnetic_axis_R_m": eq.Rmagnetic,
        "magnetic_axis_Z_m": eq.Zmagnetic,
        "minor_radius_m": eq.minorRadius,
        "aspect_ratio": eq.aspectRatio,
        "elongation": eq.elongation,
        "triangularity": eq.triangularity,
    }.items():
        try:
            value = func()
            if np.isfinite(value):
                metrics[name] = float(value)
        except Exception as exc:
            metrics[f"{name}_error"] = str(exc)
    try:
        q_values = eq.q(npsi=25)
        q_array = np.asarray(q_values, dtype=float)
        finite = q_array[np.isfinite(q_array)]
        if finite.size:
            metrics["q_min"] = float(np.min(finite))
            metrics["q_axis_proxy"] = float(finite[0])
            metrics["q_edge_proxy"] = float(finite[-1])
    except Exception as exc:
        metrics["q_profile_error"] = str(exc)
    return metrics


def _plot_equilibrium(
    eq: Any,
    boundary_points: dict[str, np.ndarray],
    coil_layout: dict[str, Any],
    plot_path: Path,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 6))
    psi = np.asarray(eq.psi())
    levels = np.linspace(float(np.min(psi)), float(np.max(psi)), 40)
    ax.contour(eq.R, eq.Z, psi, levels=levels, linewidths=0.8)
    ax.plot(boundary_points["R"], boundary_points["Z"], "r-", linewidth=2.0, label="target boundary")
    for coil in coil_layout["coil_centers"]:
        ax.plot(coil["R"], coil["Z"], "ks", markersize=5)
        ax.text(coil["R"], coil["Z"], coil["name"].replace("_PROXY", ""), fontsize=7)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("R [m]")
    ax.set_ylabel("Z [m]")
    ax.set_title("FreeGS fixed-boundary sanity check")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=140)
    plt.close(fig)


def _grid_size() -> int:
    raw = os.environ.get(GRID_ENV_VAR, "33")
    try:
        grid = int(raw)
    except ValueError:
        grid = 33
    allowed = [17, 33, 65, 129]
    return min(allowed, key=lambda item: abs(item - grid))


def _maxits() -> int:
    try:
        return max(1, int(os.environ.get(MAXITS_ENV_VAR, "25")))
    except ValueError:
        return 25


def _rtol() -> float:
    try:
        return max(1.0e-8, float(os.environ.get(RTOL_ENV_VAR, "5e-3")))
    except ValueError:
        return 5.0e-3


def _prefixed(prefix: str, values: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}{key}": value for key, value in values.items()}


def _install_fixed_boundary_critical_fallback(critical: Any, equilibrium: Any, jtor: Any) -> None:
    """Patch FreeGS critical-point lookup for this process.

    FreeGS 0.8.2 can return small arrays from SciPy interpolator calls where the
    older code expects scalars. The fixed-boundary MVP only needs a robust core
    O-point estimate, so we use the largest interior psi value and no X-points.
    """

    critical.find_critical = _fixed_boundary_find_critical
    equilibrium.critical.find_critical = _fixed_boundary_find_critical
    jtor.critical.find_critical = _fixed_boundary_find_critical


def _fixed_boundary_find_critical(R: Any, Z: Any, psi: Any) -> tuple[list[tuple[float, float, float]], list]:
    psi_array = np.asarray(psi)
    if psi_array.ndim != 2 or psi_array.shape[0] < 3 or psi_array.shape[1] < 3:
        return [], []
    interior = psi_array[1:-1, 1:-1]
    if not np.any(np.isfinite(interior)):
        return [], []
    local_index = np.unravel_index(np.nanargmax(interior), interior.shape)
    i = int(local_index[0] + 1)
    j = int(local_index[1] + 1)
    return [(float(np.asarray(R)[i, j]), float(np.asarray(Z)[i, j]), float(psi_array[i, j]))], []


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if hasattr(value, "item"):
        return value.item()
    return value
