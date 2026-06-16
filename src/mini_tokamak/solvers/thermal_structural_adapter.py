"""Reserved thermal/structural adapter."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter


class ThermalStructuralAdapter(SolverAdapter):
    name = "thermal_structural_proxy"

    def is_available(self) -> bool:
        return True

    def run(self, candidate: Candidate) -> SolverResult:
        return SolverResult(
            solver=self.name,
            status="LOW_FIDELITY_PLACEHOLDER",
            available=True,
            metrics={"center_column_radius_m": candidate.center_column_radius},
            message="Integrated structural analysis is not implemented; see constraint proxies.",
        )

