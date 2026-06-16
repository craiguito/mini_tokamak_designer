"""Optional CadQuery STEP export."""

from __future__ import annotations

from pathlib import Path

from mini_tokamak.schemas import Candidate


class CadQueryAdapter:
    name = "CadQuery"

    def is_available(self) -> bool:
        try:
            import cadquery  # noqa: F401
        except Exception:
            return False
        return True

    def export_step(self, candidate: Candidate, output_dir: str | Path) -> str | None:
        if not self.is_available():
            return None
        import cadquery as cq

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        step_path = out / f"{candidate.candidate_id}_plasma_proxy.step"

        r_mm = candidate.R * 1000.0
        a_mm = candidate.a * 1000.0
        z_mm = candidate.kappa * candidate.a * 1000.0

        # A revolved elliptical plasma solid is only a geometry placeholder. It is
        # intentionally not detailed enough to imply hardware construction.
        solid = (
            cq.Workplane("XZ")
            .center(r_mm, 0)
            .ellipse(a_mm, z_mm)
            .revolve(360, (0, 0, 0), (0, 0, 1))
        )
        cq.exporters.export(solid, str(step_path))
        return str(step_path)

