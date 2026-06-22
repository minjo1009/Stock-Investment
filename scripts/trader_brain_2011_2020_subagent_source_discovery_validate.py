from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_2011_2020_subagent_source_discovery"
REPORT = ROOT / "docs/reports/task_2011_2020_subagent_source_discovery/task_2011_2020_subagent_source_discovery.md"
DECISION = ROOT / "docs/reports/task_2011_2020_subagent_source_discovery/task_2011_2020_decision.csv"
REGISTRY = ROOT / "tasks/task_registry.csv"
OPERATING_STATE = ROOT / "docs/operating_system/project_operating_state.md"
AUTHORITY = "DIAGNOSTIC_SUBAGENT_SOURCE_DISCOVERY_ONLY"

REQUIRED_COUNTS = {
    "task2011_subagent_source_findings.csv": 4,
    "task2012_ranked_source_options.csv": 17,
    "task2013_aggressive_symbol_source_priority.csv": 48,
    "task2014_l1_l5_source_field_contract.csv": 8,
    "task2015_2021_2026_implementation_backlog.csv": 6,
    "task2020_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


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
    fail_if(not (OUT_DIR / "task2020_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision")


def validate_findings_and_options() -> None:
    findings = read_csv(OUT_DIR / "task2011_subagent_source_findings.csv")
    families = {row["family"] for row in findings}
    expected = {"ir_ceo_press_release", "earnings_call_transcript", "contract_customer_confirmation", "policy_news_external_catalyst"}
    fail_if(families != expected, f"source families mismatch: {families}")
    by_family = {row["family"]: row for row in findings}
    fail_if("SEC 8-K" not in by_family["ir_ceo_press_release"]["ranked_primary_source"], "IR/CEO primary source not SEC 8-K")
    fail_if("Quartr" not in by_family["earnings_call_transcript"]["ranked_primary_source"], "transcript primary source not Quartr")
    fail_if("Federal Register" not in by_family["policy_news_external_catalyst"]["ranked_primary_source"], "policy primary source not Federal Register")
    options = read_csv(OUT_DIR / "task2012_ranked_source_options.csv")
    fail_if(not any(row["access_model"] == "vendor_gated" for row in options), "vendor gate not recorded")
    fail_if(not any(row["access_model"] == "free_official" for row in options), "free official options missing")
    fail_if(any(row["missing_source_is_negative"] != "0" for row in options), "missing source treated as negative")


def validate_symbol_queue_and_contract() -> None:
    symbols = read_csv(OUT_DIR / "task2013_aggressive_symbol_source_priority.csv")
    by_symbol = {row["symbol"]: row for row in symbols}
    for symbol in ["AVGO", "ANET", "AA", "CIEN", "AEIS", "CEG"]:
        fail_if(symbol not in by_symbol, f"priority symbol missing {symbol}")
    for symbol in ["ANET", "AMD", "CEG"]:
        fail_if(by_symbol[symbol]["fixture_type"] != "positive_free_source_fixture", f"{symbol} not positive fixture")
    for symbol in ["CIEN", "AVGO", "AEIS"]:
        fail_if(by_symbol[symbol]["fixture_type"] != "blocker_or_vendor_gate_fixture", f"{symbol} not blocker fixture")
    contracts = read_csv(OUT_DIR / "task2014_l1_l5_source_field_contract.csv")
    fail_if(not any(row["layer"] == "L1" for row in contracts), "L1 contract missing")
    fail_if(not any(row["layer"] == "L5" for row in contracts), "L5 contract missing")
    fail_if(any("no_current_2026_direct_assignment" not in row["forbidden_rule"] for row in contracts), "forbidden rule missing")


def validate_closeout_docs_registry() -> None:
    closeout = read_csv(OUT_DIR / "task2020_closeout.csv")[0]
    fail_if(closeout["paper_shadow_policy_status"] != "BLOCKED_UNTIL_EXTRACTORS_IMPLEMENTED_AND_GATE_RECOMPUTED", "paper gate not blocked")
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital changed")
    payload = json.loads((OUT_DIR / "task2020_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "subagent_source_discovery_complete", "json verdict mismatch")
    report = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Subagent Source Discovery",
        "SEC 8-K Exhibit 99.1",
        "Quartr is best",
        "Federal Register",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in report, f"report missing phrase {phrase}")
    registry = REGISTRY.read_text(encoding="utf-8")
    fail_if("Task2011,Subagent Source Family Findings" not in registry, "registry task2011 missing")
    fail_if("Task2020,Subagent Source Discovery Closeout" not in registry, "registry task2020 missing")
    state = OPERATING_STATE.read_text(encoding="utf-8")
    fail_if("Task2011-Task2020 completed subagent source discovery" not in state, "operating state row missing")


def main() -> None:
    try:
        validate_files_counts_authority()
        validate_findings_and_options()
        validate_symbol_queue_and_contract()
        validate_closeout_docs_registry()
    except AssertionError as exc:
        print(f"[TASK2011_2020_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK2011_2020_VALIDATE_OK] subagent source discovery artifacts are valid")


if __name__ == "__main__":
    main()
