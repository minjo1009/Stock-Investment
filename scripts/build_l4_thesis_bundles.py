from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.l4_thesis_bundle.builder import build_l4_thesis_bundles


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/l4_thesis_bundle_4156.json")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    result = build_l4_thesis_bundles(inputs=config["inputs"], output_dir=config["outputs"]["artifact_dir"])
    print(
        "[TASK-4156] built "
        f"bundles={result.get('bundle_count', 0)} "
        f"evidence_links={result.get('evidence_link_count', 0)} "
        f"blockers={result.get('blocker_count', 0)} "
        f"validation_status={result.get('validation_status')}"
    )
    return 0 if result.get("validation_status") != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

