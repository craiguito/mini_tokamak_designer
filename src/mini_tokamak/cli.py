"""Command-line interface for MiniTokamak Designer."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mini_tokamak.cad.cross_section import export_cross_section
from mini_tokamak.cad.export_step import export_step_if_available
from mini_tokamak.config import project_root_from_path
from mini_tokamak.optimization.optuna_search import run_optuna_search
from mini_tokamak.optimization.random_search import run_random_search
from mini_tokamak.schemas import CandidateResult
from mini_tokamak.solvers import default_adapters
from mini_tokamak.storage.db import best_results, list_runs

app = typer.Typer(help="MiniTokamak Designer feasibility-search CLI.")
console = Console()


def repo_root() -> Path:
    return project_root_from_path(Path(__file__).resolve())


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    if p.exists() or p.is_absolute():
        return p
    candidate = repo_root() / p
    return candidate if candidate.exists() else p


@app.command()
def verify() -> None:
    """Print available core libraries and external solver adapters."""
    modules = [
        "numpy",
        "scipy",
        "pandas",
        "xarray",
        "pydantic",
        "matplotlib",
        "plotly",
        "duckdb",
        "h5py",
        "zarr",
        "typer",
        "rich",
        "optuna",
        "torch",
        "jax",
        "openmdao",
        "mlflow",
        "cadquery",
        "paramak",
        "openmc",
        "freegs",
        "torax",
        "openfusiontoolkit",
        "OpenFUSIONToolkit",
    ]
    import importlib.util

    table = Table(title="MiniTokamak Designer stack verification")
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Notes")
    for module in modules:
        found = importlib.util.find_spec(module) is not None
        table.add_row(module, "PASS" if found else "NOT_EVALUATED", "importable" if found else "missing")
    for adapter in default_adapters():
        available = adapter.is_available()
        table.add_row(adapter.name, "PASS" if available else "LOW_FIDELITY_PLACEHOLDER", "adapter probe")
    console.print(table)


@app.command()
def run(
    config: Path = typer.Option(..., "--config", help="Design-space YAML config."),
    n: int = typer.Option(100, "--n", min=1, help="Number of candidates."),
    mode: str = typer.Option("random", "--mode", help="random or optuna."),
    seed: int = typer.Option(42, "--seed", help="Random seed."),
    fuse_top_n: int = typer.Option(
        0,
        "--fuse-top-n",
        min=0,
        help="Run the FUSE actor pass on the top N ranked candidates after screening.",
    ),
    fuse_actors: str = typer.Option(
        "ActorPFdesign",
        "--fuse-actors",
        help="Comma-separated FUSE actors for --fuse-top-n, e.g. ActorPFdesign,ActorCXbuild.",
    ),
    torax_top_n: int = typer.Option(
        0,
        "--torax-top-n",
        min=0,
        help="Run the TORAX CPU transport smoke on the top N ranked candidates after screening.",
    ),
) -> None:
    """Run a design-space search."""
    config_path = resolve_path(config)
    root = repo_root()
    if mode == "random":
        summary = run_random_search(
            config_path,
            n=n,
            project_root=root,
            seed=seed,
            fuse_top_n=fuse_top_n,
            fuse_actors=fuse_actors,
            torax_top_n=torax_top_n,
        )
    elif mode == "optuna":
        summary = run_optuna_search(
            config_path,
            n=n,
            project_root=root,
            fuse_top_n=fuse_top_n,
            fuse_actors=fuse_actors,
            torax_top_n=torax_top_n,
        )
    else:
        raise typer.BadParameter("mode must be 'random' or 'optuna'")
    console.print(f"Run complete: [bold]{summary.run_id}[/bold]")
    console.print(f"Output: {summary.output_dir}")
    console.print(f"Best candidate: {summary.best_candidate_id}")
    console.print(f"Best score: {summary.best_score}")


@app.command()
def cad(candidate_json: Path = typer.Argument(..., help="CandidateResult JSON file.")) -> None:
    """Generate CAD fallback output for a saved candidate result."""
    path = resolve_path(candidate_json)
    data = json.loads(path.read_text(encoding="utf-8"))
    result = CandidateResult(**data)
    out_dir = repo_root() / "data" / "cad" / result.run_id
    paths = export_cross_section(result.candidate, out_dir)
    step_path = export_step_if_available(result.candidate, out_dir)
    console.print({"cross_section": paths, "step": step_path})


@app.command()
def report(run_id: str) -> None:
    """Print report paths for a run."""
    root = repo_root()
    report_dir = root / "data" / "reports" / run_id
    console.print(f"Markdown: {report_dir / 'report.md'}")
    console.print(f"HTML: {report_dir / 'report.html'}")


@app.command("list-runs")
def list_runs_cmd() -> None:
    """List recorded runs."""
    db_path = repo_root() / "data" / "runs" / "mini_tokamak.duckdb"
    table = Table(title="Runs")
    for col in ["run_id", "created_at", "mode", "n_requested", "output_dir"]:
        table.add_column(col)
    for row in list_runs(db_path):
        table.add_row(
            str(row["run_id"]),
            str(row["created_at"]),
            str(row["mode"]),
            str(row["n_requested"]),
            str(row["output_dir"]),
        )
    console.print(table)


@app.command("show-best")
def show_best(limit: int = typer.Option(10, "--limit", min=1)) -> None:
    """Show best candidates across runs."""
    db_path = repo_root() / "data" / "runs" / "mini_tokamak.duckdb"
    table = Table(title="Best candidates")
    for col in ["candidate_id", "score", "feasibility", "failure", "R", "a", "Bt", "Ip"]:
        table.add_column(col)
    for row in best_results(db_path, limit=limit):
        table.add_row(
            str(row["candidate_id"])[:8],
            f"{float(row['objective_score']):.2f}",
            f"{float(row['feasibility_score']):.2f}",
            str(row["dominant_failure_reason"]),
            f"{float(row['R']):.2f}",
            f"{float(row['a']):.2f}",
            f"{float(row['Bt']):.1f}",
            f"{float(row['Ip']):.1f}",
        )
    console.print(table)


if __name__ == "__main__":
    app()
