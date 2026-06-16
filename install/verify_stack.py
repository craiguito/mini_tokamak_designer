"""Verify the MiniTokamak Designer runtime stack without requiring heavy solvers."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


MODULES = [
    "numpy",
    "scipy",
    "pandas",
    "xarray",
    "pydantic",
    "yaml",
    "matplotlib",
    "plotly",
    "rich",
    "typer",
    "duckdb",
    "h5py",
    "zarr",
    "pytest",
    "optuna",
    "torch",
    "jax",
    "openmdao",
    "mlflow",
    "cadquery",
    "paramak",
    "openmc",
    "freegs",
    "torax",
    "openfusiontoolkit",
    "OpenFUSIONToolkit",
]

EXECUTABLES = ["git", "cmake", "ninja", "julia", "process", "openmc", "wsl"]


def module_status(name: str) -> str:
    return "PASS" if importlib.util.find_spec(name) is not None else "NOT_EVALUATED"


def executable_status(name: str) -> str:
    return "PASS" if shutil.which(name) else "NOT_EVALUATED"


def main() -> int:
    print("MiniTokamak Designer stack verification")
    print(f"Repo: {REPO_ROOT}")
    print("\nPython modules:")
    for module in MODULES:
        print(f"  {module:22} {module_status(module)}")
    print("\nExecutables:")
    for exe in EXECUTABLES:
        print(f"  {exe:22} {executable_status(exe)}")
    print("\nSolver adapters:")
    from mini_tokamak.solvers import default_adapters

    for adapter in default_adapters():
        try:
            available = adapter.is_available()
        except Exception as exc:
            available = False
            print(f"  {adapter.name:22} LOW_FIDELITY_PLACEHOLDER ({exc})")
            continue
        print(f"  {adapter.name:22} {'PASS' if available else 'LOW_FIDELITY_PLACEHOLDER'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
