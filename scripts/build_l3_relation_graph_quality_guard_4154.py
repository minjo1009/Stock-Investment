from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.l3_relation_graph_quality_guard_4154.builder import build_quality_guard


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/l3_relation_graph_quality_guard_4154.json")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    result = build_quality_guard(
        source_dir=config["inputs"]["source_artifact_dir"],
        output_dir=config["outputs"]["artifact_dir"],
    )
    counts = result["output_counts"]
    print(
        "[TASK-4154] built "
        f"quality_rows={counts['graph_quality_summary_rows']} "
        f"clusters={counts['event_clusters_with_limitations']} "
        f"unsupported={counts['unsupported_relation_families']} "
        f"gap_summary={counts['coverage_gap_summary_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

