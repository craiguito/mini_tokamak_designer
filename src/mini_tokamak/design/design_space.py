"""Design-space helpers."""

from __future__ import annotations

from mini_tokamak.schemas import Candidate, DesignSpaceConfig


def envelope_dimensions(candidate: Candidate) -> dict[str, float]:
    return {
        "length_m": candidate.machine_length,
        "width_m": candidate.machine_width,
        "height_m": candidate.machine_height,
    }


def fits_envelope(candidate: Candidate, space: DesignSpaceConfig) -> bool:
    dims = envelope_dimensions(candidate)
    return (
        dims["length_m"] <= space.max_length_m
        and dims["width_m"] <= space.max_width_m
        and dims["height_m"] <= space.max_height_m
    )

