"""PROCESS systems-code adapter.

The MVP adapter writes auditable PROCESS input decks by default. Actual PROCESS
execution is opt-in because a single PROCESS evaluation can take tens of seconds,
which would make a 100-candidate random search unexpectedly slow.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter, executable_available, module_available


EXECUTE_ENV_VAR = "MINI_TOKAMAK_PROCESS_EXECUTE"
TEMPLATE_ENV_VAR = "MINI_TOKAMAK_PROCESS_TEMPLATE"
TIMEOUT_ENV_VAR = "MINI_TOKAMAK_PROCESS_TIMEOUT_S"

DEFAULT_TEMPLATE_CANDIDATES = (
    Path("/home/craig/src/PROCESS/examples/data/large_tokamak_eval_IN.DAT"),
    Path("/opt/PROCESS/examples/data/large_tokamak_eval_IN.DAT"),
)

PROCESS_PARSE_KEYS = (
    "ifail",
    "rmajor",
    "rminor",
    "aspect",
    "kappa",
    "triang",
    "b_plasma_toroidal_on_axis",
    "b_tf_inboard_peak_with_ripple",
    "plasma_current_MA",
    "q95",
    "beta_total_vol_avg",
    "beta_poloidal_vol_avg",
    "hfact",
    "nd_plasma_electrons_vol_avg",
    "temp_plasma_electron_vol_avg_kev",
    "p_fusion_total_mw",
    "p_plant_electric_net_mw",
    "p_plasma_separatrix_mw",
    "pflux_fw_neutron_mw",
    "sig_tf_case",
    "sig_tf_wp",
    "tmarg",
)


class PROCESSAdapter(SolverAdapter):
    name = "PROCESS"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._run_root: Path | None = None

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        self._run_root = Path(output_dir)
        self._run_root.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        if self._available is None:
            self._available = executable_available(["process"]) or module_available(["process"])
        return self._available

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(
                candidate,
                "PROCESS is not installed or not on PATH. Adapter returned a placeholder only.",
            )

        template_path = self._find_template()
        if template_path is None:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics={
                    "candidate_id": candidate.candidate_id,
                    "template_required": True,
                    "template_env_var": TEMPLATE_ENV_VAR,
                },
                message=(
                    "PROCESS is available, but no input template was found. Set "
                    f"{TEMPLATE_ENV_VAR} to a validated PROCESS IN.DAT template."
                ),
            )

        run_dir = self._candidate_run_dir(candidate)
        input_path = run_dir / "IN.DAT"
        overrides = self._candidate_overrides(candidate)
        self._write_process_input(template_path, input_path, candidate, overrides)

        execute_requested = self._execute_requested()
        metrics: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "input_path": str(input_path),
            "template_path": str(template_path),
            "execution_requested": execute_requested,
            "candidate_ip_ma_requested": candidate.Ip,
            "candidate_minor_radius_m_requested": candidate.a,
            "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
        }

        if not execute_requested:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=metrics,
                raw_output_path=str(input_path),
                message=(
                    "PROCESS input deck generated. Execution skipped by default to keep "
                    f"screening runs fast; set {EXECUTE_ENV_VAR}=1 to run PROCESS."
                ),
            )

        process_exe = shutil.which("process")
        if process_exe is None:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=metrics | {"process_executable_required": True},
                raw_output_path=str(input_path),
                message=(
                    "PROCESS Python module is importable, but the `process` executable "
                    "is not on PATH, so execution was not attempted."
                ),
            )

        return self._execute_process(candidate, run_dir, input_path, process_exe, metrics)

    def parse_results(self, raw: object) -> dict[str, object]:
        path = Path(raw)
        metrics: dict[str, object] = {}
        try:
            from process.core.io.mfile import MFile  # type: ignore[import-not-found]

            mfile = MFile(filename=str(path))
            for key in PROCESS_PARSE_KEYS:
                if key in mfile.data:
                    metrics[key] = _to_json_scalar(mfile.data[key].get_scan(-1))
        except Exception as exc:  # pragma: no cover - parser availability varies by PROCESS version.
            metrics["mfile_parser_error"] = str(exc)
        for key, value in _parse_mfile_text(path).items():
            metrics.setdefault(key, value)
        return metrics

    def _execute_process(
        self,
        candidate: Candidate,
        run_dir: Path,
        input_path: Path,
        process_exe: str,
        metrics: dict[str, Any],
    ) -> SolverResult:
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"
        mfile_path = run_dir / "MFILE.DAT"
        timeout_s = self._timeout_s()

        try:
            completed = subprocess.run(
                [process_exe, "-i", input_path.name, "-m", mfile_path.name],
                cwd=run_dir,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_safe_text(exc.stdout), encoding="utf-8")
            stderr_path.write_text(_safe_text(exc.stderr), encoding="utf-8")
            return SolverResult(
                solver=self.name,
                status="FAIL",
                available=True,
                metrics=metrics
                | {
                    "timeout_s": timeout_s,
                    "stdout_path": str(stdout_path),
                    "stderr_path": str(stderr_path),
                },
                raw_output_path=str(input_path),
                message=f"PROCESS execution timed out after {timeout_s} seconds.",
            )

        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        metrics.update(
            {
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "mfile_path": str(mfile_path) if mfile_path.exists() else None,
            }
        )
        failure_hint = _failure_hint(completed.stderr)
        if failure_hint:
            metrics["failure_hint"] = failure_hint

        mfile_has_content = mfile_path.exists() and mfile_path.stat().st_size > 0
        if mfile_has_content:
            metrics.update(self.parse_results(mfile_path))

        ifail = _optional_int(metrics.get("ifail"))
        failed = completed.returncode != 0 or (ifail is not None and ifail != 1)
        status = "FAIL" if failed else "WARNING"
        message = (
            "PROCESS execution failed or did not converge; inspect MFILE/stdout/stderr."
            if failed
            else (
                "PROCESS executed with the MVP template mapping. Treat this as a "
                "systems-code probe, not a design viability claim."
            )
        )
        if failed and stderr_path.stat().st_size > 0:
            raw_output_path = str(stderr_path)
        else:
            raw_output_path = str(mfile_path if mfile_has_content else stdout_path)
        return SolverResult(
            solver=self.name,
            status=status,
            available=True,
            metrics=metrics,
            message=message,
            raw_output_path=raw_output_path,
        )

    def _find_template(self) -> Path | None:
        env_template = os.environ.get(TEMPLATE_ENV_VAR)
        if env_template:
            path = Path(env_template).expanduser()
            if path.exists():
                return path
        for path in DEFAULT_TEMPLATE_CANDIDATES:
            if path.exists():
                return path
        return None

    def _candidate_run_dir(self, candidate: Candidate) -> Path:
        root = self._run_root or (Path.cwd() / "data" / "runs" / "process_standalone")
        run_dir = root / candidate.candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _candidate_overrides(self, candidate: Candidate) -> dict[str, float | str]:
        shield = max(candidate.shield_thickness, 0.0)
        if candidate.fuel_mode == "DT_later_flag_only":
            blanket = max(0.05, min(shield, 1.2))
        else:
            blanket = 0.0
        center_column = max(candidate.center_column_radius, 0.01)

        return {
            "runtitle": f"MiniTokamak {candidate.candidate_id[:8]}",
            "rmajor": candidate.R,
            "aspect": candidate.aspect_ratio,
            "kappa": candidate.kappa,
            "triang": candidate.delta,
            "b_plasma_toroidal_on_axis": candidate.Bt,
            "dr_shld_inboard": shield,
            "dr_shld_outboard": shield,
            "dr_blkt_inboard": blanket,
            "dr_blkt_outboard": blanket,
            "dr_tf_inboard": center_column,
            "dr_bore": max(0.01, center_column * 0.20),
            "dr_cs": max(0.01, center_column * 0.50),
            "p_hcd_primary_extra_heat_mw": candidate.heating_power,
            "p_hcd_injected_max": max(candidate.heating_power, 0.1),
            "p_plant_electric_net_required_mw": 1.0,
        }

    def _write_process_input(
        self,
        template_path: Path,
        output_path: Path,
        candidate: Candidate,
        overrides: dict[str, float | str],
    ) -> None:
        template_lines = template_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines = _header_lines(candidate, template_path)
        remaining = template_lines[:]
        for key, value in overrides.items():
            remaining = _replace_or_append_assignment(remaining, key, value)
        lines.extend(remaining)
        output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _execute_requested(self) -> bool:
        return os.environ.get(EXECUTE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "run"}

    def _timeout_s(self) -> int:
        raw = os.environ.get(TIMEOUT_ENV_VAR, "180")
        try:
            return max(1, int(raw))
        except ValueError:
            return 180


def _header_lines(candidate: Candidate, template_path: Path) -> list[str]:
    return [
        "* Generated by MiniTokamak Designer PROCESSAdapter.",
        "* Simulation-only feasibility research input; not construction or operating guidance.",
        "* Low-fidelity MVP mapping from compact candidate schema to a generic PROCESS template.",
        f"* template_path = {template_path}",
        f"* candidate_id = {candidate.candidate_id}",
        f"* machine_type = {candidate.machine_type}",
        f"* fuel_mode = {candidate.fuel_mode}",
        f"* requested_minor_radius_a_m = {candidate.a:.10g}",
        f"* requested_plasma_current_Ip_MA = {candidate.Ip:.10g}",
        "* note = Ip is recorded here but not directly mapped; template uses PROCESS current scaling.",
        "* ---- original PROCESS template with MiniTokamak overrides follows ----",
    ]


def _replace_or_append_assignment(
    lines: list[str],
    key: str,
    value: float | str,
) -> list[str]:
    pattern = re.compile(rf"^(?P<prefix>\s*{re.escape(key)}\s*=\s*)(?P<body>.*)$", re.IGNORECASE)
    formatted = _format_process_value(value)
    replaced = False
    output: list[str] = []
    for line in lines:
        match = pattern.match(line)
        if not match:
            output.append(line)
            continue
        comment = ""
        body = match.group("body")
        if "*" in body:
            comment = " *" + body.split("*", 1)[1].rstrip()
        output.append(f"{match.group('prefix')}{formatted}{comment}")
        replaced = True
    if not replaced:
        output.append(f"{key:<32} = {formatted} * inserted by MiniTokamak Designer")
    return output


def _format_process_value(value: float | str) -> str:
    if isinstance(value, str):
        return value.replace("\n", " ").replace("*", "").strip()
    return f"{value:.10g}"


def _to_json_scalar(value: object) -> object:
    if hasattr(value, "item"):
        return value.item()  # type: ignore[no-any-return]
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (list, tuple)) and len(value) == 1:
        return _to_json_scalar(value[0])
    return value


def _parse_mfile_text(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    pattern = re.compile(
        r"^\s*(?P<key>[A-Za-z][A-Za-z0-9_]*)\s*(?:=|\()\s*"
        r"(?P<value>[-+]?\d+(?:\.\d*)?(?:[EeDd][-+]?\d+)?)"
    )
    metrics: dict[str, object] = {}
    wanted = set(PROCESS_PARSE_KEYS)
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line)
        if not match:
            continue
        key = match.group("key")
        if key not in wanted:
            continue
        raw = match.group("value").replace("D", "E").replace("d", "e")
        try:
            value: object = float(raw)
        except ValueError:
            value = raw
        metrics[key] = value
    return metrics


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _failure_hint(stderr: str) -> str | None:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("process.") or "ProcessValueError" in line:
            return line
    return lines[-1] if lines else None
