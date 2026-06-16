"""FUSE.jl adapter."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter


EXECUTE_ENV_VAR = "MINI_TOKAMAK_FUSE_EXECUTE"
TIMEOUT_ENV_VAR = "MINI_TOKAMAK_FUSE_TIMEOUT_S"
CASE_ENV_VAR = "MINI_TOKAMAK_FUSE_CASE"
ACTORS_ENV_VAR = "MINI_TOKAMAK_FUSE_ACTORS"
DEFAULT_ACTOR_SEQUENCE = ("ActorPFdesign",)


class FUSEAdapter(SolverAdapter):
    name = "FUSE.jl"

    def __init__(self) -> None:
        self._available: bool | None = None
        self._message = "FUSE availability has not been probed."
        self._julia_exe: str | None = None
        self._run_root: Path | None = None
        self._probe_metrics: dict[str, Any] = {}

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        self._run_root = Path(output_dir)
        self._run_root.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        julia = self._find_julia()
        if julia is None:
            self._message = "Julia is not installed or not on PATH."
            self._available = False
            return False
        self._julia_exe = julia

        probe_code = (
            'using FUSE; using JSON; '
            'println("FUSE_OK"); '
            'println("FUSE_PKGDIR=" * pkgdir(FUSE))'
        )
        probe = subprocess.run(
            [julia, "-e", probe_code],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        stdout = probe.stdout or ""
        self._available = probe.returncode == 0 and "FUSE_OK" in stdout
        if self._available:
            pkgdir = _line_value(stdout, "FUSE_PKGDIR=")
            self._probe_metrics = {"fuse_package_path": pkgdir} if pkgdir else {}
            self._message = "FUSE import works. MVP execution is opt-in."
        else:
            stderr = (probe.stderr or "").strip().splitlines()
            self._message = stderr[-1] if stderr else "Julia exists, but `using FUSE` failed."
            self._probe_metrics = {
                "probe_returncode": probe.returncode,
                "probe_stdout_tail": _tail(stdout),
                "probe_stderr_tail": _tail(probe.stderr or ""),
            }
        return self._available

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, self._message)

        run_dir = self._candidate_run_dir(candidate)
        candidate_path = run_dir / "candidate.json"
        script_path = run_dir / "fuse_candidate_probe.jl"
        result_path = run_dir / "fuse_result.json"
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"

        candidate_path.write_text(
            json.dumps(candidate.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        script_path.write_text(_julia_probe_script(), encoding="utf-8")

        execute_requested = self._execute_requested()
        metrics: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "candidate_path": str(candidate_path),
            "script_path": str(script_path),
            "execution_requested": execute_requested,
            "fuse_case": self._case_name(),
            "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
            **self._probe_metrics,
        }

        if not execute_requested:
            return SolverResult(
                solver=self.name,
                status="NOT_EVALUATED",
                available=True,
                metrics=metrics,
                raw_output_path=str(script_path),
                message=(
                    "FUSE candidate probe generated. Execution skipped by default to keep "
                    f"screening runs fast; set {EXECUTE_ENV_VAR}=1 to run FUSE.init."
                ),
            )

        completed = self._execute(script_path, candidate_path, result_path, stdout_path, stderr_path)
        metrics.update(
            {
                "returncode": completed.returncode,
                "stdout_path": str(stdout_path),
                "stderr_path": str(stderr_path),
                "result_path": str(result_path) if result_path.exists() else None,
            }
        )

        if result_path.exists() and result_path.stat().st_size > 0:
            parsed = self.parse_results(result_path)
            metrics.update(parsed)

        failure_hint = _failure_hint(completed.stderr)
        if failure_hint:
            metrics["failure_hint"] = failure_hint

        julia_status = str(metrics.get("julia_status", "UNKNOWN"))
        failed = completed.returncode != 0 or julia_status == "FAIL"
        raw_output_path = str(stderr_path if failed and stderr_path.stat().st_size > 0 else result_path)
        return SolverResult(
            solver=self.name,
            status="FAIL" if failed else "WARNING",
            available=True,
            metrics=metrics,
            raw_output_path=raw_output_path,
            message=(
                "FUSE execution failed; inspect stderr and generated Julia probe."
                if failed
                else (
                    "FUSE.init completed with the MVP candidate mapping. Treat this as "
                    "initial FUSE plumbing, not a design viability claim."
                )
            ),
        )

    def run_actor_sequence(
        self,
        candidate: Candidate,
        rank: int,
        actors: list[str] | None = None,
    ) -> SolverResult:
        if not self.is_available():
            return SolverResult(
                solver=f"{self.name} actors",
                status="LOW_FIDELITY_PLACEHOLDER",
                available=False,
                metrics={"candidate_id": candidate.candidate_id, "top_rank": rank},
                message=self._message,
            )

        actor_sequence = actors or self._actor_sequence()
        run_dir = self._candidate_run_dir(candidate)
        candidate_path = run_dir / "candidate.json"
        script_path = run_dir / "fuse_actor_sequence.jl"
        result_path = run_dir / "fuse_actor_sequence.json"
        stdout_path = run_dir / "actor_stdout.txt"
        stderr_path = run_dir / "actor_stderr.txt"

        candidate_path.write_text(
            json.dumps(candidate.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )
        script_path.write_text(_julia_actor_sequence_script(), encoding="utf-8")

        metrics: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "top_rank": rank,
            "candidate_path": str(candidate_path),
            "script_path": str(script_path),
            "fuse_case": self._case_name(),
            "actor_sequence_requested": actor_sequence,
            "mvp_mapping_fidelity": "LOW_FIDELITY_PLACEHOLDER",
            **self._probe_metrics,
        }

        completed = self._execute(
            script_path,
            candidate_path,
            result_path,
            stdout_path,
            stderr_path,
            extra_env={ACTORS_ENV_VAR: ",".join(actor_sequence)},
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

        failure_hint = _failure_hint(completed.stderr)
        if failure_hint:
            metrics["failure_hint"] = failure_hint

        julia_status = str(metrics.get("julia_status", "UNKNOWN"))
        failed = completed.returncode != 0 or julia_status == "FAIL"
        raw_output_path = str(stderr_path if failed and stderr_path.stat().st_size > 0 else result_path)
        return SolverResult(
            solver=f"{self.name} actors",
            status="FAIL" if failed else "WARNING",
            available=True,
            metrics=metrics,
            raw_output_path=raw_output_path,
            message=(
                "FUSE actor sequence failed; inspect per-actor results and stderr."
                if failed
                else (
                    "FUSE actor sequence completed for a top-ranked candidate. Treat this "
                    "as controlled integration evidence, not a design viability claim."
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

    def _execute(
        self,
        script_path: Path,
        candidate_path: Path,
        result_path: Path,
        stdout_path: Path,
        stderr_path: Path,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        assert self._julia_exe is not None
        env = os.environ.copy()
        env.setdefault("JULIA_PKG_PRECOMPILE_AUTO", "0")
        env.setdefault(CASE_ENV_VAR, self._case_name())
        if extra_env:
            env.update(extra_env)
        try:
            completed = subprocess.run(
                [self._julia_exe, str(script_path), str(candidate_path), str(result_path)],
                cwd=script_path.parent,
                capture_output=True,
                text=True,
                timeout=self._timeout_s(),
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_path.write_text(_safe_text(exc.stdout), encoding="utf-8")
            stderr_path.write_text(_safe_text(exc.stderr), encoding="utf-8")
            result_path.write_text(
                json.dumps(
                    {
                        "julia_status": "FAIL",
                        "error_type": "TimeoutExpired",
                        "error": f"FUSE execution timed out after {self._timeout_s()} seconds.",
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(
                args=[self._julia_exe, str(script_path)],
                returncode=124,
                stdout=_safe_text(exc.stdout),
                stderr=_safe_text(exc.stderr),
            )

        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        return completed

    def _find_julia(self) -> str | None:
        found = shutil.which("julia")
        if found:
            return found
        juliaup = Path.home() / ".juliaup" / "bin" / "julia"
        return str(juliaup) if juliaup.exists() else None

    def _candidate_run_dir(self, candidate: Candidate) -> Path:
        root = self._run_root or (Path.cwd() / "data" / "runs" / "fuse_standalone")
        run_dir = root / candidate.candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _execute_requested(self) -> bool:
        return os.environ.get(EXECUTE_ENV_VAR, "").strip().lower() in {"1", "true", "yes", "run"}

    def _timeout_s(self) -> int:
        raw = os.environ.get(TIMEOUT_ENV_VAR, "600")
        try:
            return max(1, int(raw))
        except ValueError:
            return 240

    def _case_name(self) -> str:
        return os.environ.get(CASE_ENV_VAR, "FPP").strip() or "FPP"

    def _actor_sequence(self) -> list[str]:
        raw = os.environ.get(ACTORS_ENV_VAR, "")
        return parse_actor_sequence(raw) or list(DEFAULT_ACTOR_SEQUENCE)


def parse_actor_sequence(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _julia_probe_script() -> str:
    return r'''
using FUSE
using JSON

candidate_path = ARGS[1]
result_path = ARGS[2]
candidate = JSON.parsefile(candidate_path)
case_name = get(ENV, "MINI_TOKAMAK_FUSE_CASE", "FPP")

metrics = Dict{String, Any}(
    "julia_status" => "NOT_EVALUATED",
    "candidate_id" => candidate["candidate_id"],
    "fuse_case" => case_name,
    "fuse_package_path" => pkgdir(FUSE),
    "mvp_mapping_fidelity" => "LOW_FIDELITY_PLACEHOLDER",
)

function set_if_present!(mapped::Dict{String, Any}, obj, field::Symbol, value, label::String)
    if field in propertynames(obj)
        try
            setproperty!(obj, field, value)
            mapped[label] = value
        catch err
            mapped[label * "_error"] = sprint(showerror, err)
        end
    else
        mapped[label * "_missing"] = true
    end
end

try
    ini, act = FUSE.case_parameters(Symbol(case_name))
    mapped = Dict{String, Any}()

    set_if_present!(mapped, ini.equilibrium, :R0, candidate["R"], "ini.equilibrium.R0")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03f5"), candidate["a"] / candidate["R"], "ini.equilibrium.epsilon")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03ba"), candidate["kappa"], "ini.equilibrium.kappa")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03b4"), candidate["delta"], "ini.equilibrium.delta")

    dd = FUSE.init(ini, act)
    metrics["julia_status"] = "PASS"
    metrics["dd_type"] = string(typeof(dd))
    metrics["mapped_fields"] = mapped
catch err
    metrics["julia_status"] = "FAIL"
    metrics["error_type"] = string(typeof(err))
    metrics["error"] = sprint(showerror, err)
    metrics["stacktrace"] = sprint(show, catch_backtrace())
end

open(result_path, "w") do io
    JSON.print(io, metrics, 2)
end

println(JSON.json(metrics))
exit(metrics["julia_status"] == "PASS" ? 0 : 1)
'''.lstrip()


def _julia_actor_sequence_script() -> str:
    return r'''
using FUSE
using JSON

candidate_path = ARGS[1]
result_path = ARGS[2]
candidate = JSON.parsefile(candidate_path)
case_name = get(ENV, "MINI_TOKAMAK_FUSE_CASE", "FPP")
actor_sequence = filter(!isempty, strip.(split(get(ENV, "MINI_TOKAMAK_FUSE_ACTORS", "ActorPFdesign"), ",")))

metrics = Dict{String, Any}(
    "julia_status" => "NOT_EVALUATED",
    "candidate_id" => candidate["candidate_id"],
    "fuse_case" => case_name,
    "actor_sequence" => collect(actor_sequence),
    "fuse_package_path" => pkgdir(FUSE),
    "mvp_mapping_fidelity" => "LOW_FIDELITY_PLACEHOLDER",
)

function set_if_present!(mapped::Dict{String, Any}, obj, field::Symbol, value, label::String)
    if field in propertynames(obj)
        try
            setproperty!(obj, field, value)
            mapped[label] = value
        catch err
            mapped[label * "_error"] = sprint(showerror, err)
        end
    else
        mapped[label * "_missing"] = true
    end
end

function actor_call(name::AbstractString, dd, act)
    actor = getproperty(FUSE, Symbol(name))
    actor(dd, act)
    return nothing
end

actor_results = Vector{Dict{String, Any}}()

try
    ini, act = FUSE.case_parameters(Symbol(case_name))
    mapped = Dict{String, Any}()

    set_if_present!(mapped, ini.equilibrium, :R0, candidate["R"], "ini.equilibrium.R0")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03f5"), candidate["a"] / candidate["R"], "ini.equilibrium.epsilon")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03ba"), candidate["kappa"], "ini.equilibrium.kappa")
    set_if_present!(mapped, ini.equilibrium, Symbol("\u03b4"), candidate["delta"], "ini.equilibrium.delta")

    dd = FUSE.init(ini, act)
    metrics["init_status"] = "PASS"
    metrics["dd_type"] = string(typeof(dd))
    metrics["mapped_fields"] = mapped

    for actor_name in actor_sequence
        result = Dict{String, Any}(
            "actor" => actor_name,
            "status" => "NOT_EVALUATED",
        )
        t0 = time()
        try
            actor_call(actor_name, dd, act)
            result["status"] = "PASS"
        catch err
            result["status"] = "FAIL"
            result["error_type"] = string(typeof(err))
            result["error"] = sprint(showerror, err)
            result["stacktrace"] = sprint(show, catch_backtrace())
        end
        result["elapsed_s"] = time() - t0
        push!(actor_results, result)
        if result["status"] == "FAIL"
            metrics["dominant_failure_actor"] = actor_name
            break
        end
    end

    metrics["actor_results"] = actor_results
    metrics["julia_status"] = any(r["status"] == "FAIL" for r in actor_results) ? "FAIL" : "PASS"
catch err
    metrics["julia_status"] = "FAIL"
    metrics["error_type"] = string(typeof(err))
    metrics["error"] = sprint(showerror, err)
    metrics["stacktrace"] = sprint(show, catch_backtrace())
    metrics["actor_results"] = actor_results
end

open(result_path, "w") do io
    JSON.print(io, metrics, 2)
end

println(JSON.json(metrics))
exit(metrics["julia_status"] == "PASS" ? 0 : 1)
'''.lstrip()


def _line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    return None


def _tail(text: str, limit: int = 5) -> str:
    return "\n".join(text.strip().splitlines()[-limit:])


def _failure_hint(stderr: str) -> str | None:
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return lines[-1] if lines else None


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)
