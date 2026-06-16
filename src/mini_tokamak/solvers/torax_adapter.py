"""TORAX transport adapter."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
from pprint import pformat
import shutil
import subprocess
import sys
from typing import Any

from mini_tokamak.design.dimensionless import beta_limit_percent, q_star
from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter
from mini_tokamak.units import MU0


EXECUTE_ENV_VAR = "MINI_TOKAMAK_TORAX_EXECUTE"
TIMEOUT_ENV_VAR = "MINI_TOKAMAK_TORAX_TIMEOUT_S"
T_FINAL_ENV_VAR = "MINI_TOKAMAK_TORAX_T_FINAL"
FIXED_DT_ENV_VAR = "MINI_TOKAMAK_TORAX_FIXED_DT"
N_RHO_ENV_VAR = "MINI_TOKAMAK_TORAX_N_RHO"
GREENWALD_FRACTION_ENV_VAR = "MINI_TOKAMAK_TORAX_GREENWALD_FRACTION"
PROFILE_MODEL_VERSION = "controlled_profile_source_v1"


class TORAXAdapter(SolverAdapter):
    name = "TORAX"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._message = "TORAX availability has not been probed."
        self._probe_metrics: dict[str, Any] = {}
        self._run_torax_exe: str | None = None
        self._run_root: Path | None = None

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        self._run_root = Path(output_dir)
        self._run_root.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        probe_code = (
            "import torax; "
            "print('TORAX_OK'); "
            "print('TORAX_PATH=' + str(torax.__file__)); "
            "print('TORAX_VERSION=' + str(getattr(torax, '__version__', 'unknown')))"
        )
        probe = subprocess.run(
            [sys.executable, "-c", probe_code],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        stdout = probe.stdout or ""
        self._available = probe.returncode == 0 and "TORAX_OK" in stdout
        self._run_torax_exe = shutil.which("run_torax")
        self._probe_metrics = {
            "probe_returncode": probe.returncode,
            "probe_stdout_tail": _tail(stdout),
            "probe_stderr_tail": _tail(probe.stderr or ""),
            "run_torax_executable": self._run_torax_exe,
        }
        if self._available:
            torax_path = _line_value(stdout, "TORAX_PATH=")
            torax_version = _line_value(stdout, "TORAX_VERSION=")
            if torax_path:
                self._probe_metrics["torax_path"] = torax_path
            if torax_version:
                self._probe_metrics["torax_version"] = torax_version
            self._message = "TORAX import works. Execution is opt-in."
        else:
            stderr = (probe.stderr or "").strip().splitlines()
            self._message = stderr[-1] if stderr else "TORAX import failed."
        return self._available

    def run(self, candidate: Candidate) -> SolverResult:
        return self._run(candidate, force_execute=False, top_candidate_rank=None)

    def run_transport_smoke(self, candidate: Candidate, rank: int) -> SolverResult:
        """Run the opt-in TORAX transport smoke for a ranked candidate.

        This is used by `--torax-top-n` so normal screening does not need
        `MINI_TOKAMAK_TORAX_EXECUTE=1`.
        """

        return self._run(candidate, force_execute=True, top_candidate_rank=rank)

    def _run(
        self,
        candidate: Candidate,
        *,
        force_execute: bool,
        top_candidate_rank: int | None,
    ) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, self._message)

        run_dir = self._candidate_run_dir(candidate)
        candidate_path = run_dir / "candidate.json"
        manifest_path = run_dir / "torax_manifest.json"
        config_path = run_dir / "torax_config.py"
        result_path = run_dir / "torax_result.json"
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"
        output_dir = run_dir / "torax_output"

        candidate_path.write_text(
            json.dumps(candidate.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        manifest = torax_manifest(candidate)
        manifest_path.write_text(json.dumps(_json_ready(manifest), indent=2), encoding="utf-8")
        config_path.write_text(_config_module(manifest), encoding="utf-8")

        execute_requested = force_execute or _execute_requested()
        metrics: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "candidate_path": str(candidate_path),
            "manifest_path": str(manifest_path),
            "config_path": str(config_path),
            "execution_requested": execute_requested,
            "execution_source": _execution_source(force_execute, execute_requested),
            "top_candidate_rank": top_candidate_rank,
            "geometry_status": "PASS" if not manifest["geometry_failures"] else "FAIL",
            "geometry_failures": manifest["geometry_failures"],
            "transport_model": manifest["config"]["transport"]["model_name"],
            "geometry_model": manifest["config"]["geometry"]["geometry_type"],
            "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
            "profile_model_version": manifest["profile_source_model"]["model_version"],
            "target_greenwald_fraction": manifest["profile_source_model"]["density"][
                "target_greenwald_fraction"
            ],
            "actual_greenwald_fraction": manifest["profile_source_model"]["density"][
                "actual_greenwald_fraction"
            ],
            "input_nbar_m3": manifest["profile_source_model"]["density"]["nbar_m3"],
            "input_T_i_core_keV": manifest["profile_source_model"]["temperature"][
                "T_i_core_keV"
            ],
            "input_T_e_core_keV": manifest["profile_source_model"]["temperature"][
                "T_e_core_keV"
            ],
            "input_aux_power_MW": manifest["profile_source_model"]["source"]["aux_power_MW"],
            "input_power_density_MW_m3": manifest["profile_source_model"]["source"][
                "power_density_MW_m3"
            ],
            "profile_guardrail_status": manifest["profile_source_model"]["guardrails"][
                "overall_status"
            ],
            "profile_guardrail_reasons": manifest["profile_source_model"]["guardrails"][
                "reasons"
            ],
            **self._probe_metrics,
        }

        if manifest["geometry_failures"]:
            result_metrics = {
                **metrics,
                "torax_status": "FAIL",
                "stage": "geometry_precheck",
                "output_file": None,
            }
            result_path.write_text(json.dumps(_json_ready(result_metrics), indent=2), encoding="utf-8")
            return SolverResult(
                solver=self.name,
                status="FAIL",
                available=True,
                metrics=result_metrics,
                raw_output_path=str(result_path),
                message="TORAX geometry precheck failed; no transport execution attempted.",
            )

        if not execute_requested:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=metrics,
                raw_output_path=str(config_path),
                message=(
                    "TORAX candidate config generated. Execution skipped by default to keep "
                    f"screening runs fast; set {EXECUTE_ENV_VAR}=1 to run a short CPU "
                    "transport smoke."
                ),
            )

        if self._run_torax_exe is None:
            result_metrics = {
                **metrics,
                "torax_status": "NOT_EVALUATED",
                "stage": "missing_run_torax_executable",
            }
            result_path.write_text(json.dumps(_json_ready(result_metrics), indent=2), encoding="utf-8")
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=result_metrics,
                raw_output_path=str(result_path),
                message="TORAX is importable, but `run_torax` is not on PATH.",
            )

        completed = self._execute_torax(
            config_path=config_path,
            output_dir=output_dir,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
        output_file = _latest_state_history(output_dir)
        metrics.update(
            {
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "output_dir": str(output_dir),
                "output_file": str(output_file) if output_file else None,
            }
        )
        if output_file is not None:
            output_summary = _summarize_output(output_file)
            metrics.update(output_summary)
            metrics.update(
                compare_transport_to_constraints(
                    candidate,
                    profile_model=manifest["profile_source_model"],
                    output_summary=output_summary,
                )
            )

        failed = completed.returncode != 0 or output_file is None
        metrics.update(
            {
                "torax_status": "FAIL" if failed else "PASS",
                "stage": "run_torax" if output_file else "no_output_file",
            }
        )
        result_path.write_text(json.dumps(_json_ready(metrics), indent=2), encoding="utf-8")

        return SolverResult(
            solver=self.name,
            status="FAIL" if failed else "WARNING",
            available=True,
            metrics=metrics,
            raw_output_path=str(stderr_path if failed and stderr_path.stat().st_size > 0 else result_path),
            message=(
                "TORAX execution failed or produced no state-history file; inspect artifacts."
                if failed
                else (
                    "TORAX short CPU transport run completed. Treat as transport plumbing "
                    "evidence, not validated pulse/profile physics."
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

    def _execute_torax(
        self,
        config_path: Path,
        output_dir: Path,
        stdout_path: Path,
        stderr_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        assert self._run_torax_exe is not None
        output_dir.mkdir(parents=True, exist_ok=True)
        command = [
            self._run_torax_exe,
            "--config",
            str(config_path),
            "--quit",
            "--output_dir",
            str(output_dir),
        ]
        env = os.environ.copy()
        env.setdefault("JAX_PLATFORMS", "cpu")
        env.setdefault("CUDA_VISIBLE_DEVICES", "")
        env.setdefault("MPLBACKEND", "Agg")
        try:
            completed = subprocess.run(
                command,
                cwd=config_path.parent,
                env=env,
                capture_output=True,
                text=True,
                timeout=_timeout_s(),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_safe_text(exc.stdout), encoding="utf-8")
            stderr_path.write_text(_safe_text(exc.stderr), encoding="utf-8")
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
        root = self._run_root or (Path.cwd() / "data" / "runs" / "torax_standalone")
        run_dir = root / candidate.candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir


def torax_manifest(candidate: Candidate) -> dict[str, Any]:
    geometry_failures = _geometry_failures(candidate)
    profile_model = torax_profile_source_model(candidate)
    config = {
        "profile_conditions": {
            "Ip": candidate.Ip * 1.0e6,
            "nbar": profile_model["density"]["nbar_m3"],
            "n_e_nbar_is_fGW": False,
            "T_i": profile_model["temperature"]["T_i_keV_profile"],
            "T_e": profile_model["temperature"]["T_e_keV_profile"],
            "n_e": profile_model["density"]["n_e_m3_profile"],
        },
        "plasma_composition": {},
        "numerics": {
            "t_initial": 0.0,
            "t_final": _t_final(),
            "fixed_dt": _fixed_dt(),
            "exact_t_final": True,
            "evolve_current": False,
            "evolve_density": False,
            "evolve_ion_heat": True,
            "evolve_electron_heat": True,
        },
        "geometry": {
            "geometry_type": "circular",
            "n_rho": _n_rho(),
            "R_major": candidate.R,
            "a_minor": candidate.a,
            "B_0": candidate.Bt,
            "elongation_LCFS": candidate.kappa,
        },
        "sources": {
            "generic_heat": {
                "P_total": profile_model["source"]["aux_power_W"],
            },
            "ohmic": {},
            "ei_exchange": {},
        },
        "pedestal": {},
        "transport": {
            "model_name": "constant",
        },
        "solver": {
            "solver_type": "linear",
        },
        "time_step_calculator": {
            "calculator_type": "fixed",
        },
    }
    return {
        "candidate_id": candidate.candidate_id,
        "candidate": candidate.model_dump(mode="json"),
        "config": config,
        "profile_source_model": profile_model,
        "profile_proxies": profile_model,
        "geometry_failures": geometry_failures,
        "note": (
            "Research-only TORAX circular-geometry transport smoke. Profiles are "
            "candidate-derived controlled placeholders for software integration, not "
            "validated plasma operating scenarios."
        ),
    }


def torax_profile_source_model(candidate: Candidate) -> dict[str, Any]:
    """Build deterministic low-fidelity TORAX profile and source inputs.

    This is a controlled initialization model for transport plumbing. It is not a recipe for
    a real discharge, and it intentionally carries guardrail metadata into the run artifacts.
    """

    greenwald_m3 = _greenwald_density_m3(candidate)
    requested_fraction = _greenwald_fraction()
    target_nbar = requested_fraction * greenwald_m3
    nbar = _clamp(target_nbar, 5.0e18, 8.0e19)
    actual_fraction = nbar / greenwald_m3 if greenwald_m3 > 0.0 else math.nan

    compactness = candidate.a / max(candidate.R, 1.0e-6)
    density_peaking = _clamp(1.12 + 0.30 * compactness, 1.12, 1.45)
    edge_density_fraction = _clamp(0.30 + 0.08 * candidate.kappa, 0.35, 0.55)
    core_density = nbar * density_peaking
    mid_density = nbar
    shoulder_density = nbar * max(edge_density_fraction, 0.60)
    edge_density = max(2.0e18, nbar * edge_density_fraction)

    plasma_volume = max(candidate.estimated_plasma_volume, 0.05)
    power_density = max(0.0, candidate.heating_power) / plasma_volume
    heating_temp_core = 0.85 + 1.15 * math.sqrt(max(power_density, 0.0))
    heating_temp_core *= _clamp((5.0 / max(candidate.Bt, 0.5)) ** 0.20, 0.65, 1.25)

    beta_cap_percent = _beta_cap_percent(candidate)
    beta_temp_cap = _temperature_cap_from_beta(candidate, nbar, beta_cap_percent)
    temp_core = _clamp(min(heating_temp_core, beta_temp_cap), 0.75, 18.0)
    temp_was_capped = heating_temp_core > beta_temp_cap
    temp_edge = _clamp(0.13 * temp_core, 0.15, 2.2)
    temp_shoulder = max(temp_edge * 1.8, temp_core * 0.42)

    source_power = max(0.0, candidate.heating_power)
    wetted_area = _wetted_area_proxy(candidate)
    heat_load_proxy = source_power / wetted_area
    pressure_proxy_pa = 2.0 * nbar * temp_core * 1.602176634e-16
    beta_proxy_percent = pressure_proxy_pa / _magnetic_pressure_pa(candidate) * 100.0

    guardrail_reasons: list[str] = []
    if target_nbar > nbar * 1.0001:
        guardrail_reasons.append("density_target_clipped_to_mvp_cap")
    elif target_nbar < nbar * 0.9999:
        guardrail_reasons.append("density_target_raised_to_mvp_floor")
    if actual_fraction > 0.85:
        guardrail_reasons.append("greenwald_fraction_above_0p85")
    elif actual_fraction > 0.65:
        guardrail_reasons.append("greenwald_fraction_above_0p65")
    if temp_was_capped:
        guardrail_reasons.append("temperature_limited_by_beta_cap")
    if beta_proxy_percent > beta_cap_percent:
        guardrail_reasons.append("beta_proxy_above_cap")
    if heat_load_proxy > 25.0:
        guardrail_reasons.append("input_heat_exhaust_proxy_fail")
    elif heat_load_proxy > 10.0:
        guardrail_reasons.append("input_heat_exhaust_proxy_warning")
    if power_density > 50.0:
        guardrail_reasons.append("input_power_density_outside_mvp_range")

    guardrail_status = _guardrail_status(guardrail_reasons)
    return {
        "model_version": PROFILE_MODEL_VERSION,
        "fidelity": "LOW_FIDELITY_PLACEHOLDER",
        "density": {
            "greenwald_density_proxy_m3": greenwald_m3,
            "target_greenwald_fraction": requested_fraction,
            "actual_greenwald_fraction": actual_fraction,
            "nbar_m3": nbar,
            "density_peaking": density_peaking,
            "edge_density_fraction": edge_density_fraction,
            "n_e_m3_profile": {
                0.0: core_density,
                0.45: core_density * 0.92,
                0.75: mid_density,
                0.90: shoulder_density,
                1.0: edge_density,
            },
        },
        "temperature": {
            "beta_cap_percent": beta_cap_percent,
            "beta_temperature_cap_keV": beta_temp_cap,
            "uncapped_heating_core_temperature_keV": heating_temp_core,
            "temperature_limited_by_beta_cap": temp_was_capped,
            "T_i_core_keV": temp_core,
            "T_e_core_keV": 0.92 * temp_core,
            "T_edge_keV": temp_edge,
            "T_i_keV_profile": {
                0.0: temp_core,
                0.45: temp_core * 0.86,
                0.75: temp_shoulder,
                0.90: max(temp_edge * 1.25, temp_core * 0.24),
                1.0: temp_edge,
            },
            "T_e_keV_profile": {
                0.0: 0.92 * temp_core,
                0.45: 0.80 * temp_core,
                0.75: max(temp_edge * 1.7, temp_core * 0.38),
                0.90: max(temp_edge * 1.18, temp_core * 0.22),
                1.0: temp_edge,
            },
        },
        "source": {
            "aux_power_MW": source_power,
            "aux_power_W": source_power * 1.0e6,
            "power_density_MW_m3": power_density,
            "wetted_area_proxy_m2": wetted_area,
            "input_heat_load_proxy_MW_m2": heat_load_proxy,
            "source_model": "uniform_generic_heat_with_ohmic_and_ei_exchange",
        },
        "pressure": {
            "input_pressure_proxy_Pa": pressure_proxy_pa,
            "input_beta_proxy_percent": beta_proxy_percent,
        },
        "guardrails": {
            "overall_status": guardrail_status,
            "reasons": guardrail_reasons,
        },
    }


def compare_transport_to_constraints(
    candidate: Candidate,
    profile_model: dict[str, Any],
    output_summary: dict[str, Any],
) -> dict[str, Any]:
    """Compare executed TORAX outputs with the MVP screening proxies."""

    checks: dict[str, str] = {}
    reasons: list[str] = []

    q95 = _float_or_none(output_summary.get("torax_final_q95"))
    q_proxy = q_star(candidate.R, candidate.a, candidate.Bt, candidate.Ip, candidate.kappa)
    if q95 is None:
        checks["torax_q95"] = "NOT_EVALUATED"
    elif q95 < 2.0:
        checks["torax_q95"] = "FAIL"
        reasons.append("torax_q95_below_2")
    elif q95 < 3.0:
        checks["torax_q95"] = "WARNING"
        reasons.append("torax_q95_below_3")
    else:
        checks["torax_q95"] = "PASS"

    fgw = _float_or_none(output_summary.get("torax_final_fgw_n_e_line_avg"))
    if fgw is None:
        checks["torax_greenwald_fraction"] = "NOT_EVALUATED"
    elif fgw > 1.0:
        checks["torax_greenwald_fraction"] = "FAIL"
        reasons.append("torax_greenwald_fraction_above_1")
    elif fgw > 0.8:
        checks["torax_greenwald_fraction"] = "WARNING"
        reasons.append("torax_greenwald_fraction_above_0p8")
    else:
        checks["torax_greenwald_fraction"] = "PASS"

    p_sol_mw = _float_or_none(output_summary.get("torax_final_P_SOL_total_MW"))
    wetted_area = _wetted_area_proxy(candidate)
    p_sol_heat_load = None if p_sol_mw is None else p_sol_mw / wetted_area
    if p_sol_heat_load is None:
        checks["torax_heat_exhaust_proxy"] = "NOT_EVALUATED"
    elif p_sol_heat_load > 25.0:
        checks["torax_heat_exhaust_proxy"] = "FAIL"
        reasons.append("torax_sol_heat_exhaust_proxy_fail")
    elif p_sol_heat_load > 10.0:
        checks["torax_heat_exhaust_proxy"] = "WARNING"
        reasons.append("torax_sol_heat_exhaust_proxy_warning")
    else:
        checks["torax_heat_exhaust_proxy"] = "PASS"

    beta_limit = beta_limit_percent(candidate.Ip, candidate.a, candidate.Bt)
    final_beta = _final_beta_proxy(candidate, output_summary)
    if final_beta is None:
        checks["torax_beta_proxy"] = "NOT_EVALUATED"
    elif beta_limit <= 0.0 or final_beta > 1.5 * beta_limit:
        checks["torax_beta_proxy"] = "FAIL"
        reasons.append("torax_beta_proxy_above_1p5_limit")
    elif final_beta > beta_limit:
        checks["torax_beta_proxy"] = "WARNING"
        reasons.append("torax_beta_proxy_above_limit")
    else:
        checks["torax_beta_proxy"] = "PASS"

    overall = _worst_status(checks.values())
    target_fraction = _nested_float(profile_model, "density", "actual_greenwald_fraction")
    comparison = {
        "torax_transport_comparison_fidelity": "LOW_FIDELITY_PLACEHOLDER",
        "torax_transport_constraint_status": overall,
        "torax_transport_constraint_reasons": reasons,
        "torax_transport_checks": checks,
        "torax_q_star_proxy": q_proxy,
        "torax_q95_minus_q_star": None if q95 is None else q95 - q_proxy,
        "torax_target_greenwald_fraction": target_fraction,
        "torax_final_greenwald_fraction_line_minus_target": (
            None if fgw is None or target_fraction is None else fgw - target_fraction
        ),
        "torax_wetted_area_proxy_m2": wetted_area,
        "torax_final_SOL_heat_load_MW_m2": p_sol_heat_load,
        "torax_final_beta_proxy_percent": final_beta,
        "torax_beta_limit_proxy_percent": beta_limit,
    }
    if reasons:
        comparison["torax_transport_dominant_failure_reason"] = reasons[0]
    return comparison


def _geometry_failures(candidate: Candidate) -> list[str]:
    failures: list[str] = []
    if candidate.R <= 0.0:
        failures.append("major_radius_nonpositive")
    if candidate.a <= 0.0:
        failures.append("minor_radius_nonpositive")
    if candidate.R < candidate.a:
        failures.append("circular_geometry_requires_R_major_ge_a_minor")
    if candidate.kappa <= 0.0:
        failures.append("elongation_nonpositive")
    return failures


def _greenwald_density_m3(candidate: Candidate) -> float:
    return max(1.0e16, candidate.Ip / (math.pi * max(candidate.a, 1.0e-6) ** 2) * 1.0e20)


def _greenwald_fraction() -> float:
    return _env_float(GREENWALD_FRACTION_ENV_VAR, default=0.25, lower=0.02, upper=0.85)


def _beta_cap_percent(candidate: Candidate) -> float:
    beta_limit = beta_limit_percent(candidate.Ip, candidate.a, candidate.Bt)
    if beta_limit <= 0.0 or not math.isfinite(beta_limit):
        return 1.0
    return _clamp(0.75 * beta_limit, 0.5, 6.0)


def _temperature_cap_from_beta(candidate: Candidate, nbar_m3: float, beta_cap_percent: float) -> float:
    pressure_cap = (beta_cap_percent / 100.0) * _magnetic_pressure_pa(candidate)
    return pressure_cap / max(2.0 * nbar_m3 * 1.602176634e-16, 1.0e-12)


def _magnetic_pressure_pa(candidate: Candidate) -> float:
    return max(candidate.Bt, 0.0) ** 2 / (2.0 * MU0)


def _wetted_area_proxy(candidate: Candidate) -> float:
    return max(0.15, 2.0 * math.pi * candidate.R * max(0.08, 0.25 * candidate.a))


def _guardrail_status(reasons: list[str]) -> str:
    if any(reason.endswith("_fail") or "_above_1" in reason for reason in reasons):
        return "FAIL"
    if reasons:
        return "WARNING"
    return "PASS"


def _worst_status(statuses: object) -> str:
    order = {"FAIL": 4, "WARNING": 3, "LOW_FIDELITY_PLACEHOLDER": 2, "NOT_EVALUATED": 1, "PASS": 0}
    worst = "PASS"
    for status in statuses:
        if order.get(str(status), -1) > order[worst]:
            worst = str(status)
    return worst


def _final_beta_proxy(candidate: Candidate, output_summary: dict[str, Any]) -> float | None:
    n_e = _float_or_none(output_summary.get("torax_final_n_e_volume_avg_m3"))
    t_e = _float_or_none(output_summary.get("torax_final_T_e_volume_avg_keV"))
    t_i = _float_or_none(output_summary.get("torax_final_T_i_volume_avg_keV"))
    if n_e is None or t_e is None or t_i is None:
        return None
    pressure_pa = n_e * (t_e + t_i) * 1.602176634e-16
    return pressure_pa / _magnetic_pressure_pa(candidate) * 100.0


def _nested_float(data: dict[str, Any], *keys: str) -> float | None:
    value: Any = data
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return _float_or_none(value)


def _float_or_none(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _env_float(name: str, default: float, lower: float, upper: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return _clamp(value, lower, upper)


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


def _config_module(manifest: dict[str, Any]) -> str:
    config_literal = pformat(manifest["config"], sort_dicts=False, width=100)
    return (
        '"""Generated TORAX config for MiniTokamak Designer.\n\n'
        "Research-only placeholder transport inputs; not a validated operating scenario.\n"
        '"""\n\n'
        f"CONFIG = {config_literal}\n"
    )


def _execute_requested() -> bool:
    return os.getenv(EXECUTE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "on"}


def _execution_source(force_execute: bool, execute_requested: bool) -> str:
    if force_execute:
        return "torax_top_n"
    if execute_requested:
        return EXECUTE_ENV_VAR
    return "default_skip"


def _timeout_s() -> int:
    try:
        return max(10, int(os.getenv(TIMEOUT_ENV_VAR, "180")))
    except ValueError:
        return 180


def _t_final() -> float:
    try:
        return max(0.01, float(os.getenv(T_FINAL_ENV_VAR, "0.2")))
    except ValueError:
        return 0.2


def _fixed_dt() -> float:
    try:
        return max(0.001, float(os.getenv(FIXED_DT_ENV_VAR, "0.05")))
    except ValueError:
        return 0.05


def _n_rho() -> int:
    try:
        return max(4, int(os.getenv(N_RHO_ENV_VAR, "12")))
    except ValueError:
        return 12


def _latest_state_history(output_dir: Path) -> Path | None:
    files = sorted(output_dir.glob("state_history_*.nc"))
    return files[-1] if files else None


def _summarize_output(output_file: Path) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "output_file_size_bytes": output_file.stat().st_size,
    }
    try:
        import xarray as xr

        data_tree = xr.open_datatree(output_file)
        summary["output_groups"] = sorted(data_tree.children.keys())
        if "time" in data_tree.dataset.coords:
            times = data_tree.dataset.coords["time"].values
            summary["time_steps"] = int(len(times))
            if len(times):
                summary["t_initial_s"] = float(times[0])
                summary["t_final_s"] = float(times[-1])
        for name, child in data_tree.children.items():
            if "time" in child.dataset.coords and "time_steps" not in summary:
                times = child.dataset.coords["time"].values
                summary["time_steps"] = int(len(times))
                if len(times):
                    summary["t_initial_s"] = float(times[0])
                    summary["t_final_s"] = float(times[-1])
            summary.setdefault("output_variables_sample", {})[name] = list(child.dataset.variables)[:12]
        summary.update(_extract_transport_output_metrics(data_tree))
        data_tree.close()
    except Exception as exc:
        summary["output_parse_error"] = f"{type(exc).__name__}: {exc}"
    return summary


def _extract_transport_output_metrics(data_tree: Any) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "torax_profile_output_available": False,
    }

    if "numerics" in data_tree.children:
        numerics = data_tree["numerics"].dataset
        metrics["torax_sim_status"] = _dataset_value(numerics, "sim_status")
        metrics["torax_sim_error"] = _dataset_value(numerics, "sim_error")

    if "profiles" in data_tree.children:
        profiles = data_tree["profiles"].dataset
        metrics["torax_profile_output_available"] = True
        for var, prefix in [
            ("T_e", "torax_final_T_e"),
            ("T_i", "torax_final_T_i"),
            ("n_e", "torax_final_n_e"),
            ("q", "torax_final_q"),
            ("pressure_total", "torax_final_pressure_total"),
        ]:
            metrics.update(_profile_metrics(profiles, var, prefix))

    if "scalars" in data_tree.children:
        scalars = data_tree["scalars"].dataset
        scalar_map = {
            "Ip": ("torax_final_Ip_MA", 1.0e-6),
            "tau_E": ("torax_final_tau_E_s", 1.0),
            "P_SOL_total": ("torax_final_P_SOL_total_MW", 1.0e-6),
            "P_aux_total": ("torax_final_P_aux_total_MW", 1.0e-6),
            "P_heat_total": ("torax_final_P_heat_total_MW", 1.0e-6),
            "P_external_total": ("torax_final_P_external_total_MW", 1.0e-6),
            "T_e_volume_avg": ("torax_final_T_e_volume_avg_keV", 1.0),
            "T_i_volume_avg": ("torax_final_T_i_volume_avg_keV", 1.0),
            "n_e_volume_avg": ("torax_final_n_e_volume_avg_m3", 1.0),
            "n_e_line_avg": ("torax_final_n_e_line_avg_m3", 1.0),
            "fgw_n_e_volume_avg": ("torax_final_fgw_n_e_volume_avg", 1.0),
            "fgw_n_e_line_avg": ("torax_final_fgw_n_e_line_avg", 1.0),
            "q95": ("torax_final_q95", 1.0),
            "q_min": ("torax_final_q_min", 1.0),
            "W_thermal_total": ("torax_final_W_thermal_total_MJ", 1.0e-6),
            "Q_fusion": ("torax_final_Q_fusion", 1.0),
        }
        for source, (target, scale) in scalar_map.items():
            value = _dataset_value(scalars, source)
            if isinstance(value, int | float):
                metrics[target] = float(value) * scale
            elif value is not None:
                metrics[target] = value

    return metrics


def _profile_metrics(dataset: Any, var_name: str, prefix: str) -> dict[str, Any]:
    if var_name not in dataset:
        return {}
    final = _final_array(dataset[var_name])
    numbers = [float(value) for value in final if math.isfinite(float(value))]
    if not numbers:
        return {}
    return {
        f"{prefix}_core": numbers[0],
        f"{prefix}_edge": numbers[-1],
        f"{prefix}_min": min(numbers),
        f"{prefix}_max": max(numbers),
    }


def _dataset_value(dataset: Any, var_name: str) -> Any:
    if var_name not in dataset:
        return None
    array = _final_array(dataset[var_name])
    if not array:
        return None
    value = array[0]
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    if isinstance(value, int | float | str | bool):
        return value
    return str(value)


def _final_array(data_array: Any) -> list[Any]:
    final = data_array
    if "time" in getattr(data_array, "dims", ()):
        final = data_array.isel(time=-1)
    values = getattr(final, "values", final)
    try:
        import numpy as np

        return list(np.asarray(values).ravel())
    except Exception:
        if isinstance(values, list | tuple):
            return list(values)
        return [values]


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
    return value
