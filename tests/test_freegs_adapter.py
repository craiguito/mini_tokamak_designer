from pathlib import Path

from mini_tokamak.schemas import Candidate
from mini_tokamak.solvers.freegs_adapter import (
    FreeGSAdapter,
    boundary_geometry_metrics,
    miller_boundary_points,
    rough_pf_coil_layout,
)


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="freegs-test-candidate",
        machine_type="spherical_tokamak",
        fuel_mode="DD_research",
        R=0.9,
        a=0.3,
        aspect_ratio=3.0,
        kappa=1.8,
        delta=0.25,
        Bt=5.0,
        Ip=1.5,
        heating_power=5.0,
        shield_thickness=0.08,
        first_wall_thickness=0.015,
        center_column_radius=0.15,
        estimated_volume=2.2,
        estimated_plasma_volume=1.0,
    )


def test_miller_boundary_geometry_is_positive():
    candidate = _candidate()
    boundary = miller_boundary_points(candidate, n=41)
    metrics = boundary_geometry_metrics(candidate, boundary)
    coils = rough_pf_coil_layout(candidate, boundary)

    assert len(boundary["R"]) == 41
    assert metrics["target_min_R_positive"] is True
    assert metrics["center_column_clearance_ok"] is True
    assert coils["coil_centers"][0]["Z"] > 0
    assert coils["coil_centers"][1]["Z"] < 0


def test_freegs_adapter_records_successful_sanity_result(tmp_path, monkeypatch):
    adapter = FreeGSAdapter()
    adapter._available = True
    adapter.prepare_run("test-run", tmp_path / "freegs")

    def fake_sanity(candidate, boundary_path, field_path, plot_path):
        boundary_path.write_text("{}", encoding="utf-8")
        field_path.write_bytes(b"npz")
        plot_path.write_bytes(b"png")
        return {
            "freegs_status": "PASS",
            "stage": "fixed_boundary_picard",
            "psi_range": 1.0,
        }

    monkeypatch.setattr(adapter, "_run_fixed_boundary_sanity", fake_sanity)

    result = adapter.run(_candidate())

    assert result.status == "WARNING"
    assert result.available is True
    assert result.raw_output_path is not None
    assert Path(result.raw_output_path).exists()
    assert result.metrics["freegs_status"] == "PASS"


def test_freegs_adapter_records_failed_sanity_result(tmp_path, monkeypatch):
    adapter = FreeGSAdapter()
    adapter._available = True
    adapter.prepare_run("test-run", tmp_path / "freegs")

    def fake_sanity(candidate, boundary_path, field_path, plot_path):
        raise ValueError("bad boundary")

    monkeypatch.setattr(adapter, "_run_fixed_boundary_sanity", fake_sanity)

    result = adapter.run(_candidate())

    assert result.status == "FAIL"
    assert result.metrics["error_type"] == "ValueError"


def test_freegs_adapter_does_not_report_missing_artifacts(tmp_path, monkeypatch):
    adapter = FreeGSAdapter()
    adapter._available = True
    adapter.prepare_run("test-run", tmp_path / "freegs")

    def fake_sanity(candidate, boundary_path, field_path, plot_path):
        boundary_path.write_text("{}", encoding="utf-8")
        return {
            "freegs_status": "FAIL",
            "stage": "geometry_precheck",
            "geometry_failures": ["rough_pf_coils_exceed_machine_radius_proxy"],
        }

    monkeypatch.setattr(adapter, "_run_fixed_boundary_sanity", fake_sanity)

    result = adapter.run(_candidate())

    assert result.status == "FAIL"
    assert result.metrics["boundary_path"] is not None
    assert result.metrics["field_path"] is None
    assert result.metrics["plot_path"] is None
