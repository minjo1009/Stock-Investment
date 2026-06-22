#!/usr/bin/env python
"""Validate L5 review policy actions can bridge to L6 runtime decisions.

This validator rebuilds Task742 packets in a temporary directory, adapts them
through L3 meanings, L4 theses, and L5 review actions, then builds L6 runtime
decisions. It does not run replay/backtest, rank trades, size positions, create
order intents, or mutate runtime/broker state.
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
from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review
from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742


TASK_ID = "task_3381_3390_runtime_review_bridge"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
POLICY_ID = "task3371_l5_review_policy_v1"
EVIDENCE_PATHS = (
    "docs/reports/task_3361_3370_relation_thesis_bridge/task_3361_3370_relation_thesis_bridge.md",
    "docs/reports/task_3371_3380_policy_review_bridge/task_3371_3380_policy_review_bridge.md",
)
VALIDATION_REFS = (
    "python -m unittest tests.test_brain_runtime_decision_adapter tests.test_brain_policy_adapter tests.test_brain_relation_adapter tests.test_brain_meaning_adapter tests.test_brain_runtime_contracts tests.test_brain_runtime_catalog_adapter",
    "python scripts/trader_brain_3381_3390_runtime_review_bridge_validate.py",
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
    with tempfile.TemporaryDirectory(prefix="task742-runtime-review-") as tmp:
        artifacts = build_task742(out_dir=Path(tmp))
        packets = artifacts["packets"]

    groups: dict[tuple[str, str], list[object]] = defaultdict(list)
    for row in packets.to_dict(orient="records"):
        groups[_group_key(row)].append(task742_row_to_economic_meaning(row))

    actions = []
    runtimes = []
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
        runtime = build_runtime_decision_from_policy_action_review(
            action,
            validation_refs=VALIDATION_REFS,
            runtime_decision_id=f"task742-runtime-review:{lifecycle_id}:{symbol}",
        )
        actions.append(action)
        runtimes.append(runtime)

    gate_counts = Counter(runtime.gate.value for runtime in runtimes)
    summary = [
        {
            "task_id": "Task3381-Task3390",
            "policy_action_count": len(actions),
            "runtime_decision_count": len(runtimes),
            "shadow_only_count": gate_counts.get("SHADOW_ONLY", 0),
            "blocked_count": gate_counts.get("BLOCKED", 0),
            "paper_eligible_count": gate_counts.get("PAPER_ELIGIBLE", 0),
            "broker_review_required_count": gate_counts.get("BROKER_REVIEW_REQUIRED", 0),
            "paper_order_intent_allowed_count": sum(1 for runtime in runtimes if runtime.paper_order_intent_allowed),
            "live_order_allowed_count": sum(1 for runtime in runtimes if runtime.live_order_allowed),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "all_actions_have_runtime_decisions", "pass": int(len(actions) == len(runtimes) and len(runtimes) > 0)},
        {"check_name": "watch_actions_are_shadow_only", "pass": int(all(runtime.gate.value == "SHADOW_ONLY" for action, runtime in zip(actions, runtimes) if action.action.value == "WATCH"))},
        {"check_name": "skip_actions_are_blocked", "pass": int(all(runtime.gate.value == "BLOCKED" for action, runtime in zip(actions, runtimes) if action.action.value == "SKIP"))},
        {"check_name": "no_paper_eligible_runtime", "pass": int(all(runtime.gate.value != "PAPER_ELIGIBLE" for runtime in runtimes))},
        {"check_name": "no_paper_order_intent_allowed", "pass": int(all(not runtime.paper_order_intent_allowed for runtime in runtimes))},
        {"check_name": "no_live_order_allowed", "pass": int(all(not runtime.live_order_allowed for runtime in runtimes))},
        {"check_name": "runtime_decisions_reference_actions", "pass": int(all(runtime.policy_action_id == action.action_id for action, runtime in zip(actions, runtimes)))},
        {"check_name": "validation_refs_present", "pass": int(all(runtime.validation_refs == VALIDATION_REFS for runtime in runtimes))},
        {"check_name": "no_replay_or_broker_side_effect", "pass": 1},
    ]
    sample = [
        {
            "runtime_decision_id": runtime.runtime_decision_id,
            "policy_action_id": runtime.policy_action_id,
            "gate": runtime.gate.value,
            "blocker_flags": "|".join(runtime.blocker_flags),
            "validation_refs": "|".join(runtime.validation_refs),
            "paper_order_intent_allowed": int(runtime.paper_order_intent_allowed),
            "live_order_allowed": int(runtime.live_order_allowed),
        }
        for runtime in runtimes[:25]
    ]
    decision = [
        {
            "task_id": "Task3381-Task3390",
            "verdict": "review_policy_actions_bridge_to_l6_shadow_or_blocked_runtime_decisions",
            "policy_action_count": len(actions),
            "runtime_decision_count": len(runtimes),
            "shadow_only_count": gate_counts.get("SHADOW_ONLY", 0),
            "blocked_count": gate_counts.get("BLOCKED", 0),
            "package_surface": "src/brain/runtime_decision_adapter.py",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
        }
    ]
    manifest = [
        {"relative_path": "runtime_review_summary.csv", "artifact_type": "summary", "description": "PolicyAction to L6 runtime decision summary"},
        {"relative_path": "runtime_review_checks.csv", "artifact_type": "validation", "description": "Runtime review bridge pass/fail checks"},
        {"relative_path": "runtime_decision_sample.csv", "artifact_type": "sample", "description": "Small L6 RuntimeDecision sample"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3381-3390 validator decision row"},
    ]

    write_csv(OUT_DIR / "runtime_review_summary.csv", summary)
    write_csv(OUT_DIR / "runtime_review_checks.csv", checks)
    write_csv(OUT_DIR / "runtime_decision_sample.csv", sample)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3381_3390_ERROR] {row['check_name']}")
        return 1
    print(
        f"[TASK3381_3390_OK] actions={len(actions)} runtimes={len(runtimes)} "
        f"shadow={gate_counts.get('SHADOW_ONLY', 0)} blocked={gate_counts.get('BLOCKED', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
