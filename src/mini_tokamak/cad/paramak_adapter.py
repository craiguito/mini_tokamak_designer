"""Optional Paramak availability probe."""

from __future__ import annotations

import importlib.util


class ParamakAdapter:
    name = "Paramak"

    def is_available(self) -> bool:
        return importlib.util.find_spec("paramak") is not None

