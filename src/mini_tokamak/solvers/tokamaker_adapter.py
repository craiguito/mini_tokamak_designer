"""OpenFUSIONToolkit/TokaMaker adapter."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter


EXECUTE_ENV_VAR = "MINI_TOKAMAK_TOKAMAKER_EXECUTE"
MODE_ENV_VAR = "MINI_TOKAMAK_TOKAMAKER_MODE"
TIMEOUT_ENV_VAR = "MINI_TOKAMAK_TOKAMAKER_TIMEOUT_S"
MAXITS_ENV_VAR = "MINI_TOKAMAK_TOKAMAKER_MAXITS"
MESH_SCALE_ENV_VAR = "MINI_TOKAMAK_TOKAMAKER_MESH_SCALE"

VALID_MODES = {"vacuum", "free_boundary"}


class TokaMakerAdapter(SolverAdapter):
    name = "TokaMaker"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._message = "TokaMaker availability has not been probed."
        self._probe_metrics: dict[str, Any] = {}
        self._run_root: Path | None = None

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        self._run_root = Path(output_dir)
        self._run_root.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        probe_code = (
            "import h5py; "
            "import OpenFUSIONToolkit; "
            "from OpenFUSIONToolkit.TokaMaker import TokaMaker; "
            "print('TOKAMAKER_OK'); "
            "print('OFT_PATH=' + str(OpenFUSIONToolkit.__file__)); "
            "print('H5PY_VERSION=' + str(h5py.__version__))"
        )
        probe = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        stdout = probe.stdout or ""
        self._available = probe.returncode == 0 and "TOKAMAKER_OK" in stdout
        self._probe_metrics = {
            "probe_returncode": probe.returncode,
            "probe_stdout_tail": _tail(stdout),
            "probe_stderr_tail": _tail(probe.stderr or ""),
            "import_order_workaround": "import h5py before OpenFUSIONToolkit",
        }
        if self._available:
            oft_path = _line_value(stdout, "OFT_PATH=")
            h5py_version = _line_value(stdout, "H5PY_VERSION=")
            if oft_path:
                self._probe_metrics["openfusiontoolkit_path"] = oft_path
            if h5py_version:
                self._probe_metrics["h5py_version"] = h5py_version
            self._message = "OpenFUSIONToolkit/TokaMaker import works. Execution is opt-in."
        else:
            stderr = (probe.stderr or "").strip().splitlines()
            self._message = stderr[-1] if stderr else "OpenFUSIONToolkit/TokaMaker import failed."
        return self._available

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, self._message)

        run_dir = self._candidate_run_dir(candidate)
        candidate_path = run_dir / "candidate.json"
        input_path = run_dir / "tokamaker_input.json"
        runner_path = run_dir / "tokamaker_runner.py"
        result_path = run_dir / "tokamaker_result.json"
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"
        mesh_path = run_dir / "tokamaker_mesh.npz"
        plot_path = run_dir / "tokamaker_mesh.png"

        candidate_path.write_text(
            json.dumps(candidate.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        manifest = tokamaker_manifest(candidate)
        input_path.write_text(json.dumps(_json_ready(manifest), indent=2), encoding="utf-8")
        runner_path.write_text(_runner_script(), encoding="utf-8")

        execute_requested = _execute_requested()
        mode = _mode()
        metrics: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "candidate_path": str(candidate_path),
            "input_path": str(input_path),
            "runner_path": str(runner_path),
            "execution_requested": execute_requested,
            "tokamaker_mode": mode,
            "geometry_status": "PASS" if not manifest["geometry_failures"] else "FAIL",
            "geometry_failures": manifest["geometry_failures"],
            "mesh_model": "Miller-like plasma boundary with two PF proxy coil rectangles",
            "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
            **self._probe_metrics,
        }

        if manifest["geometry_failures"]:
            result_metrics = {
                **metrics,
                "tokamaker_status": "FAIL",
                "stage": "geometry_precheck",
                "mesh_path": None,
                "plot_path": None,
            }
            result_path.write_text(json.dumps(_json_ready(result_metrics), indent=2), encoding="utf-8")
            return SolverResult(
                solver=self.name,
                status="FAIL",
                available=True,
                metrics=result_metrics,
                raw_output_path=str(result_path),
                message="TokaMaker geometry precheck failed; no solver execution attempted.",
            )

        if not execute_requested:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=metrics,
                raw_output_path=str(input_path),
                message=(
                    "TokaMaker input manifest and runner generated. Execution skipped by "
                    f"default to keep screening runs fast; set {EXECUTE_ENV_VAR}=1 to run "
                    "the vacuum-solve preflight."
                ),
            )

        completed = self._execute_runner(
            runner_path=runner_path,
            input_path=input_path,
            result_path=result_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            mesh_path=mesh_path,
            plot_path=plot_path,
            mode=mode,
        )
        metrics.update(
            {
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "result_path": str(result_path) if result_path.exists() else None,
            }
        )
        if result_path.exists() and result_path.stat().st_size > 0:
            metrics.update(self.parse_results(result_path))
        if mesh_path.exists():
            metrics["mesh_path"] = str(mesh_path)
        else:
            metrics["mesh_path"] = None
        if plot_path.exists():
            metrics["plot_path"] = str(plot_path)
        else:
            metrics["plot_path"] = None

        failed = completed.returncode != 0 or metrics.get("tokamaker_status") == "FAIL"
        raw_output_path = str(stderr_path if failed and stderr_path.stat().st_size > 0 else result_path)
        return SolverResult(
            solver=self.name,
            status="FAIL" if failed else "WARNING",
            available=True,
            metrics=metrics,
            raw_output_path=raw_output_path,
            message=(
                "TokaMaker execution failed or free-boundary solve did not converge; inspect artifacts."
                if failed
                else (
                    "TokaMaker vacuum-solve preflight completed. Treat as OpenFUSIONToolkit "
                    "integration evidence, not free-boundary viability."
                )
            ),
        )

    def parse_results(self, raw: object) -> dict[str, object]:
        path = Path(raw)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"parse_error": str(exc)}
        return data if isinstance(data, dict) else {"raw": data}

    def _execute_runner(
        self,
        runner_path: Path,
        input_path: Path,
        result_path: Path,
        stdout_path: Path,
        stderr_path: Path,
        mesh_path: Path,
        plot_path: Path,
        mode: str,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env[MODE_ENV_VAR] = mode
        env.setdefault("MPLBACKEND", "Agg")
        command = [
            sys.executable,
            str(runner_path),
            str(input_path),
            str(result_path),
            str(mesh_path),
            str(plot_path),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=runner_path.parent,
                env=env,
                capture_output=True,
                text=True,
                timeout=_timeout_s(),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_safe_text(exc.stdout), encoding="utf-8")
            stderr_path.write_text(_safe_text(exc.stderr), encoding="utf-8")
            timeout_result = {
                "tokamaker_status": "FAIL",
                "stage": "timeout",
                "timeout_s": _timeout_s(),
                "error": f"TokaMaker runner timed out after {_timeout_s()} seconds.",
            }
            result_path.write_text(json.dumps(timeout_result, indent=2), encoding="utf-8")
            return subprocess.CompletedProcess(
                args=command,
                returncode=124,
                stdout=_safe_text(exc.stdout),
                stderr=_safe_text(exc.stderr),
            )

        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        return completed

    def _candidate_run_dir(self, candidate: Candidate) -> Path:
        root = self._run_root or (Path.cwd() / "data" / "runs" / "tokamaker_standalone")
        run_dir = root / candidate.candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


def tokamaker_manifest(candidate: Candidate) -> dict[str, Any]:
    boundary = miller_boundary_points(candidate)
    geometry = boundary_geometry_metrics(candidate, boundary)
    coils = rough_pf_coil_regions(candidate, boundary)
    mesh = mesh_settings(candidate, boundary, coils)
    targets = {
        "F0_RBt": max(1.0e-6, candidate.R * candidate.Bt),
        "Ip_A": candidate.Ip * 1.0e6,
        "p_axis_proxy_Pa": pressure_axis_proxy(candidate),
        "R0_m": candidate.R,
        "Z0_m": 0.0,
        "maxits": _maxits(),
    }
    geometry_failures = geometry_failures_for(candidate, geometry, coils)
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(mode="json"),
        "boundary_model": "Miller-like target plasma boundary",
        "boundary": {
            "R": boundary["R"].tolist(),
            "Z": boundary["Z"].tolist(),
        },
        "geometry_metrics": geometry,
        "coil_regions": coils,
        "mesh_settings": mesh,
        "targets": targets,
        "geometry_failures": geometry_failures,
        "solver_mode_requested": _mode(),
        "note": (
            "Research-only TokaMaker proxy inputs. Coil rectangles are numerical regions "
            "for equilibrium preflight, not construction coil geometry."
        ),
    }


def miller_boundary_points(candidate: Candidate, n: int = 81) -> dict[str, np.ndarray]:
    theta = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    r = candidate.R + candidate.a * np.cos(theta + candidate.delta * np.sin(theta))
    z = candidate.kappa * candidate.a * np.sin(theta)
    return {"theta": theta, "R": r, "Z": z}


def boundary_geometry_metrics(
    candidate: Candidate,
    boundary: dict[str, np.ndarray],
) -> dict[str, float | bool]:
    r = boundary["R"]
    z = boundary["Z"]
    inboard_gap = candidate.R - candidate.a - candidate.center_column_radius
    return {
        "target_min_R_m": float(np.min(r)),
        "target_max_R_m": float(np.max(r)),
        "target_min_Z_m": float(np.min(z)),
        "target_max_Z_m": float(np.max(z)),
        "target_width_m": float(np.max(r) - np.min(r)),
        "target_height_m": float(np.max(z) - np.min(z)),
        "target_inboard_gap_m": inboard_gap,
        "target_min_R_positive": bool(np.min(r) > 0.0),
        "center_column_clearance_ok": bool(inboard_gap > 0.0),
        "elongation_target": candidate.kappa,
        "triangularity_target": candidate.delta,
    }


def rough_pf_coil_regions(candidate: Candidate, boundary: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    r_boundary_max = float(np.max(boundary["R"]))
    z_abs_max = float(np.max(np.abs(boundary["Z"])))
    radial_clearance = max(0.10, 0.25 * candidate.a)
    vertical_clearance = max(0.10, 0.25 * candidate.a)
    width = max(0.08, 0.20 * candidate.a)
    height = max(0.08, 0.20 * candidate.a)
    coil_r = r_boundary_max + radial_clearance
    coil_z = z_abs_max + vertical_clearance
    current_proxy = max(1.0e3, candidate.Ip * 1.0e6 * 0.05)
    return [
        {
            "name": "PF_UPPER_PROXY",
            "coil_set": "PF_UPPER",
            "R": coil_r,
            "Z": coil_z,
            "width_m": width,
            "height_m": height,
            "nturns": 1,
            "current_A": current_proxy,
        },
        {
            "name": "PF_LOWER_PROXY",
            "coil_set": "PF_LOWER",
            "R": coil_r,
            "Z": -coil_z,
            "width_m": width,
            "height_m": height,
            "nturns": 1,
            "current_A": current_proxy,
        },
    ]


def mesh_settings(
    candidate: Candidate,
    boundary: dict[str, np.ndarray],
    coils: list[dict[str, Any]],
) -> dict[str, float]:
    scale = _mesh_scale()
    rmax = max(
        float(np.max(boundary["R"])) + max(0.30, 0.75 * candidate.a),
        max(coil["R"] + 0.20 for coil in coils),
    )
    z_abs = max(
        float(np.max(np.abs(boundary["Z"]))) + max(0.30, 0.75 * candidate.a),
        max(abs(coil["Z"]) + 0.20 for coil in coils),
    )
    base = max(0.05, min(0.16, candidate.a / 4.0)) * scale
    return {
        "rextent_m": rmax,
        "zmin_m": -z_abs,
        "zmax_m": z_abs,
        "plasma_dx_m": base,
        "vacuum_dx_m": base * 1.5,
        "coil_dx_m": base * 1.25,
        "mesh_scale": scale,
    }


def geometry_failures_for(
    candidate: Candidate,
    geometry: dict[str, Any],
    coils: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    if not geometry["target_min_R_positive"]:
        failures.append("target_boundary_crosses_axis")
    if not geometry["center_column_clearance_ok"]:
        failures.append("plasma_intersects_center_column_proxy")
    machine_radius = candidate.machine_width / 2.0
    outermost_coil = max(coil["R"] + 0.5 * coil["width_m"] for coil in coils)
    if outermost_coil > machine_radius + 1.0e-9:
        failures.append("rough_pf_coils_exceed_machine_radius_proxy")
    return failures


def pressure_axis_proxy(candidate: Candidate) -> float:
    mu0 = 4.0e-7 * math.pi
    magnetic_pressure = candidate.Bt**2 / (2.0 * mu0)
    beta_proxy = min(0.12, max(0.005, 0.02 + 0.004 * candidate.heating_power))
    return magnetic_pressure * beta_proxy


def _execute_requested() -> bool:
    return os.getenv(EXECUTE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def _mode() -> str:
    mode = os.getenv(MODE_ENV_VAR, "vacuum").strip().lower()
    return mode if mode in VALID_MODES else "vacuum"


def _timeout_s() -> int:
    try:
        return max(5, int(os.getenv(TIMEOUT_ENV_VAR, "180")))
    except ValueError:
        return 180


def _maxits() -> int:
    try:
        return max(1, int(os.getenv(MAXITS_ENV_VAR, "20")))
    except ValueError:
        return 20


def _mesh_scale() -> float:
    try:
        return max(0.5, min(4.0, float(os.getenv(MESH_SCALE_ENV_VAR, "1.0"))))
    except ValueError:
        return 1.0


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _tail(text: str, max_lines: int = 20) -> str:
    lines = text.strip().splitlines()
    return "\n".join(lines[-max_lines:])


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _runner_script() -> str:
    return r'''"""Generated TokaMaker runner for MiniTokamak Designer."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import sys
import traceback

import h5py  # Import before OpenFUSIONToolkit to avoid HDF5 library-order issues.
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from OpenFUSIONToolkit import OFT_env
from OpenFUSIONToolkit.TokaMaker import TokaMaker
from OpenFUSIONToolkit.TokaMaker.meshing import gs_Domain


def main() -> int:
    input_path = Path(sys.argv[1])
    result_path = Path(sys.argv[2])
    mesh_path = Path(sys.argv[3])
    plot_path = Path(sys.argv[4])
    mode = os.getenv("MINI_TOKAMAK_TOKAMAKER_MODE", "vacuum").strip().lower()
    if mode not in {"vacuum", "free_boundary"}:
        mode = "vacuum"

    manifest = json.loads(input_path.read_text(encoding="utf-8"))
    result = {
        "tokamaker_status": "FAIL",
        "stage": "startup",
        "mode": mode,
        "h5py_version": h5py.__version__,
    }

    try:
        boundary = np.column_stack(
            [
                np.asarray(manifest["boundary"]["R"], dtype=float),
                np.asarray(manifest["boundary"]["Z"], dtype=float),
            ]
        )
        mesh_settings = manifest["mesh_settings"]
        targets = manifest["targets"]

        domain = gs_Domain(
            rextent=float(mesh_settings["rextent_m"]),
            zextents=[float(mesh_settings["zmin_m"]), float(mesh_settings["zmax_m"])],
        )
        domain.define_region("plasma", float(mesh_settings["plasma_dx_m"]), "plasma")
        domain.define_region("vacuum", float(mesh_settings["vacuum_dx_m"]), "boundary")
        for coil in manifest["coil_regions"]:
            domain.define_region(
                coil["name"],
                float(mesh_settings["coil_dx_m"]),
                "coil",
                nTurns=float(coil.get("nturns", 1)),
                coil_set=coil["coil_set"],
            )
        domain.add_polygon(boundary, "plasma", "vacuum")
        for coil in manifest["coil_regions"]:
            domain.add_rectangle(
                float(coil["R"]),
                float(coil["Z"]),
                float(coil["width_m"]),
                float(coil["height_m"]),
                coil["name"],
                "vacuum",
            )

        r, lc, reg = domain.build_mesh()
        np.savez_compressed(mesh_path, r=r, lc=lc, reg=reg)
        _plot_mesh(plot_path, r, lc, reg, boundary, manifest["coil_regions"])

        result.update(
            {
                "stage": "mesh_built",
                "mesh_points": int(r.shape[0]),
                "mesh_cells": int(lc.shape[0]),
                "mesh_regions": sorted(int(item) for item in set(reg.tolist())),
                "mesh_path": str(mesh_path),
                "plot_path": str(plot_path),
            }
        )

        env = OFT_env(nthreads=1, unique_tempfiles="local_dir", quiet=True)
        tm = TokaMaker(env)
        tm.setup_mesh(r=r, lc=lc, reg=reg)
        tm.setup_regions(domain.get_conductors(), domain.get_coils())
        tm.setup(order=1, F0=float(targets["F0_RBt"]))
        tm.settings.pm = False
        tm.settings.maxits = int(targets.get("maxits", 20))
        tm.settings.nl_tol = 1.0e-5
        tm.update_settings()

        currents = {
            coil["coil_set"]: float(coil["current_A"])
            for coil in manifest["coil_regions"]
        }
        tm.set_coil_currents(currents)
        tm.vac_solve()
        result.update(
            {
                "tokamaker_status": "PASS",
                "stage": "vacuum_solve",
                "vacuum_status": "PASS",
                "coil_set_names": list(tm.coil_set_names),
                "coil_currents_A": currents,
                "ncoils": int(tm.ncoils),
                "np": int(tm.np),
                "nc": int(tm.nc),
            }
        )

        if mode == "free_boundary":
            try:
                tm.set_profiles(ffp_prof={"type": "flat"}, pp_prof={"type": "flat"})
                tm.set_targets(
                    Ip=float(targets["Ip_A"]),
                    pax=float(targets["p_axis_proxy_Pa"]),
                    R0=float(targets["R0_m"]),
                    Z0=float(targets["Z0_m"]),
                )
                _, iterations = tm.solve(return_its=True)
                result.update(
                    {
                        "stage": "free_boundary_solve",
                        "free_boundary_status": "PASS",
                        "nonlinear_iterations": int(iterations),
                    }
                )
            except Exception as exc:
                result.update(
                    {
                        "tokamaker_status": "FAIL",
                        "stage": "free_boundary_solve",
                        "free_boundary_status": "FAIL",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )

        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0
    except Exception as exc:
        result.update(
            {
                "tokamaker_status": "FAIL",
                "stage": result.get("stage", "unknown"),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 2


def _plot_mesh(plot_path, r, lc, reg, boundary, coils):
    fig, ax = plt.subplots(figsize=(7, 6))
    color_mesh = ax.tripcolor(
        r[:, 0],
        r[:, 1],
        lc,
        facecolors=reg,
        cmap="tab10",
        edgecolors="0.75",
        linewidth=0.25,
        alpha=0.65,
    )
    ax.plot(boundary[:, 0], boundary[:, 1], color="black", linewidth=1.5)
    for coil in coils:
        x0 = float(coil["R"]) - 0.5 * float(coil["width_m"])
        z0 = float(coil["Z"]) - 0.5 * float(coil["height_m"])
        rect = plt.Rectangle(
            (x0, z0),
            float(coil["width_m"]),
            float(coil["height_m"]),
            fill=False,
            edgecolor="tab:red",
            linewidth=1.3,
        )
        ax.add_patch(rect)
        ax.text(float(coil["R"]), float(coil["Z"]), coil["coil_set"], fontsize=7, ha="center")
    ax.set_xlabel("R [m]")
    ax.set_ylabel("Z [m]")
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("TokaMaker proxy mesh")
    fig.colorbar(color_mesh, ax=ax, shrink=0.8, label="region id")
    fig.tight_layout()
    fig.savefig(plot_path, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
'''
