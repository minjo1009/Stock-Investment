from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2001_2010_aggressive_policy_freeze_source_extractors"
REPORT = ROOT / "docs/reports/task_2001_2010_aggressive_policy_freeze_source_extractors/task_2001_2010_aggressive_policy_freeze_source_extractors.md"
DECISION = ROOT / "docs/reports/task_2001_2010_aggressive_policy_freeze_source_extractors/task_2001_2010_decision.csv"
REGISTRY = ROOT / "tasks/task_registry.csv"
OPERATING_STATE = ROOT / "docs/operating_system/project_operating_state.md"
AUTHORITY = "DIAGNOSTIC_POLICY_FREEZE_AND_SOURCE_EXTRACTOR_ONLY"
POLICY_ID = "winner_accel_top5_to_top2_convex_v1"

REQUIRED_COUNTS = {
    "task2001_aggressive_policy_freeze.csv": 1,
    "task2002_policy_freeze_manifest.csv": 6,
    "task2003_source_family_contract.csv": 9,
    "task2004_aggressive_source_extraction_panel.csv": 116,
    "task2005_l1_full_source_packets.csv": 116,
    "task2006_l2_full_source_semantics.csv": 116,
    "task2007_l3_full_source_edges.csv": 430,
    "task2008_l4_full_source_thesis.csv": 116,
    "task2009_l5_paper_shadow_readiness.csv": 116,
    "task2010_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def parse_ts(value: str) -> datetime | None:
    try:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_files_counts_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        rows = read_csv(OUT_DIR / name)
        fail_if(len(rows) != expected, f"{name} expected {expected} got {len(rows)}")
        for idx, row in enumerate(rows, start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{name}:{idx} outcome assignment")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task2010_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision")


def validate_policy_freeze() -> None:
    freeze = read_csv(OUT_DIR / "task2001_aggressive_policy_freeze.csv")[0]
    fail_if(freeze["policy_variant_id"] != POLICY_ID, "wrong policy frozen")
    fail_if(len(freeze["frozen_policy_spec_hash"]) != 64, "freeze hash not sha256-like")
    fail_if(freeze["select_top_n"] != "2", "aggressive policy select_top_n changed")
    fail_if(freeze["max_multiplier"] != "1.42", "aggressive policy max multiplier changed")
    fail_if(freeze["policy_change_permission"] != "blocked_without_new_task_and_new_hash", "policy mutation not blocked")
    fail_if(freeze["paper_shadow_permission"] != "blocked_until_source_extractor_gate_passes", "paper shadow not blocked")
    fail_if(freeze["real_capital_permission"] != "0", "real capital permission nonzero")
    manifest = read_csv(OUT_DIR / "task2002_policy_freeze_manifest.csv")
    fail_if(any(row["exists"] != "1" for row in manifest), "freeze dependency missing")
    fail_if(any(row["mutation_allowed"] != "0" for row in manifest), "freeze dependency mutation allowed")


def validate_source_contract_and_extractors() -> None:
    contracts = read_csv(OUT_DIR / "task2003_source_family_contract.csv")
    by_family = {row["source_family"]: row for row in contracts}
    for family in ["sec_guidance", "sec_financing_dilution", "alfred_fred_macro", "price_volume", "ir_ceo_press_release", "earnings_call_transcript", "contract_customer_confirmation", "policy_news_external_catalyst", "analyst_revision_consensus"]:
        fail_if(family not in by_family, f"missing source family {family}")
    fail_if(by_family["price_volume"]["extractor_status"] != "audit_only_attached", "price volume incorrectly promoted")
    fail_if(by_family["analyst_revision_consensus"]["extractor_status"] != "vendor_gate", "analyst gate incorrectly opened")
    fail_if(any(row["missing_source_is_negative"] != "0" for row in contracts), "missing source treated as negative")

    extracts = read_csv(OUT_DIR / "task2004_aggressive_source_extraction_panel.csv")
    fail_if(not any(row["sec_guidance_extractor_state"] == "attached_asof" for row in extracts), "SEC guidance never attached")
    fail_if(not any(row["sec_dilution_extractor_state"] not in {"source_gap", ""} for row in extracts), "SEC dilution never attached")
    fail_if(not any(row["macro_extractor_state"] == "active_small_adjustment_certified_fred_only" for row in extracts), "macro never attached")
    fail_if(not any("audit_only" in row["price_volume_extractor_state"] for row in extracts), "price audit missing")
    fail_if(any(row["analyst_revision_certified"] != "0" for row in extracts), "analyst revision incorrectly certified")
    fail_if(any(row["paper_shadow_source_gate_pass"] != "0" for row in extracts), "paper shadow gate incorrectly passed")
    for idx, row in enumerate(extracts, start=2):
        decision = parse_ts(row["decision_asof_ts"])
        for col in ["sec_guidance_available_to_brain_ts", "sec_dilution_available_to_brain_ts"]:
            ts = parse_ts(row.get(col, ""))
            if ts and decision:
                fail_if(ts > decision, f"{col} after decision at row {idx}")
        fail_if(row["current_2026_direct_input_used"] != "0", f"current source used directly at row {idx}")
        fail_if(row["inferred_matching_used"] != "0", f"inferred matching used at row {idx}")


def validate_bridge_and_gate() -> None:
    l5 = read_csv(OUT_DIR / "task2009_l5_paper_shadow_readiness.csv")
    fail_if(any(row["paper_shadow_trade_allowed"] != "0" for row in l5), "paper shadow trade allowed before full source gate")
    fail_if(any(row["real_capital_trade_allowed"] != "0" for row in l5), "real capital trade allowed")
    closeout = read_csv(OUT_DIR / "task2010_closeout.csv")[0]
    fail_if(closeout["paper_shadow_policy_status"] != "BLOCKED_UNTIL_FULL_SOURCE_EXTRACTOR_GATE", "paper status not blocked")
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital changed")
    payload = json.loads((OUT_DIR / "task2010_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "aggressive_policy_frozen_full_source_extractor_bridge_partial", "json verdict mismatch")


def validate_docs_registry() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Aggressive Policy Freeze And Source Extractors",
        "Paper shadow policy status: `BLOCKED_UNTIL_FULL_SOURCE_EXTRACTOR_GATE`",
        "Price/volume remains audit-only",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in report, f"report missing phrase {phrase}")
    registry = REGISTRY.read_text(encoding="utf-8")
    fail_if("Task2001,Aggressive Policy Freeze" not in registry, "registry task2001 missing")
    fail_if("Task2010,Freeze Extractor Closeout" not in registry, "registry task2010 missing")
    state = OPERATING_STATE.read_text(encoding="utf-8")
    fail_if("Task2001-Task2010 froze aggressive policy" not in state, "operating state row missing")


def main() -> None:
    try:
        validate_files_counts_authority()
        validate_policy_freeze()
        validate_source_contract_and_extractors()
        validate_bridge_and_gate()
        validate_docs_registry()
    except AssertionError as exc:
        print(f"[TASK2001_2010_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK2001_2010_VALIDATE_OK] aggressive policy freeze and source extractor bridge is valid")


if __name__ == "__main__":
    main()
