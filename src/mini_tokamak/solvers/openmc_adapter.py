"""OpenMC neutronics adapter."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter, executable_available, module_available


class OpenMCAdapter(SolverAdapter):
    name = "OpenMC"

    def is_available(self) -> bool:
        return module_available(["openmc"]) or executable_available(["openmc"])

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, "OpenMC is not installed or not on PATH.")
        return SolverResult(
            solver=self.name,
            status="NOT_EVALUATED",
            available=True,
            metrics={
                "candidate_id": candidate.candidate_id,
                "geometry_export_required": True,
            },
            message=(
                "OpenMC is available, but neutronics is intentionally NOT_EVALUATED until "
                "cross-section data and validated geometry are configured."
            ),
        )

