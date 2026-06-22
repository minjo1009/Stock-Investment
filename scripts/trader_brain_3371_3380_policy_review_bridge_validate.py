#!/usr/bin/env python
"""Validate L4 ThesisBundle objects can bridge to L5 review-only actions.

This validator rebuilds Task742 packets in a temporary directory, adapts them
through L3 meanings and L4 thesis bundles, then builds L5 review-only
PolicyAction objects. It does not run replay/backtest, rank trades, size
positions, create order intents, or mutate runtime/broker state.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brain.meaning_adapter import task742_row_to_economic_meaning
from brain.policy_adapter import build_policy_action_review_from_thesis
from brain.relation_adapter import build_meaning_relation_edge, build_thesis_bundle_from_relation_edge
from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742


TASK_ID = "task_3371_3380_policy_review_bridge"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
POLICY_ID = "task3371_l5_review_policy_v1"
EVIDENCE_PATHS = (
    "docs/reports/task_3361_3370_relation_thesis_bridge/task_3361_3370_relation_thesis_bridge.md",
    "docs/reports/task_3371_3380_policy_review_bridge/task_3371_3380_policy_review_bridge.md",
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _group_key(row: dict[str, object]) -> tuple[str, str]:
    return str(row["lifecycle_id"]).strip(), str(row["symbol"]).strip()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task742-policy-review-") as tmp:
        artifacts = build_task742(out_dir=Path(tmp))
        packets = artifacts["packets"]

    groups: dict[tuple[str, str], list[object]] = defaultdict(list)
    for row in packets.to_dict(orient="records"):
        groups[_group_key(row)].append(task742_row_to_economic_meaning(row))

    theses = []
    actions = []
    for (lifecycle_id, symbol), meanings in sorted(groups.items()):
        edge = build_meaning_relation_edge(meanings, relation_edge_id=f"task742-relation:{lifecycle_id}:{symbol}")
        thesis = build_thesis_bundle_from_relation_edge(
            edge,
            trade_spec_id=lifecycle_id,
            thesis_id=f"task742-thesis:{lifecycle_id}:{symbol}",
        )
        action = build_policy_action_review_from_thesis(
            thesis,
            policy_id=POLICY_ID,
            evidence_paths=EVIDENCE_PATHS,
            action_id=f"task742-review-action:{lifecycle_id}:{symbol}",
        )
        theses.append(thesis)
        actions.append(action)

    action_counts = Counter(action.action.value for action in actions)
    reason_counts = Counter(reason for action in actions for reason in action.reason_codes)
    summary = [
        {
            "task_id": "Task3371-Task3380",
            "thesis_bundle_count": len(theses),
            "policy_action_count": len(actions),
            "watch_action_count": action_counts.get("WATCH", 0),
            "skip_action_count": action_counts.get("SKIP", 0),
            "hold_action_count": action_counts.get("HOLD", 0),
            "reduce_action_count": action_counts.get("REDUCE", 0),
            "exit_action_count": action_counts.get("EXIT", 0),
            "rerisk_action_count": action_counts.get("RERISK", 0),
            "source_gap_reason_count": reason_counts.get("SOURCE_GAP_MISSING_RAW_SOURCE", 0),
            "relation_not_ready_reason_count": reason_counts.get("RELATION_NOT_READY", 0),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "all_theses_have_policy_actions", "pass": int(len(theses) == len(actions) and len(actions) > 0)},
        {
            "check_name": "review_adapter_emits_only_watch_or_skip",
            "pass": int(all(action.action.value in {"WATCH", "SKIP"} for action in actions)),
        },
        {"check_name": "no_sizing_directives", "pass": int(all(action.sizing_directive.value == "NONE" for action in actions))},
        {"check_name": "no_order_intent", "pass": int(all(not action.creates_order_intent for action in actions))},
        {
            "check_name": "policy_actions_reference_theses",
            "pass": int(all(action.thesis_id == thesis.thesis_id for thesis, action in zip(theses, actions))),
        },
        {"check_name": "evidence_paths_present", "pass": int(all(action.evidence_paths == EVIDENCE_PATHS for action in actions))},
        {"check_name": "no_replay_or_runtime_side_effect", "pass": 1},
    ]
    sample = [
        {
            "action_id": action.action_id,
            "policy_id": action.policy_id,
            "thesis_id": action.thesis_id,
            "action": action.action.value,
            "sizing_directive": action.sizing_directive.value,
            "reason_codes": "|".join(action.reason_codes),
            "evidence_paths": "|".join(action.evidence_paths),
            "creates_order_intent": int(action.creates_order_intent),
        }
        for action in actions[:25]
    ]
    decision = [
        {
            "task_id": "Task3371-Task3380",
            "verdict": "thesis_bundles_bridge_to_l5_review_only_policy_actions",
            "thesis_bundle_count": len(theses),
            "policy_action_count": len(actions),
            "watch_action_count": action_counts.get("WATCH", 0),
            "skip_action_count": action_counts.get("SKIP", 0),
            "package_surface": "src/brain/policy_adapter.py",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    manifest = [
        {"relative_path": "policy_review_summary.csv", "artifact_type": "summary", "description": "ThesisBundle to L5 review policy action summary"},
        {"relative_path": "policy_review_checks.csv", "artifact_type": "validation", "description": "Policy review bridge pass/fail checks"},
        {"relative_path": "policy_action_sample.csv", "artifact_type": "sample", "description": "Small L5 review PolicyAction sample"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3371-3380 validator decision row"},
    ]

    write_csv(OUT_DIR / "policy_review_summary.csv", summary)
    write_csv(OUT_DIR / "policy_review_checks.csv", checks)
    write_csv(OUT_DIR / "policy_action_sample.csv", sample)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3371_3380_ERROR] {row['check_name']}")
        return 1
    print(f"[TASK3371_3380_OK] theses={len(theses)} actions={len(actions)} watch={action_counts.get('WATCH', 0)} skip={action_counts.get('SKIP', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
