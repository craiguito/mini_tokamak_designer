from pathlib import Path
import subprocess

from mini_tokamak.schemas import Candidate
from mini_tokamak.solvers.torax_adapter import (
    EXECUTE_ENV_VAR,
    GREENWALD_FRACTION_ENV_VAR,
    TORAXAdapter,
    compare_transport_to_constraints,
    torax_manifest,
    torax_profile_source_model,
)


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="torax-test-candidate",
        machine_type="compact_tokamak",
        fuel_mode="DD_research",
        R=1.1,
        a=0.35,
        aspect_ratio=3.14,
        kappa=1.8,
        delta=0.2,
        Bt=5.0,
        Ip=1.5,
        heating_power=5.0,
        shield_thickness=0.2,
        first_wall_thickness=0.02,
        center_column_radius=0.18,
        estimated_volume=3.3,
        estimated_plasma_volume=1.4,
        notes="test candidate",
    )


def test_torax_manifest_maps_candidate_to_circular_config(monkeypatch):
    monkeypatch.delenv("MINI_TOKAMAK_TORAX_T_FINAL", raising=False)
    manifest = torax_manifest(_candidate())
    profile = manifest["profile_source_model"]

    assert manifest["geometry_failures"] == []
    assert manifest["candidate_id"] == "torax-test-candidate"
    assert manifest["config"]["geometry"]["geometry_type"] == "circular"
    assert manifest["config"]["geometry"]["R_major"] == 1.1
    assert manifest["config"]["geometry"]["a_minor"] == 0.35
    assert manifest["config"]["profile_conditions"]["Ip"] == 1.5e6
    assert manifest["config"]["profile_conditions"]["nbar"] == profile["density"]["nbar_m3"]
    assert manifest["config"]["sources"]["generic_heat"]["P_total"] == 5.0e6
    assert profile["model_version"] == "controlled_profile_source_v1"
    assert profile["density"]["nbar_m3"] > 0
    assert profile["temperature"]["T_i_core_keV"] >= profile["temperature"]["T_edge_keV"]


def test_torax_profile_model_honors_greenwald_fraction_env(monkeypatch):
    monkeypatch.setenv(GREENWALD_FRACTION_ENV_VAR, "0.40")
    model = torax_profile_source_model(_candidate())

    assert model["density"]["target_greenwald_fraction"] == 0.40
    assert 0.0 < model["density"]["actual_greenwald_fraction"] <= 0.85
    assert model["source"]["aux_power_MW"] == 5.0
    assert model["guardrails"]["overall_status"] in {"PASS", "WARNING", "FAIL"}


def test_torax_transport_comparison_flags_output_constraints():
    candidate = _candidate()
    profile = torax_profile_source_model(candidate)
    comparison = compare_transport_to_constraints(
        candidate,
        profile_model=profile,
        output_summary={
            "torax_final_q95": 1.7,
            "torax_final_fgw_n_e_line_avg": 0.9,
            "torax_final_P_SOL_total_MW": 30.0,
            "torax_final_n_e_volume_avg_m3": 5.0e19,
            "torax_final_T_e_volume_avg_keV": 3.0,
            "torax_final_T_i_volume_avg_keV": 3.0,
        },
    )

    assert comparison["torax_transport_constraint_status"] == "FAIL"
    assert "torax_q95_below_2" in comparison["torax_transport_constraint_reasons"]
    assert comparison["torax_final_SOL_heat_load_MW_m2"] > 25.0


def test_torax_adapter_generates_config_without_execution(tmp_path, monkeypatch):
    monkeypatch.delenv(EXECUTE_ENV_VAR, raising=False)
    adapter = TORAXAdapter()
    adapter._available = True
    adapter._run_torax_exe = "run_torax"
    adapter._message = "TORAX import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "torax")

    result = adapter.run(_candidate())

    assert result.status == "NOT_EVALUATED"
    assert result.available is True
    assert result.raw_output_path is not None
    config_path = Path(result.raw_output_path)
    manifest_path = Path(result.metrics["manifest_path"])
    assert config_path.exists()
    assert manifest_path.exists()
    assert "CONFIG =" in config_path.read_text(encoding="utf-8")
    assert "torax-test-candidate" in manifest_path.read_text(encoding="utf-8")


def test_torax_adapter_handles_missing_run_torax_executable(tmp_path, monkeypatch):
    monkeypatch.setenv(EXECUTE_ENV_VAR, "1")
    adapter = TORAXAdapter()
    adapter._available = True
    adapter._run_torax_exe = None
    adapter._message = "TORAX import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "torax")

    result = adapter.run(_candidate())

    assert result.status == "NOT_EVALUATED"
    assert result.metrics["stage"] == "missing_run_torax_executable"


def test_torax_adapter_records_execution_success(tmp_path, monkeypatch):
    monkeypatch.setenv(EXECUTE_ENV_VAR, "1")
    adapter = TORAXAdapter()
    adapter._available = True
    adapter._run_torax_exe = "run_torax"
    adapter._message = "TORAX import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "torax")

    def fake_execute_torax(config_path, output_dir, stdout_path, stderr_path):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "state_history_20260616_000000.nc").write_bytes(b"netcdf")
        stdout_path.write_text("stdout", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(args=["run_torax"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(adapter, "_execute_torax", fake_execute_torax)

    result = adapter.run(_candidate())

    assert result.status == "WARNING"
    assert result.metrics["torax_status"] == "PASS"
    assert result.metrics["stage"] == "run_torax"
    assert result.metrics["output_file"].endswith(".nc")
    assert result.metrics["torax_transport_constraint_status"] == "NOT_EVALUATED"


def test_torax_adapter_transport_smoke_forces_execution(tmp_path, monkeypatch):
    monkeypatch.delenv(EXECUTE_ENV_VAR, raising=False)
    adapter = TORAXAdapter()
    adapter._available = True
    adapter._run_torax_exe = "run_torax"
    adapter._message = "TORAX import works. Execution is opt-in."
    adapter.prepare_run("test-run", tmp_path / "torax")

    def fake_execute_torax(config_path, output_dir, stdout_path, stderr_path):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "state_history_20260616_000001.nc").write_bytes(b"netcdf")
        stdout_path.write_text("stdout", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        return subprocess.CompletedProcess(args=["run_torax"], returncode=0, stdout="", stderr="")

    monkeypatch.setattr(adapter, "_execute_torax", fake_execute_torax)

    result = adapter.run_transport_smoke(_candidate(), rank=2)

    assert result.status == "WARNING"
    assert result.metrics["execution_requested"] is True
    assert result.metrics["execution_source"] == "torax_top_n"
    assert result.metrics["top_candidate_rank"] == 2
    assert result.metrics["stage"] == "run_torax"
