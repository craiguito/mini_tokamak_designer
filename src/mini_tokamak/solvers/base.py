"""Base solver adapter interface."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Iterable

from mini_tokamak.schemas import Candidate, SolverResult


class SolverAdapter(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(self, candidate: Candidate) -> SolverResult:
        raise NotImplementedError

    def parse_results(self, raw: object) -> dict[str, object]:
        return {"raw": raw}

    def prepare_run(self, run_id: str, output_dir: str | Path) -> None:
        """Give adapters a per-run directory for generated solver inputs/outputs."""

    def fallback_result(self, candidate: Candidate, reason: str) -> SolverResult:
        return SolverResult(
            solver=self.name,
            status="LOW_FIDELITY_PLACEHOLDER",
            available=False,
            metrics={"candidate_id": candidate.candidate_id},
            message=reason,
        )


def module_available(module_names: Iterable[str]) -> bool:
    return any(importlib.util.find_spec(module_name) is not None for module_name in module_names)


def executable_available(names: Iterable[str]) -> bool:
    return any(shutil.which(name) for name in names)


def run_command(command: list[str], timeout_s: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout_s, check=False)
