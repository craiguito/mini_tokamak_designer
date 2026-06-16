"""Sanity checks that are safe to run without external solvers."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate


def has_positive_geometry(candidate: Candidate) -> bool:
    return all(
        value > 0
        for value in [
            candidate.R,
            candidate.a,
            candidate.aspect_ratio,
            candidate.kappa,
            candidate.Bt,
            candidate.Ip,
            candidate.center_column_radius,
        ]
    )

