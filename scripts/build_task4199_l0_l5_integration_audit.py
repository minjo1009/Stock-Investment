from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "TASK-4199"
OUT = ROOT / "data/artifacts/task_4199_l0_scheduler_deletion_and_l0_l5_integration_audit"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def count_csv(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return sum(1 for _ in csv.DictReader(fh))


def count_jsonl(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig") as fh:
        return sum(1 for line in fh if line.strip())


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_get(node: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = node
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def build() -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    l0 = read_json(ROOT / "data/artifacts/l0_operating_status/current_l0_status.json")
    l1 = read_json(ROOT / "data/artifacts/task_4186_l1_completion_gpt_review_and_audit/task_4186_l1_completion_audit_summary.json")
    l2 = read_json(ROOT / "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l0_l2_hardening_summary.json")
    l3_manifest = read_json(ROOT / "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graph_v2_manifest.json")
    l3_validation = read_json(ROOT / "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graph_validation.json")
    l4_manifest = read_json(ROOT / "data/diagnostics/l4/l4_run_manifest.json")
    l4_validation = read_json(ROOT / "data/diagnostics/l4/l4_validation_report.json")
    l4_scanner = read_json(ROOT / "data/artifacts/task_4176_l4_diagnostic_blocker_taxonomy_scanner_v1/task_4176_l4_scanner_summary.json")

    deleted_scheduler_proof = read_json(OUT / "deleted_scheduler_proof.json")
    deleted_entrypoint_proof = read_json(OUT / "deleted_legacy_entrypoints_proof.json")

    l4_bundle_rows = count_jsonl(ROOT / "data/diagnostics/l4/l4_thesis_bundles.jsonl")
    l4_evidence_rows = count_csv(ROOT / "data/diagnostics/l4/l4_thesis_evidence_links.csv")
    l4_blocker_rows = count_csv(ROOT / "data/diagnostics/l4/l4_thesis_blockers.csv")

    l5_checks_path = ROOT / "data/artifacts/task_3917_l1_l5_institutional_hardening_package/package_validation_checks.csv"
    l5_check_rows = count_csv(l5_checks_path)
    l5_current_builder_exists = any((ROOT / p).exists() for p in [
        "scripts/build_l5_policy_actions.py",
        "src/brain/l5_policy_action",
        "configs/l5_policy_action.json",
    ])

    matrix = [
        {
            "layer": "L0",
            "role": "raw/backfill/realtime source acquisition",
            "latest_active_artifact": "data/artifacts/l0_operating_status/current_l0_status.json",
            "input_from_previous": "external providers",
            "output_to_next": "L1 source packets and L2 refresh via 4147 loop",
            "status": "PARTIAL_RUNNING",
            "evidence": f"newswire {safe_get(l0, 'public_newswire', 'progress_pct')}%, scheduler 4195={safe_get(l0, 'scheduler', 'backfill_recovery', 'last_result_status')}, realtime 4147={safe_get(l0, 'scheduler', 'realtime', 'last_result_status')}",
            "blocker_or_gap": "; ".join(l0.get("blockers") or []) or "none",
            "next_action": "keep continuous guard running; do not open downstream completeness claims until newswire and 5m are complete or terminal-blocked",
        },
        {
            "layer": "L1",
            "role": "normalize article/source packets, mapping, feature-ready packet handoff",
            "latest_active_artifact": "data/artifacts/task_4186_l1_completion_gpt_review_and_audit/task_4186_l1_completion_audit_summary.json",
            "input_from_previous": "L0 current available rows, not full completed universe",
            "output_to_next": "L2 diagnostic feature rows / mapping queues",
            "status": l1.get("closeout_verdict") or "UNKNOWN",
            "evidence": f"ready packets={l1.get('l1_ready_article_packets_after')}, unresolved feature gap={l1.get('feature_materialization_gap_unresolved')}, recall unresolved={l1.get('source_recall_unresolved_after')}",
            "blocker_or_gap": "upstream L0 incomplete; L1 must rerun/refresh as L0 adds rows",
            "next_action": "make L1 refresh proof depend on latest L0 batch watermark, not one-time task completion",
        },
        {
            "layer": "L2",
            "role": "diagnostic feature/materialization layer for swing-trading context",
            "latest_active_artifact": "data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l0_l2_hardening_summary.json",
            "input_from_previous": "L1 article packets and wide packets",
            "output_to_next": "L3 meaning/relation graph inputs",
            "status": "DIAGNOSTIC_FEATURES_PRESENT",
            "evidence": f"L2 rows={l2.get('l2_diagnostic_feature_rows')}, L1 ready={l2.get('l1_article_ready_packets')}, trading eligible={l2.get('trading_eligible_rows')}",
            "blocker_or_gap": "L2 is diagnostic only; latest full L0 incremental completion is not proven fully re-materialized into L2",
            "next_action": "rerun L1/L2 loop after L0 batches and emit freshness/watermark proof",
        },
        {
            "layer": "L3",
            "role": "relation graph and event/coverage graph",
            "latest_active_artifact": "data/artifacts/task_4152_l3_relation_graph_v2/l3_relation_graph_v2_manifest.json",
            "input_from_previous": "L1/L2 task_4146 and task_4147 artifacts",
            "output_to_next": "L4 thesis bundles and blockers",
            "status": l3_validation.get("status") or "UNKNOWN",
            "evidence": f"graphs={safe_get(l3_manifest, 'output_counts', 'l3_relation_graphs')}, edges={safe_get(l3_manifest, 'output_counts', 'l3_relation_edges')}, coverage gaps={safe_get(l3_manifest, 'output_counts', 'l3_coverage_gaps')}",
            "blocker_or_gap": "proto event identity and coverage gaps remain; no ranking/signal authority",
            "next_action": "refresh L3 after L1/L2 watermarks; continue unsupported relation narrowing only where it reduces blocker count",
        },
        {
            "layer": "L4",
            "role": "diagnostic thesis bundles, evidence links, blockers, contradiction scan visibility",
            "latest_active_artifact": "data/diagnostics/l4/l4_run_manifest.json",
            "input_from_previous": "L3 relation graph, L3 quality guard, L1/L2 artifacts",
            "output_to_next": "future L5 review-only policy/action candidate inputs",
            "status": l4_validation.get("status") or "UNKNOWN",
            "evidence": f"bundles={l4_bundle_rows}, evidence_links={l4_evidence_rows}, blockers={l4_blocker_rows}, not_scanned={l4_scanner.get('not_scanned_rows')}",
            "blocker_or_gap": "mostly DRAFT_MIXED; L0 incomplete, unsupported relation, proto event identity, contradiction-not-scanned blockers remain",
            "next_action": "keep L4 diagnostic; do not call it final thesis judgment until blockers burn down and refresh proof exists",
        },
        {
            "layer": "L5",
            "role": "policy/action review boundary and future decision adapter, not current order engine",
            "latest_active_artifact": "data/artifacts/task_3917_l1_l5_institutional_hardening_package/package_validation_checks.csv",
            "input_from_previous": "should consume accepted L4 diagnostic bundles, but current direct L4->L5 builder is absent",
            "output_to_next": "review-only policy/action diagnostics; no broker/order/paper/live",
            "status": "GOVERNANCE_PRESENT_BUT_CURRENT_PIPELINE_NOT_MATERIALIZED",
            "evidence": f"L5 hardening checks={l5_check_rows}, current L4-to-L5 builder exists={int(l5_current_builder_exists)}",
            "blocker_or_gap": "no current L5 materializer from latest L4; actual policy/action artifact schema validation remains future work",
            "next_action": "build only after L0-L4 refresh proof; keep no-order/no-paper/no-live gates closed",
        },
    ]

    risks = [
        {
            "priority": "P0",
            "risk": "L0 newswire is still incomplete, so downstream layers cannot claim full source coverage.",
            "evidence": f"pending={safe_get(l0, 'public_newswire', 'pending_units')}, partial={safe_get(l0, 'public_newswire', 'partial_units')}, progress={safe_get(l0, 'public_newswire', 'progress_pct')}",
            "fix": "Keep 4195 continuous guard running and require terminal complete/blocker proof.",
        },
        {
            "priority": "P0",
            "risk": "L1/L2/L3/L4 outputs are mostly task snapshots, not proven continuously refreshed after each new L0 batch.",
            "evidence": "L1/L2 latest summaries are from task_4186/task_4147; L4 manifest created from earlier L0 collection status.",
            "fix": "Add refresh watermark proof that says which L0 batch each layer consumed.",
        },
        {
            "priority": "P1",
            "risk": "L4 still has large blocker families and cannot be final thesis judgment.",
            "evidence": f"L4 blocker rows={l4_blocker_rows}; scanner not_scanned={l4_scanner.get('not_scanned_rows')}; unsupported_relation_reference={l4_scanner.get('unsupported_relation_count_reference')}",
            "fix": "Burn down only high-impact unsupported relation families; keep catch-all forbidden.",
        },
        {
            "priority": "P1",
            "risk": "L5 is not currently wired to latest L4 outputs.",
            "evidence": f"current L4-to-L5 builder exists={int(l5_current_builder_exists)}",
            "fix": "After L0-L4 refresh proof, add review-only L5 materializer and schema validator.",
        },
        {
            "priority": "P2",
            "risk": "Stale worker history can be misread as current worker failure.",
            "evidence": "; ".join(l0.get("warnings") or []),
            "fix": "Separate historical recycle ledger from active worker health in reports.",
        },
    ]

    safety = {
        "strategy": "NOT_ACCEPTED",
        "deployment": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "broker_mutation": 0,
        "live_order": 0,
        "paper_promotion": 0,
        "missing_or_stale_data": "UNKNOWN/BLOCKER",
    }

    summary = {
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "verdict": "NOT_FULLY_COMPLETE_L0_RUNNING_L5_NOT_CURRENTLY_MATERIALIZED",
        "deleted_scheduler_proof_ok": all(row.get("deleted") for row in deleted_scheduler_proof.get("deleted_legacy_schedulers", [])),
        "deleted_entrypoint_proof_ok": all(row.get("deleted") for row in deleted_entrypoint_proof.get("deleted_legacy_entrypoints", [])),
        "layer_matrix": matrix,
        "risk_priority": risks,
        "safety": safety,
    }

    write_json(OUT / "l0_l5_integration_audit.json", summary)
    write_csv(OUT / "layer_linkage_matrix.csv", matrix)
    write_csv(OUT / "risk_priority.csv", risks)
    write_gpt_prompt(summary)
    return summary


def write_gpt_prompt(summary: dict[str, Any]) -> None:
    matrix_text = "\n".join(
        f"- {row['layer']}: status={row['status']}; evidence={row['evidence']}; gap={row['blocker_or_gap']}; next={row['next_action']}"
        for row in summary["layer_matrix"]
    )
    risks_text = "\n".join(
        f"- {row['priority']} {row['risk']} Evidence: {row['evidence']} Fix: {row['fix']}"
        for row in summary["risk_priority"]
    )
    prompt = f"""You are a professional backend engineer, data platform reliability engineer, quant data infrastructure reviewer, and professional swing trader/risk reviewer.

Do not read GitHub for this review. The local Codex workspace has uncommitted work that is not visible on GitHub. Treat the context below as the source packet to review.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence

User goal:
Verify whether the current latest Layer 0 collection setup is clean after deleting old schedulers/legacy entrypoints, then review Layer 0 through Layer 5 linkage, role implementation, missing pieces, and operational risks. Avoid overengineering and avoid code-for-code. If issues exist, propose concrete Codex-executable fixes in priority order.

Current cleanup:
- Old Windows schedulers were deleted, not disabled.
- Current schedulers are TraderBrainL0ContinuousBackfillGuard4195 every 5 minutes and TraderBrainL0L2Hardening4147 every 15 minutes.
- Legacy entrypoint scripts were deleted. configs/db_source_acquisition_scheduler.json remains only as reference config for the 4147 safe realtime config.

Layer audit:
{matrix_text}

Risk priority:
{risks_text}

Required review output:
1. PASS / CONDITIONAL PASS / FAIL on the current L0 runtime cleanup.
2. PASS / CONDITIONAL PASS / FAIL on L0-L5 linkage.
3. P0/P1/P2 issues only if they are real operational or data-chain risks.
4. Concrete implementation steps for Codex.
5. Explicitly cut any overengineering.
6. Confirm no trading authority should be opened.
"""
    (OUT / "gpt_pro_prompt.md").write_text(prompt, encoding="utf-8", newline="\n")


def main() -> int:
    summary = build()
    print(json.dumps({
        "task_id": TASK_ID,
        "verdict": summary["verdict"],
        "outputs": [
            str(OUT / "l0_l5_integration_audit.json"),
            str(OUT / "layer_linkage_matrix.csv"),
            str(OUT / "risk_priority.csv"),
            str(OUT / "gpt_pro_prompt.md"),
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
