"""Optional BoTorch search interface."""

from __future__ import annotations


def is_available() -> bool:
    try:
        import botorch  # noqa: F401
        import torch  # noqa: F401
    except Exception:
        return False
    return True

