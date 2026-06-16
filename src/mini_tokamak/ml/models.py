"""Surrogate model placeholders."""

from __future__ import annotations


class SurrogateNotTrainedError(RuntimeError):
    """Raised when a surrogate model is requested before training."""

