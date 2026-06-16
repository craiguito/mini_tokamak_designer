from pathlib import Path
import subprocess

from mini_tokamak.schemas import Candidate
from mini_tokamak.solvers.fuse_adapter import EXECUTE_ENV_VAR, FUSEAdapter, parse_actor_sequence


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="fuse-test-candidate",
        machine_type="compact_tokamak",
        fuel_mode="DD_research",
        R=1.0,
        a=0.4,
        aspect_ratio=2.5,
        kappa=1.8,
        delta=0.25,
        Bt=5.5,
        Ip=2.5,
        heating_power=6.0,
        shield_thickness=0.18,
        first_wall_thickness=0.02,
        center_column_radius=0.2,
        estimated_volume=3.5,
        estimated_plasma_volume=1.5,
        notes="test candidate",
    )


def test_fuse_adapter_generates_probe_without_execution(tmp_path, monkeypatch):
    monkeypatch.delenv(EXECUTE_ENV_VAR, raising=False)

    adapter = FUSEAdapter()
    adapter._available = True
    adapter._julia_exe = "julia"
    adapter._message = "FUSE import works. MVP execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "fuse")

    result = adapter.run(_candidate())

    assert result.status == "NOT_EVALUATED"
    assert result.available is True
    assert result.raw_output_path is not None
    script = Path(result.raw_output_path)
    candidate_json = Path(result.metrics["candidate_path"])
    assert script.exists()
    assert candidate_json.exists()
    assert "using FUSE" in script.read_text(encoding="utf-8")
    assert "fuse-test-candidate" in candidate_json.read_text(encoding="utf-8")


def test_fuse_adapter_parses_result_json(tmp_path):
    result_path = tmp_path / "fuse_result.json"
    result_path.write_text(
        '{"julia_status":"PASS","dd_type":"IMASdd.dd{Float64}"}',
        encoding="utf-8",
    )

    metrics = FUSEAdapter().parse_results(result_path)

    assert metrics["julia_status"] == "PASS"
    assert metrics["dd_type"] == "IMASdd.dd{Float64}"


def test_fuse_adapter_actor_sequence_result(tmp_path, monkeypatch):
    adapter = FUSEAdapter()
    adapter._available = True
    adapter._julia_exe = "julia"
    adapter._message = "FUSE import works. MVP execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "fuse")

    def fake_execute(script_path, candidate_path, result_path, stdout_path, stderr_path, extra_env=None):
        result_path.write_text(
            """
{
  "julia_status": "PASS",
  "dd_type": "IMASdd.dd{Float64}",
  "actor_results": [{"actor": "ActorPFdesign", "status": "PASS", "elapsed_s": 0.1}]
}
""".strip(),
            encoding="utf-8",
        )
        stdout_path.write_text("{}", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        assert extra_env is not None
        assert extra_env["MINI_TOKAMAK_FUSE_ACTORS"] == "ActorPFdesign"
        return subprocess.CompletedProcess(args=["julia"], returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(adapter, "_execute", fake_execute)

    result = adapter.run_actor_sequence(_candidate(), rank=1, actors=["ActorPFdesign"])

    assert result.solver == "FUSE.jl actors"
    assert result.status == "WARNING"
    assert result.metrics["julia_status"] == "PASS"
    assert result.metrics["actor_results"][0]["actor"] == "ActorPFdesign"


def test_parse_actor_sequence():
    assert parse_actor_sequence("ActorPFdesign, ActorCXbuild,, ") == [
        "ActorPFdesign",
        "ActorCXbuild",
    ]
