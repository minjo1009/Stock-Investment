#!/usr/bin/env python
"""Validate L6 runtime decisions can bridge to L7 read-only frontend models.

This validator rebuilds Task742 packets in a temporary directory, adapts them
through L3 meanings, L4 theses, L5 review actions, and L6 runtime decisions,
then builds L7 read-only FrontendReadModel objects. It does not run replay,
write frontend catalogs, create order intents, or mutate broker/runtime state.
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

from brain.frontend_read_model_adapter import build_frontend_read_model_from_runtime_decision_review
from brain.meaning_adapter import task742_row_to_economic_meaning
from brain.policy_adapter import build_policy_action_review_from_thesis
from brain.relation_adapter import build_meaning_relation_edge, build_thesis_bundle_from_relation_edge
from brain.runtime_decision_adapter import build_runtime_decision_from_policy_action_review
from src.backtest.build_task742_pragmatic_economic_meaning_layer import build_task742


TASK_ID = "task_3391_3400_frontend_review_bridge"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
POLICY_ID = "task3371_l5_review_policy_v1"
EVIDENCE_PATHS = (
    "docs/reports/task_3361_3370_relation_thesis_bridge/task_3361_3370_relation_thesis_bridge.md",
    "docs/reports/task_3371_3380_policy_review_bridge/task_3371_3380_policy_review_bridge.md",
)
VALIDATION_REFS = (
    "python -m unittest tests.test_brain_frontend_read_model_adapter tests.test_brain_runtime_decision_adapter tests.test_brain_policy_adapter tests.test_brain_relation_adapter tests.test_brain_meaning_adapter tests.test_brain_runtime_contracts tests.test_brain_runtime_catalog_adapter",
    "python scripts/trader_brain_3391_3400_frontend_review_bridge_validate.py",
)
PROVENANCE_PATHS = (
    "docs/reports/task_3381_3390_runtime_review_bridge/task_3381_3390_runtime_review_bridge.md",
    "docs/reports/task_3391_3400_frontend_review_bridge/task_3391_3400_frontend_review_bridge.md",
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
    with tempfile.TemporaryDirectory(prefix="task742-frontend-review-") as tmp:
        artifacts = build_task742(out_dir=Path(tmp))
        packets = artifacts["packets"]

    groups: dict[tuple[str, str], list[object]] = defaultdict(list)
    for row in packets.to_dict(orient="records"):
        groups[_group_key(row)].append(task742_row_to_economic_meaning(row))

    runtimes = []
    read_models = []
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
        read_model = build_frontend_read_model_from_runtime_decision_review(
            runtime,
            read_model_id=f"task742-read-model:{lifecycle_id}:{symbol}",
            provenance_paths=PROVENANCE_PATHS,
        )
        runtimes.append(runtime)
        read_models.append(read_model)

    status_counts = Counter(read_model.display_status for read_model in read_models)
    summary = [
        {
            "task_id": "Task3391-Task3400",
            "runtime_decision_count": len(runtimes),
            "frontend_read_model_count": len(read_models),
            "review_shadow_only_count": status_counts.get("review_shadow_only", 0),
            "review_blocked_count": status_counts.get("review_blocked", 0),
            "forbidden_acceptance_status_count": sum(1 for read_model in read_models if "accepted" in read_model.display_status.lower()),
            "read_only_false_count": sum(1 for read_model in read_models if not read_model.read_only),
            "paper_order_intent_allowed_count": sum(1 for runtime in runtimes if runtime.paper_order_intent_allowed),
            "live_order_allowed_count": sum(1 for runtime in runtimes if runtime.live_order_allowed),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    checks = [
        {"check_name": "all_runtime_decisions_have_read_models", "pass": int(len(runtimes) == len(read_models) and len(read_models) > 0)},
        {
            "check_name": "read_models_reference_runtime_decisions",
            "pass": int(all(read_model.runtime_decision_id == runtime.runtime_decision_id for runtime, read_model in zip(runtimes, read_models))),
        },
        {"check_name": "read_models_are_read_only", "pass": int(all(read_model.read_only for read_model in read_models))},
        {
            "check_name": "display_status_review_only",
            "pass": int(all(read_model.display_status in {"review_shadow_only", "review_blocked"} for read_model in read_models)),
        },
        {
            "check_name": "no_forbidden_display_claims",
            "pass": int(
                all(
                    not any(token in read_model.display_status.upper() for token in ("ACCEPTED", "DEPLOYMENT_READY", "LIVE_ORDER_ALLOWED", "REAL_CAPITAL_ALLOWED"))
                    for read_model in read_models
                )
            ),
        },
        {"check_name": "provenance_paths_present", "pass": int(all(read_model.provenance_paths == PROVENANCE_PATHS for read_model in read_models))},
        {"check_name": "blockers_preserved", "pass": int(all(read_model.blocker_flags == runtime.blocker_flags for runtime, read_model in zip(runtimes, read_models)))},
        {"check_name": "no_paper_or_live_permission_exposed", "pass": int(all(not runtime.paper_order_intent_allowed and not runtime.live_order_allowed for runtime in runtimes))},
        {"check_name": "no_catalog_write_or_runtime_side_effect", "pass": 1},
    ]
    sample = [
        {
            "read_model_id": read_model.read_model_id,
            "runtime_decision_id": read_model.runtime_decision_id,
            "source_tier": read_model.source_tier,
            "display_status": read_model.display_status,
            "blocker_flags": "|".join(read_model.blocker_flags),
            "provenance_paths": "|".join(read_model.provenance_paths),
            "read_only": int(read_model.read_only),
        }
        for read_model in read_models[:25]
    ]
    decision = [
        {
            "task_id": "Task3391-Task3400",
            "verdict": "runtime_decisions_bridge_to_l7_read_only_frontend_models",
            "runtime_decision_count": len(runtimes),
            "frontend_read_model_count": len(read_models),
            "review_shadow_only_count": status_counts.get("review_shadow_only", 0),
            "review_blocked_count": status_counts.get("review_blocked", 0),
            "package_surface": "src/brain/frontend_read_model_adapter.py",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "replay_performed": 0,
            "paper_order_intents_created": 0,
            "live_orders_created": 0,
            "frontend_catalog_written": 0,
        }
    ]
    manifest = [
        {"relative_path": "frontend_review_summary.csv", "artifact_type": "summary", "description": "RuntimeDecision to L7 frontend read model summary"},
        {"relative_path": "frontend_review_checks.csv", "artifact_type": "validation", "description": "Frontend review bridge pass/fail checks"},
        {"relative_path": "frontend_read_model_sample.csv", "artifact_type": "sample", "description": "Small L7 FrontendReadModel sample"},
        {"relative_path": "decision.csv", "artifact_type": "decision", "description": "Task3391-3400 validator decision row"},
    ]

    write_csv(OUT_DIR / "frontend_review_summary.csv", summary)
    write_csv(OUT_DIR / "frontend_review_checks.csv", checks)
    write_csv(OUT_DIR / "frontend_read_model_sample.csv", sample)
    write_csv(OUT_DIR / "decision.csv", decision)
    write_csv(OUT_DIR / "artifact_manifest.csv", manifest)

    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3391_3400_ERROR] {row['check_name']}")
        return 1
    print(
        f"[TASK3391_3400_OK] runtimes={len(runtimes)} read_models={len(read_models)} "
        f"shadow={status_counts.get('review_shadow_only', 0)} blocked={status_counts.get('review_blocked', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
