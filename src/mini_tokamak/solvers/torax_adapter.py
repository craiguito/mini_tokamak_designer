"""TORAX transport adapter."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate, SolverResult
from mini_tokamak.solvers.base import SolverAdapter, module_available


class TORAXAdapter(SolverAdapter):
    name = "TORAX"

    def is_available(self) -> bool:
        return module_available(["torax"])

    def run(self, candidate: Candidate) -> SolverResult:
        if not self.is_available():
            return self.fallback_result(candidate, "TORAX is not importable in this environment.")
        return SolverResult(
            solver=self.name,
            status="NOT_EVALUATED",
            available=True,
            metrics={"candidate_id": candidate.candidate_id},
            message="TORAX import works. MVP pulse/profile configuration is pending.",
        )

