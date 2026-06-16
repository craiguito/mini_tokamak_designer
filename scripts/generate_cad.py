import json
import sys
from pathlib import Path

from mini_tokamak.cad.cross_section import export_cross_section
from mini_tokamak.cad.export_step import export_step_if_available
from mini_tokamak.schemas import CandidateResult


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/generate_cad.py path/to/candidate_result.json")
    root = Path(__file__).resolve().parents[1]
    result = CandidateResult(**json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    out_dir = root / "data" / "cad" / result.run_id
    print(export_cross_section(result.candidate, out_dir))
    print({"step": export_step_if_available(result.candidate, out_dir)})

