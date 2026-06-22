from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_907_916_sec_l1_l5_pipeline"

REQUIRED_FILES = [
    "task907_source_corpus_manifest.csv",
    "task908_l1_sec_companyfacts_evidence.csv",
    "task909_source_admission_audit.csv",
    "task910_source_span_panel.csv",
    "task911_l2_primitive_facts.csv",
    "task912_l2_economic_meanings.csv",
    "task913_l3_relation_snapshots.csv",
    "task914_l4_candidate_bundles.csv",
    "task915_l5_dry_decisions.csv",
    "task916_replay_gate.csv",
    "task907_916_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_PRE_REPLAY_COLUMNS = {"future_return", "realized_return", "pnl", "rank", "score", "position_size"}
ALLOWED_RELATION_PRIMITIVES = {
    "reinforces",
    "weakens",
    "invalidates",
    "conditions",
    "sequences",
    "explains",
    "contradicts",
    "source_gap_for",
    "noise_for",
    "revenue_to_profitability_context",
    "liquidity_to_obligation_context",
    "scale_to_innovation_investment_context",
    "scale_to_capital_intensity_context",
    "asset_base_to_obligation_context",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = ART / name
        if not path.exists():
            errors.append(f"missing {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty {name}")
    if errors:
        return errors

    corpus = rows(ART / "task907_source_corpus_manifest.csv")
    l1 = rows(ART / "task908_l1_sec_companyfacts_evidence.csv")
    admission = rows(ART / "task909_source_admission_audit.csv")
    spans = rows(ART / "task910_source_span_panel.csv")
    primitives = rows(ART / "task911_l2_primitive_facts.csv")
    meanings = rows(ART / "task912_l2_economic_meanings.csv")
    relations = rows(ART / "task913_l3_relation_snapshots.csv")
    candidates = rows(ART / "task914_l4_candidate_bundles.csv")
    decisions = rows(ART / "task915_l5_dry_decisions.csv")
    replay_gates = rows(ART / "task916_replay_gate.csv")
    summary = json.loads((ART / "task907_916_summary.json").read_text(encoding="utf-8"))

    if len(corpus) != 70:
        errors.append("source corpus must cover the 70-symbol theme universe")
    if not l1:
        errors.append("L1 evidence must not be empty")
    if len(admission) != len(l1):
        errors.append("admission rows must match L1 evidence rows")
    if len(spans) != len(l1):
        errors.append("source span rows must match admitted L1 evidence rows")
    if len(primitives) != len(l1):
        errors.append("primitive rows must match admitted L1 evidence rows")
    if len(meanings) != len(primitives):
        errors.append("meaning rows must match primitive rows")
    if not relations or not candidates or not decisions:
        errors.append("L3, L4, and L5 dry panels must all be non-empty")

    for row in corpus:
        if row["coverage_state"] != "raw_source_attached":
            errors.append(f"raw source missing for {row['symbol']}")
            break
        path = ROOT / row["raw_storage_path"]
        if not path.exists():
            errors.append(f"raw storage path missing for {row['symbol']}")
            break
        if sha256(path) != row["raw_source_hash"]:
            errors.append(f"raw source hash mismatch for {row['symbol']}")
            break

    for name, panel in [
        ("l1", l1),
        ("primitive", primitives),
        ("meaning", meanings),
        ("relation", relations),
        ("candidate", candidates),
        ("decision", decisions),
    ]:
        forbidden = FORBIDDEN_PRE_REPLAY_COLUMNS & set(panel[0].keys())
        if forbidden:
            errors.append(f"{name} panel contains forbidden columns: {sorted(forbidden)}")

    l1_ids = {row["evidence_id"] for row in l1}
    span_ids = {row["evidence_id"] for row in spans}
    primitive_ids = {row["primitive_fact_id"] for row in primitives}
    meaning_ids = {row["economic_meaning_id"] for row in meanings}
    relation_ids = {row["relation_snapshot_id"] for row in relations}
    candidate_ids = {row["candidate_bundle_id"] for row in candidates}

    for row in l1:
        if row["source_family"] == "internal_source_event_capture":
            errors.append("internal source event capture entered L1 positive path")
            break
        if not row["raw_source_uri"] or not row["raw_storage_path"] or not row["raw_source_hash"]:
            errors.append("L1 row missing raw source uri/path/hash")
            break
        if row["backtest_eligible_flag"] != "0" or row["outcome_used_for_assignment_flag"] != "0":
            errors.append("L1 row must not be backtest eligible or outcome assigned")
            break
        if parse_ts(row["available_to_brain_ts"]) <= parse_ts(row["published_ts"]):
            errors.append("available_to_brain_ts must be after published_ts for conservative source-time gate")
            break

    for row in admission:
        if row["evidence_id"] not in l1_ids:
            errors.append("admission evidence id missing from L1")
            break
        if row["can_enter_l2"] != "1" or row["admission_state"] != "admitted_to_l2":
            errors.append("all current Task907-916 L1 rows must be admitted to L2")
            break

    for row in spans:
        if row["evidence_id"] not in l1_ids:
            errors.append("span evidence id missing from L1")
            break
        if not row["source_span_ref"] or not row["source_span_excerpt"] or not row["reproducibility_hash"]:
            errors.append("span row missing hash/excerpt/reproducibility")
            break

    for row in primitives:
        if row["evidence_id"] not in l1_ids or row["evidence_id"] not in span_ids:
            errors.append("primitive evidence id missing from L1 or span panel")
            break
        if row["acceptance_state"] != "accepted_source_backed":
            errors.append("primitive must be accepted_source_backed")
            break

    for row in meanings:
        if row["primitive_fact_id"] not in primitive_ids:
            errors.append("meaning primitive FK missing")
            break
        if row["meaning_authority"] != "research_only_sec_companyfacts":
            errors.append("meaning authority must remain research-only SEC companyfacts")
            break

    for row in relations:
        if parse_ts(row["edge_asof_ts"]) > parse_ts(row["decision_asof_ts"]):
            errors.append("relation edge_asof exceeds decision_asof")
            break
        ids = [value for value in row["source_meaning_ids"].split(";") if value]
        if any(value not in meaning_ids for value in ids):
            errors.append("relation source meaning FK missing")
            break
        edges = [value for value in row["relation_edges"].split(";") if value]
        if any(value not in ALLOWED_RELATION_PRIMITIVES for value in edges):
            errors.append("relation contains unexpected primitive")
            break

    for row in candidates:
        if row["relation_snapshot_id"] not in relation_ids:
            errors.append("candidate relation FK missing")
            break
        if row["adapter_eligible"] != "0":
            errors.append("candidate must not be adapter eligible")
            break
        if not row["weakest_layer"] or not row["unresolved_source_gaps"]:
            errors.append("candidate must expose weakest layer and unresolved gaps")
            break

    for row in decisions:
        if row["candidate_bundle_id"] not in candidate_ids:
            errors.append("decision candidate FK missing")
            break
        if row["trade_spec_allowed"] != "0" or row["diagnostic_replay_allowed"] != "0":
            errors.append("L5 dry decision must not permit trade spec or replay")
            break

    gate_status = {row["gate"]: row["status"] for row in replay_gates}
    if gate_status.get("l5_trade_spec_allowed") != "no_go":
        errors.append("replay gate must remain no_go")

    expected_counts = {
        "universe_symbols": len(corpus),
        "l1_evidence_rows": len(l1),
        "l2_admitted_rows": len(admission),
        "source_span_rows": len(spans),
        "primitive_fact_rows": len(primitives),
        "economic_meaning_rows": len(meanings),
        "relation_snapshot_rows": len(relations),
        "candidate_bundle_rows": len(candidates),
        "dry_decision_rows": len(decisions),
    }
    for key, expected in expected_counts.items():
        if summary.get(key) != expected:
            errors.append(f"summary {key} mismatch")
            break
    if summary.get("diagnostic_replay_status") != "not_run_l5_trade_spec_no_go":
        errors.append("summary replay status must remain not_run_l5_trade_spec_no_go")
    if summary.get("strategy_acceptance") != "NOT_ACCEPTED":
        errors.append("strategy acceptance must remain NOT_ACCEPTED")
    if summary.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("deployment readiness must remain diagnostic-only")
    if summary.get("real_capital") != "FORBIDDEN":
        errors.append("real capital must remain FORBIDDEN")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_907_916_SEC_L1_L5_ERROR] {error}")
        sys.exit(1)
    print("[TRADER_BRAIN_907_916_SEC_L1_L5_OK] artifacts validated")


if __name__ == "__main__":
    main()
