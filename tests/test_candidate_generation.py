from pathlib import Path

from mini_tokamak.config import load_design_space
from mini_tokamak.design.candidate import generate_candidates


def test_candidate_generation_schema_fields():
    root = Path(__file__).resolve().parents[1]
    space = load_design_space(root / "configs" / "design_space.car_sized.yaml")
    candidates = generate_candidates(space, 5, seed=1)
    assert len(candidates) == 5
    assert all(c.R > 0 and c.a > 0 for c in candidates)
    assert all(c.estimated_plasma_volume > 0 for c in candidates)

