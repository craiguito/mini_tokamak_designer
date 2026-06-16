"""Configuration loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mini_tokamak.schemas import DesignSpaceConfig


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in YAML file: {path}")
    return data


def load_design_space(path: str | Path) -> DesignSpaceConfig:
    return DesignSpaceConfig(**load_yaml(path))


def project_root_from_path(path: str | Path) -> Path:
    current = Path(path).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd().resolve()

