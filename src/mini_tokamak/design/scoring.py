"""Objective scoring helpers."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate, ConstraintEvaluation


def objective_score(candidate: Candidate, evaluation: ConstraintEvaluation) -> float:
    performance = float(evaluation.metrics.get("performance_proxy", 0.0))
    compactness_penalty = 2.0 * max(candidate.machine_width - 2.0, 0.0)
    score = max(0.0, evaluation.feasibility_score + min(performance, 15.0) - compactness_penalty)
    if any(check.status == "FAIL" for check in evaluation.checks):
        return min(score, 59.0)
    return score
