from pathlib import Path

from mini_tokamak.config import load_design_space
from mini_tokamak.design.candidate import generate_candidate
from mini_tokamak.design.constraints import evaluate_constraints
from mini_tokamak.design.scoring import objective_score


def test_objective_score_is_non_negative():
    root = Path(__file__).resolve().parents[1]
    space = load_design_space(root / "configs" / "design_space.car_sized.yaml")
    candidate = generate_candidate(space)
    evaluation = evaluate_constraints(candidate, space)
    assert objective_score(candidate, evaluation) >= 0

