from pathlib import Path

from mini_tokamak.reporting.plots import plot_torax_transport_comparison
from mini_tokamak.reporting.report_md import render_markdown_report
from mini_tokamak.schemas import Candidate, CandidateResult, ConstraintEvaluation, RunSummary, SolverResult


def _candidate(candidate_id: str, radius: float) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        machine_type="compact_tokamak",
        fuel_mode="DD_research",
        R=radius,
        a=0.35,
        aspect_ratio=radius / 0.35,
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


def _result(candidate_id: str, rank: int, q95: float, heat_load: float) -> CandidateResult:
    candidate = _candidate(candidate_id, radius=0.9 + 0.1 * rank)
    constraints = ConstraintEvaluation(
        checks=[],
        metrics={},
        feasibility_score=50.0,
        dominant_failure_reason="test",
    )
    torax = SolverResult(
        solver="TORAX",
        status="WARNING",
        available=True,
        message="TORAX short CPU transport run completed.",
        metrics={
            "stage": "run_torax",
            "top_candidate_rank": rank,
            "torax_final_q95": q95,
            "torax_final_fgw_n_e_line_avg": 0.2 * rank,
            "torax_final_P_SOL_total_MW": 10.0 + rank,
            "torax_final_SOL_heat_load_MW_m2": heat_load,
            "torax_transport_constraint_status": "WARNING",
            "torax_transport_constraint_reasons": ["torax_sol_heat_exhaust_proxy_warning"],
        },
    )
    return CandidateResult(
        run_id="test-run",
        candidate=candidate,
        constraints=constraints,
        solver_results=[torax],
        objective_score=60.0 - rank,
    )


def test_torax_transport_plot_is_generated_for_executed_results(tmp_path):
    results = [
        _result("candidate-one", rank=1, q95=4.0, heat_load=8.0),
        _result("candidate-two", rank=2, q95=2.5, heat_load=18.0),
    ]

    path = plot_torax_transport_comparison(results, tmp_path)

    assert path is not None
    assert Path(path).exists()
    assert Path(path).name == "torax_transport_comparison.png"


def test_markdown_report_includes_torax_ranked_comparison_table():
    results = [
        _result("candidate-one", rank=1, q95=4.0, heat_load=8.0),
        _result("candidate-two", rank=2, q95=2.5, heat_load=18.0),
    ]
    summary = RunSummary(
        run_id="test-run",
        config_path="configs/test.yaml",
        mode="random",
        n_requested=2,
        n_completed=2,
        best_candidate_id="candidate-one",
        best_score=59.0,
        output_dir="data/runs/test-run",
    )

    report = render_markdown_report(summary, results, plot_paths=[], cad_paths={})

    assert "## TORAX Transport Summary" in report
    assert "| rank | candidate_id | status | q95 | fGW line | P_SOL MW | SOL MW/m2 | comparison | reason |" in report
    assert "| 1 | `candidat`" in report
    assert "`torax_sol_heat_exhaust_proxy_warning`" in report
