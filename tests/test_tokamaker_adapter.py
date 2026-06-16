from pathlib import Path
import subprocess

from mini_tokamak.schemas import Candidate
from mini_tokamak.solvers.tokamaker_adapter import (
    EXECUTE_ENV_VAR,
    MODE_ENV_VAR,
    TokaMakerAdapter,
    tokamaker_manifest,
)


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="tokamaker-test-candidate",
        machine_type="compact_tokamak",
        fuel_mode="DD_research",
        R=1.0,
        a=0.3,
        aspect_ratio=3.0,
        kappa=1.7,
        delta=0.2,
        Bt=4.5,
        Ip=1.2,
        heating_power=4.0,
        shield_thickness=0.2,
        first_wall_thickness=0.02,
        center_column_radius=0.18,
        estimated_volume=3.0,
        estimated_plasma_volume=1.2,
        notes="test candidate",
    )


def test_tokamaker_manifest_builds_proxy_regions(monkeypatch):
    monkeypatch.delenv(MODE_ENV_VAR, raising=False)

    manifest = tokamaker_manifest(_candidate())

    assert manifest["geometry_failures"] == []
    assert manifest["candidate_id"] == "tokamaker-test-candidate"
    assert manifest["boundary_model"] == "Miller-like target plasma boundary"
    assert len(manifest["coil_regions"]) == 2
    assert manifest["coil_regions"][0]["coil_set"] == "PF_UPPER"
    assert manifest["mesh_settings"]["rextent_m"] > _candidate().R


def test_tokamaker_adapter_generates_runner_without_execution(tmp_path, monkeypatch):
    monkeypatch.delenv(EXECUTE_ENV_VAR, raising=False)

    adapter = TokaMakerAdapter()
    adapter._available = True
    adapter._message = "OpenFUSIONToolkit/TokaMaker import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "tokamaker")

    result = adapter.run(_candidate())

    assert result.status == "NOT_EVALUATED"
    assert result.available is True
    assert result.raw_output_path is not None
    input_path = Path(result.raw_output_path)
    runner_path = Path(result.metrics["runner_path"])
    assert input_path.exists()
    assert runner_path.exists()
    assert "import h5py" in runner_path.read_text(encoding="utf-8")
    assert "tokamaker-test-candidate" in input_path.read_text(encoding="utf-8")


def test_tokamaker_adapter_records_vacuum_execution_success(tmp_path, monkeypatch):
    monkeypatch.setenv(EXECUTE_ENV_VAR, "1")
    monkeypatch.delenv(MODE_ENV_VAR, raising=False)
    adapter = TokaMakerAdapter()
    adapter._available = True
    adapter._message = "OpenFUSIONToolkit/TokaMaker import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "tokamaker")

    def fake_execute_runner(
        runner_path,
        input_path,
        result_path,
        stdout_path,
        stderr_path,
        mesh_path,
        plot_path,
        mode,
    ):
        result_path.write_text(
            """
{
  "tokamaker_status": "PASS",
  "stage": "vacuum_solve",
  "vacuum_status": "PASS",
  "mesh_points": 10,
  "mesh_cells": 12
}
""".strip(),
            encoding="utf-8",
        )
        stdout_path.write_text("runner stdout", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        mesh_path.write_bytes(b"mesh")
        plot_path.write_bytes(b"png")
        assert mode == "vacuum"
        return subprocess.CompletedProcess(args=["python"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(adapter, "_execute_runner", fake_execute_runner)

    result = adapter.run(_candidate())

    assert result.status == "WARNING"
    assert result.metrics["tokamaker_status"] == "PASS"
    assert result.metrics["stage"] == "vacuum_solve"
    assert Path(result.metrics["mesh_path"]).exists()
    assert Path(result.metrics["plot_path"]).exists()


def test_tokamaker_adapter_records_free_boundary_failure(tmp_path, monkeypatch):
    monkeypatch.setenv(EXECUTE_ENV_VAR, "1")
    monkeypatch.setenv(MODE_ENV_VAR, "free_boundary")
    adapter = TokaMakerAdapter()
    adapter._available = True
    adapter._message = "OpenFUSIONToolkit/TokaMaker import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "tokamaker")

    def fake_execute_runner(
        runner_path,
        input_path,
        result_path,
        stdout_path,
        stderr_path,
        mesh_path,
        plot_path,
        mode,
    ):
        result_path.write_text(
            """
{
  "tokamaker_status": "FAIL",
  "stage": "free_boundary_solve",
  "vacuum_status": "PASS",
  "free_boundary_status": "FAIL",
  "error": "Matrix solve failed for targets"
}
""".strip(),
            encoding="utf-8",
        )
        stdout_path.write_text("runner stdout", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        mesh_path.write_bytes(b"mesh")
        plot_path.write_bytes(b"png")
        assert mode == "free_boundary"
        return subprocess.CompletedProcess(args=["python"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(adapter, "_execute_runner", fake_execute_runner)

    result = adapter.run(_candidate())

    assert result.status == "FAIL"
    assert result.metrics["vacuum_status"] == "PASS"
    assert result.metrics["free_boundary_status"] == "FAIL"
