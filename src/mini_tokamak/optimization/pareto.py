"""Pareto-front helpers."""

from __future__ import annotations

from mini_tokamak.schemas import CandidateResult


def simple_pareto_front(results: list[CandidateResult]) -> list[CandidateResult]:
    front: list[CandidateResult] = []
    for result in sorted(results, key=lambda r: r.objective_score, reverse=True):
        width = result.candidate.machine_width
        if not any(
            other.objective_score >= result.objective_score and other.candidate.machine_width <= width
            for other in front
        ):
            front.append(result)
    return front

