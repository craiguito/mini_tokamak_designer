"""STEP export entrypoint."""

from __future__ import annotations

from pathlib import Path

from mini_tokamak.cad.cadquery_adapter import CadQueryAdapter
from mini_tokamak.schemas import Candidate


def export_step_if_available(candidate: Candidate, output_dir: str | Path) -> str | None:
    return CadQueryAdapter().export_step(candidate, output_dir)

