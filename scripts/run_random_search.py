from pathlib import Path

from mini_tokamak.optimization.random_search import run_random_search


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    summary = run_random_search(root / "configs" / "design_space.car_sized.yaml", n=100, project_root=root)
    print(summary.model_dump_json(indent=2))

