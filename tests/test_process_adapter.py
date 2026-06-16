from pathlib import Path

from mini_tokamak.schemas import Candidate
from mini_tokamak.solvers.process_adapter import (
    EXECUTE_ENV_VAR,
    PROCESSAdapter,
    TEMPLATE_ENV_VAR,
)


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="process-test-candidate",
        machine_type="spherical_tokamak",
        fuel_mode="DD_research",
        R=0.8,
        a=0.38,
        aspect_ratio=2.1,
        kappa=1.9,
        delta=0.35,
        Bt=6.5,
        Ip=3.2,
        heating_power=8.0,
        shield_thickness=0.12,
        first_wall_thickness=0.02,
        center_column_radius=0.16,
        estimated_volume=3.1,
        estimated_plasma_volume=1.2,
        notes="test candidate",
    )


def test_process_adapter_generates_input_deck_without_execution(tmp_path, monkeypatch):
    template = tmp_path / "template_IN.DAT"
    template.write_text(
        "\n".join(
            [
                "runtitle = generic large tokamak * short descriptive title",
                "rmajor = 8.0 * plasma major radius",
                "aspect = 3.0 * aspect ratio",
                "kappa = 1.85 * elongation",
                "triang = 0.5 * triangularity",
                "b_plasma_toroidal_on_axis = 5.3 * toroidal field",
                "dr_shld_inboard = 0.3 * shield",
                "dr_tf_inboard = 1.2 * centerpost",
                "p_hcd_primary_extra_heat_mw = 75.0 * heating",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv(TEMPLATE_ENV_VAR, str(template))
    monkeypatch.delenv(EXECUTE_ENV_VAR, raising=False)

    adapter = PROCESSAdapter()
    adapter._available = True
    adapter.prepare_run("test-run", tmp_path / "process")

    result = adapter.run(_candidate())

    assert result.status == "NOT_EVALUATED"
    assert result.available is True
    assert result.raw_output_path is not None
    output = Path(result.raw_output_path)
    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert "Simulation-only feasibility research input" in text
    assert "candidate_id = process-test-candidate" in text
    assert "rmajor = 0.8 * plasma major radius" in text
    assert "b_plasma_toroidal_on_axis = 6.5 * toroidal field" in text
    assert "p_plant_electric_net_required_mw" in text


def test_process_adapter_text_mfile_fallback_parser(tmp_path):
    mfile = tmp_path / "MFILE.DAT"
    mfile.write_text("ifail = 1\nrmajor = 0.8\nq95 = 3.4\n", encoding="utf-8")

    metrics = PROCESSAdapter().parse_results(mfile)

    assert metrics["ifail"] == 1.0
    assert metrics["rmajor"] == 0.8
    assert metrics["q95"] == 3.4
