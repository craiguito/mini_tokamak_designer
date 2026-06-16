"""Optuna search wrapper.

The MVP delegates to random search when Optuna is not installed. The interface is
kept stable so a later phase can add informed parameter sampling.
"""

from __future__ import annotations

from pathlib import Path

from mini_tokamak.optimization.random_search import run_random_search


def run_optuna_search(
    config_path: str | Path,
    n: int,
    project_root: str | Path | None = None,
    fuse_top_n: int = 0,
    fuse_actors: str | None = None,
):
    try:
        import optuna  # noqa: F401
    except Exception:
        return run_random_search(
            config_path,
            n=n,
            project_root=project_root,
            fuse_top_n=fuse_top_n,
            fuse_actors=fuse_actors,
        )
    return run_random_search(
        config_path,
        n=n,
        project_root=project_root,
        fuse_top_n=fuse_top_n,
        fuse_actors=fuse_actors,
    )
