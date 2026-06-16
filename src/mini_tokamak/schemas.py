"""Shared pydantic schemas for design, solver, and storage records."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["PASS", "WARNING", "FAIL", "NOT_EVALUATED", "LOW_FIDELITY_PLACEHOLDER"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RangeSpec(BaseModel):
    min: float
    max: float

    def contains(self, value: float) -> bool:
        return self.min <= value <= self.max


class DesignSpaceConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_length_m: float
    max_width_m: float
    max_height_m: float
    machine_type: list[str]
    fuel_modes: list[str]
    major_radius_R_m: RangeSpec
    minor_radius_a_m: RangeSpec
    aspect_ratio_A: RangeSpec
    elongation_kappa: RangeSpec
    triangularity_delta: RangeSpec
    toroidal_field_Bt_T: RangeSpec
    plasma_current_Ip_MA: RangeSpec
    heating_power_MW: RangeSpec
    shield_thickness_m: RangeSpec
    first_wall_thickness_m: RangeSpec
    center_column_radius_m: RangeSpec


class Candidate(BaseModel):
    candidate_id: str
    timestamp: str = Field(default_factory=utc_now_iso)
    machine_type: str
    fuel_mode: str
    R: float
    a: float
    aspect_ratio: float
    kappa: float
    delta: float
    Bt: float
    Ip: float
    heating_power: float
    shield_thickness: float
    first_wall_thickness: float
    center_column_radius: float
    estimated_volume: float
    estimated_plasma_volume: float
    notes: str = ""

    @property
    def outer_radius(self) -> float:
        return self.R + self.a + self.shield_thickness + self.first_wall_thickness

    @property
    def machine_length(self) -> float:
        return 2.0 * self.outer_radius

    @property
    def machine_width(self) -> float:
        return 2.0 * self.outer_radius

    @property
    def machine_height(self) -> float:
        return 2.0 * (self.kappa * self.a + self.shield_thickness + self.first_wall_thickness)


class ConstraintCheck(BaseModel):
    name: str
    status: Status
    value: float | str | bool | None = None
    limit: float | str | None = None
    message: str
    fidelity: Status = "LOW_FIDELITY_PLACEHOLDER"


class ConstraintEvaluation(BaseModel):
    checks: list[ConstraintCheck]
    metrics: dict[str, float | str | bool]
    feasibility_score: float
    dominant_failure_reason: str
    external_solver_support: bool = False
    viability_claim: bool = False


class SolverResult(BaseModel):
    solver: str
    status: Status
    available: bool
    metrics: dict[str, Any] = Field(default_factory=dict)
    message: str
    raw_output_path: str | None = None


class CandidateResult(BaseModel):
    run_id: str
    candidate: Candidate
    constraints: ConstraintEvaluation
    solver_results: list[SolverResult]
    objective_score: float
    created_at: str = Field(default_factory=utc_now_iso)


class RunSummary(BaseModel):
    run_id: str
    config_path: str
    mode: str
    n_requested: int
    n_completed: int
    best_candidate_id: str | None
    best_score: float | None
    output_dir: str

