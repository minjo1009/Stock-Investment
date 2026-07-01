from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.l3_relation_graph_v2_4152.builder import build_from_config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/l3_relation_graph_v2_4152.json")
    args = parser.parse_args()
    manifest = build_from_config(args.config)
    counts = manifest["output_counts"]
    print(
        "[TASK-4152] built "
        f"edges={counts['l3_relation_edges']} "
        f"clusters={counts['l3_event_clusters']} "
        f"graphs={counts['l3_relation_graphs']} "
        f"gaps={counts['l3_coverage_gaps']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

