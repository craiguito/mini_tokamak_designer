"""Markdown run reports."""

from __future__ import annotations

from pathlib import Path

from mini_tokamak.reporting.failure_report import dominant_failure_counts
from mini_tokamak.schemas import CandidateResult, RunSummary


def render_markdown_report(
    summary: RunSummary,
    results: list[CandidateResult],
    plot_paths: list[str],
    cad_paths: dict[str, str | None],
) -> str:
    top = sorted(results, key=lambda r: r.objective_score, reverse=True)[:10]
    failure_counts = dominant_failure_counts(results)
    best = top[0] if top else None

    lines = [
        "# MiniTokamak Designer Run Report",
        "",
        "This report is a research-grade feasibility screen, not a construction plan.",
        "All built-in physics results are LOW_FIDELITY_PLACEHOLDER unless an external solver result says otherwise.",
        "",
        "## Run Summary",
        "",
        f"- Run ID: `{summary.run_id}`",
        f"- Mode: `{summary.mode}`",
        f"- Requested candidates: `{summary.n_requested}`",
        f"- Completed candidates: `{summary.n_completed}`",
        f"- Config: `{summary.config_path}`",
        f"- Output directory: `{summary.output_dir}`",
        "",
        "## Best Candidate",
        "",
    ]
    if best:
        c = best.candidate
        lines.extend(
            [
                f"- Candidate ID: `{c.candidate_id}`",
                f"- Machine type: `{c.machine_type}`",
                f"- Fuel mode: `{c.fuel_mode}`",
                f"- Objective score: `{best.objective_score:.2f}`",
                f"- Feasibility score: `{best.constraints.feasibility_score:.2f}`",
                f"- Dominant failure reason: `{best.constraints.dominant_failure_reason}`",
                f"- Envelope: `{c.machine_length:.2f} x {c.machine_width:.2f} x {c.machine_height:.2f} m`",
                f"- R/a/Bt/Ip: `{c.R:.3f} m / {c.a:.3f} m / {c.Bt:.2f} T / {c.Ip:.2f} MA`",
                f"- Viability claim: `{best.constraints.viability_claim}`",
                "",
                "### Best Candidate Checks",
                "",
            ]
        )
        for check in best.constraints.checks:
            lines.append(f"- `{check.status}` `{check.name}`: {check.message} Value: `{check.value}`")
        lines.extend(["", "### Best Candidate Solver Results", ""])
        for solver in best.solver_results:
            lines.append(f"- `{solver.status}` `{solver.solver}`: {solver.message}")
            failure_actor = solver.metrics.get("dominant_failure_actor")
            if failure_actor:
                lines.append(f"  - Dominant FUSE actor failure: `{failure_actor}`")
            result_path = solver.metrics.get("result_path") or solver.raw_output_path
            if result_path:
                lines.append(f"  - Raw output: `{result_path}`")
    else:
        lines.append("No candidates completed.")

    lines.extend(["", "## Dominant Failure Counts", ""])
    for name, count in failure_counts.most_common():
        lines.append(f"- `{name}`: `{count}`")

    lines.extend(_torax_transport_summary(results))

    lines.extend(["", "## Top Candidates", ""])
    lines.append("| rank | candidate_id | score | feasibility | dominant failure | R | a | Bt | Ip |")
    lines.append("|---:|---|---:|---:|---|---:|---:|---:|---:|")
    for i, result in enumerate(top, start=1):
        c = result.candidate
        lines.append(
            f"| {i} | `{c.candidate_id[:8]}` | {result.objective_score:.2f} | "
            f"{result.constraints.feasibility_score:.2f} | `{result.constraints.dominant_failure_reason}` | "
            f"{c.R:.2f} | {c.a:.2f} | {c.Bt:.1f} | {c.Ip:.1f} |"
        )

    lines.extend(["", "## Plots", ""])
    for path in plot_paths:
        lines.append(f"- `{path}`")

    lines.extend(["", "## CAD Outputs", ""])
    for key, path in cad_paths.items():
        lines.append(f"- `{key}`: `{path}`")

    lines.extend(
        [
            "",
            "## Interpretation Guardrails",
            "",
            "- PASS only means a simple MVP check passed.",
            "- WARNING means the candidate is near or outside a rough engineering screen.",
            "- FAIL means the candidate violates an MVP screen.",
            "- NOT_EVALUATED means the real solver workflow is not configured for that quantity yet.",
            "- LOW_FIDELITY_PLACEHOLDER means a simplified proxy was used.",
            "- A design is not viable unless future high-fidelity solver outputs support that claim.",
            "",
        ]
    )
    return "\n".join(lines)


def _torax_transport_summary(results: list[CandidateResult]) -> list[str]:
    torax_results = [
        (result, solver)
        for result in results
        for solver in result.solver_results
        if solver.solver == "TORAX"
    ]
    if not torax_results:
        return []

    status_counts: dict[str, int] = {}
    executed: list[tuple[CandidateResult, object]] = []
    for result, solver in torax_results:
        status_counts[solver.status] = status_counts.get(solver.status, 0) + 1
        if solver.metrics.get("stage") == "run_torax":
            executed.append((result, solver))

    lines = ["", "## TORAX Transport Summary", ""]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.append(f"- Executed TORAX runs: `{len(executed)}`")

    if not executed:
        lines.append(
            "- TORAX configs were generated but not executed. Set "
            "`MINI_TOKAMAK_TORAX_EXECUTE=1` for a short CPU transport smoke."
        )
        return lines

    lines.extend(
        [
            "",
            "| candidate_id | status | q95 | fGW line | P_SOL MW | SOL MW/m2 | comparison |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for result, solver in executed[:10]:
        metrics = solver.metrics
        lines.append(
            f"| `{result.candidate.candidate_id[:8]}` | `{solver.status}` | "
            f"{_fmt(metrics.get('torax_final_q95'))} | "
            f"{_fmt(metrics.get('torax_final_fgw_n_e_line_avg'))} | "
            f"{_fmt(metrics.get('torax_final_P_SOL_total_MW'))} | "
            f"{_fmt(metrics.get('torax_final_SOL_heat_load_MW_m2'))} | "
            f"`{metrics.get('torax_transport_constraint_status', 'NOT_EVALUATED')}` |"
        )
    lines.append(
        "TORAX transport comparisons are `LOW_FIDELITY_PLACEHOLDER` checks against the MVP "
        "screening proxies; they are not viability claims."
    )
    return lines


def _fmt(value: object) -> str:
    try:
        return f"{float(value):.3g}"
    except (TypeError, ValueError):
        return "-"


def write_markdown_report(
    summary: RunSummary,
    results: list[CandidateResult],
    plot_paths: list[str],
    cad_paths: dict[str, str | None],
    output_path: str | Path,
) -> str:
    text = render_markdown_report(summary, results, plot_paths, cad_paths)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return str(out)
