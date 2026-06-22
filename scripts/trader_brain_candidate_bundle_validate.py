from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED = {
    "candidate_bundle_id",
    "source_graph_id",
    "asof_ts",
    "thesis_question",
    "supporting_node_ids",
    "supporting_edge_ids",
    "contradiction_node_ids",
    "invalidation_edge_ids",
    "weakest_layer",
    "unresolved_gaps",
    "bundle_state",
    "forbidden_output_audit",
    "pass_does_not_mean",
}

ALLOWED_STATES = {"research_review_only", "context_only", "blocked_by_gap", "blocked_by_contradiction"}
FORBIDDEN_MARKERS = {
    "buy_signal",
    "sell_signal",
    "trade_permission",
    "position_sizing",
    "backtest_eligibility",
    "alpha_score",
    "global_rank",
    "real_capital",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_candidate_bundles(path: Path) -> list[str]:
    errors: list[str] = []
    rows = read_csv(path)
    if not rows:
        return [f"{path}: no rows"]
    missing = REQUIRED - set(rows[0].keys())
    if missing:
        return [f"{path.name}: missing columns {','.join(sorted(missing))}"]
    seen: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        bundle_id = row.get("candidate_bundle_id", "")
        scope = f"{path.name} row {idx} {bundle_id or '<missing>'}"
        if not bundle_id:
            errors.append(f"{scope}: missing candidate_bundle_id")
        if bundle_id in seen:
            errors.append(f"{scope}: duplicate candidate_bundle_id")
        seen.add(bundle_id)
        if row.get("bundle_state") not in ALLOWED_STATES:
            errors.append(f"{scope}: invalid bundle_state {row.get('bundle_state')}")
        for field in ["source_graph_id", "asof_ts", "thesis_question", "supporting_node_ids", "supporting_edge_ids", "weakest_layer", "forbidden_output_audit", "pass_does_not_mean"]:
            if not row.get(field):
                errors.append(f"{scope}: missing {field}")
        if row.get("invalidation_edge_ids") and row.get("bundle_state") not in {"blocked_by_contradiction", "blocked_by_gap", "context_only"}:
            errors.append(f"{scope}: invalidation edge must block or context-limit bundle")
        if row.get("unresolved_gaps") and row.get("bundle_state") == "research_review_only":
            errors.append(f"{scope}: unresolved gap cannot be research_review_only")
        for field, value in row.items():
            if field in {"forbidden_output_audit", "pass_does_not_mean"}:
                continue
            lowered = str(value).lower()
            for marker in FORBIDDEN_MARKERS:
                if marker in lowered:
                    errors.append(f"{scope}: forbidden output marker {marker} in {field}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundles", required=True, type=Path)
    args = parser.parse_args()
    errors = validate_candidate_bundles(args.bundles)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_CANDIDATE_BUNDLE_ERROR] {error}")
        sys.exit(1)
    print(f"[TRADER_BRAIN_CANDIDATE_BUNDLE_OK] {args.bundles}")


if __name__ == "__main__":
    main()
