"""Random-search MVP workflow."""

from __future__ import annotations

from pathlib import Path

from rich.progress import track

from mini_tokamak.cad.cross_section import export_cross_section
from mini_tokamak.cad.export_step import export_step_if_available
from mini_tokamak.config import load_design_space, project_root_from_path
from mini_tokamak.design.candidate import generate_candidates
from mini_tokamak.design.constraints import evaluate_constraints
from mini_tokamak.design.scoring import objective_score
from mini_tokamak.reporting.plots import generate_plots
from mini_tokamak.reporting.report_html import write_html_report
from mini_tokamak.reporting.report_md import write_markdown_report
from mini_tokamak.schemas import CandidateResult, RunSummary
from mini_tokamak.solvers import default_adapters
from mini_tokamak.solvers.fuse_adapter import FUSEAdapter, parse_actor_sequence
from mini_tokamak.storage.db import connect, insert_candidate_result, insert_run, replace_candidate_result
from mini_tokamak.storage.run_store import (
    ensure_run_dirs,
    make_run_id,
    write_all_results,
    write_candidate_json,
    write_top_csv,
)


def run_random_search(
    config_path: str | Path,
    n: int,
    project_root: str | Path | None = None,
    seed: int | None = 42,
    fuse_top_n: int = 0,
    fuse_actors: str | None = None,
) -> RunSummary:
    config_path = Path(config_path)
    root = Path(project_root) if project_root else project_root_from_path(config_path)
    space = load_design_space(config_path)
    run_id = make_run_id()
    dirs = ensure_run_dirs(root, run_id)
    db_path = root / "data" / "runs" / "mini_tokamak.duckdb"
    adapters = default_adapters()
    external_dir = dirs["run"] / "external_solvers"
    for adapter in adapters:
        adapter.prepare_run(run_id, external_dir / adapter.name.lower().replace(" ", "_"))

    results: list[CandidateResult] = []
    with connect(db_path) as conn:
        insert_run(conn, run_id, str(config_path), "random", n, str(dirs["run"]))
        for candidate in track(generate_candidates(space, n, seed=seed), description="Screening"):
            constraints = evaluate_constraints(candidate, space)
            solver_results = [adapter.run(candidate) for adapter in adapters]
            constraints.external_solver_support = any(
                result.available and result.status == "PASS" for result in solver_results
            )
            constraints.viability_claim = constraints.external_solver_support and not any(
                check.status == "FAIL" for check in constraints.checks
            )
            result = CandidateResult(
                run_id=run_id,
                candidate=candidate,
                constraints=constraints,
                solver_results=solver_results,
                objective_score=objective_score(candidate, constraints),
            )
            results.append(result)
            write_candidate_json(result, dirs["results"])
            insert_candidate_result(conn, result)

    results = sorted(results, key=lambda r: r.objective_score, reverse=True)
    _run_fuse_actor_pass(
        results=results,
        adapters=adapters,
        db_path=db_path,
        results_dir=dirs["results"],
        top_n=fuse_top_n,
        actors=parse_actor_sequence(fuse_actors),
    )
    write_all_results(results, dirs["run"] / "all_results.json")
    write_top_csv(results, dirs["run"] / "top_candidates.csv")
    plot_paths = generate_plots(results, dirs["plots"])

    cad_paths: dict[str, str | None] = {}
    if results:
        cad_paths.update(export_cross_section(results[0].candidate, dirs["cad"]))
        cad_paths["step"] = export_step_if_available(results[0].candidate, dirs["cad"])

    summary = RunSummary(
        run_id=run_id,
        config_path=str(config_path),
        mode="random",
        n_requested=n,
        n_completed=len(results),
        best_candidate_id=results[0].candidate.candidate_id if results else None,
        best_score=results[0].objective_score if results else None,
        output_dir=str(dirs["run"]),
    )
    md_path = write_markdown_report(
        summary, results, plot_paths, cad_paths, dirs["reports"] / "report.md"
    )
    write_html_report(md_path, dirs["reports"] / "report.html")
    return summary


def _run_fuse_actor_pass(
    results: list[CandidateResult],
    adapters: list[object],
    db_path: Path,
    results_dir: Path,
    top_n: int,
    actors: list[str],
) -> None:
    if top_n <= 0 or not results:
        return
    fuse_adapter = next((adapter for adapter in adapters if isinstance(adapter, FUSEAdapter)), None)
    if fuse_adapter is None:
        return

    selected = results[: min(top_n, len(results))]
    with connect(db_path) as conn:
        for rank, result in enumerate(
            track(selected, description="FUSE actor pass"),
            start=1,
        ):
            solver_result = fuse_adapter.run_actor_sequence(result.candidate, rank, actors=actors)
            result.solver_results.append(solver_result)
            result.constraints.external_solver_support = any(
                item.available and item.status == "PASS" for item in result.solver_results
            )
            result.constraints.viability_claim = result.constraints.external_solver_support and not any(
                check.status == "FAIL" for check in result.constraints.checks
            )
            write_candidate_json(result, results_dir)
            replace_candidate_result(conn, result)
