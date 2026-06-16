from pathlib import Path

from mini_tokamak.optimization.optuna_search import run_optuna_search


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    summary = run_optuna_search(root / "configs" / "design_space.car_sized.yaml", n=100, project_root=root)
    print(summary.model_dump_json(indent=2))

