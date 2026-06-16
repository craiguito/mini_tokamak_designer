"""Failure aggregation helpers."""

from __future__ import annotations

from collections import Counter

from mini_tokamak.schemas import CandidateResult


def dominant_failure_counts(results: list[CandidateResult]) -> Counter[str]:
    return Counter(result.constraints.dominant_failure_reason for result in results)


def check_status_counts(results: list[CandidateResult]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for result in results:
        for check in result.constraints.checks:
            counts[f"{check.name}:{check.status}"] += 1
    return counts

