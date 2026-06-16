"""Broad physical-bound checks."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate


def within_mvp_bounds(candidate: Candidate) -> bool:
    return 0.1 <= candidate.R <= 10.0 and 0.05 <= candidate.a <= 5.0 and 0.1 <= candidate.Bt <= 30.0

