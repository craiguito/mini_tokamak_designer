from pathlib import Path

from mini_tokamak.cad.cross_section import export_cross_section
from mini_tokamak.config import load_design_space
from mini_tokamak.design.candidate import generate_candidate


def test_cross_section_export(tmp_path):
    root = Path(__file__).resolve().parents[1]
    space = load_design_space(root / "configs" / "design_space.car_sized.yaml")
    candidate = generate_candidate(space)
    paths = export_cross_section(candidate, tmp_path)
    assert Path(paths["png"]).exists()
    assert Path(paths["svg"]).exists()

