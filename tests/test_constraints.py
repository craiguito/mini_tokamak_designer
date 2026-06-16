from pathlib import Path

from mini_tokamak.config import load_design_space
from mini_tokamak.design.candidate import generate_candidate
from mini_tokamak.design.constraints import evaluate_constraints


def test_constraints_return_required_labels():
    root = Path(__file__).resolve().parents[1]
    space = load_design_space(root / "configs" / "design_space.car_sized.yaml")
    candidate = generate_candidate(space)
    result = evaluate_constraints(candidate, space)
    statuses = {check.status for check in result.checks}
    assert statuses <= {"PASS", "WARNING", "FAIL", "NOT_EVALUATED", "LOW_FIDELITY_PLACEHOLDER"}
    assert result.viability_claim is False
    assert result.dominant_failure_reason

