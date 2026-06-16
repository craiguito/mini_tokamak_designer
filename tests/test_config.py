from pathlib import Path

from mini_tokamak.config import load_design_space


def test_load_car_sized_config():
    root = Path(__file__).resolve().parents[1]
    config = load_design_space(root / "configs" / "design_space.car_sized.yaml")
    assert config.max_length_m == 4.5
    assert "spherical_tokamak" in config.machine_type

