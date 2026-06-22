from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1834_1847_targeted_source_implementation"
REPORT = ROOT / "docs/reports/task_1834_1847_targeted_source_implementation/task_1834_1847_targeted_source_implementation.md"
DECISION = ROOT / "docs/reports/task_1834_1847_targeted_source_implementation/task_1834_1847_decision.csv"
AUTHORITY = "DIAGNOSTIC_TARGETED_SOURCE_IMPLEMENTATION_ONLY"

REQUIRED_FILES = [
    "task1834_rates_liquidity_source_contract.csv",
    "task1834_rates_source_packets.csv",
    "task1834_finra_margin_snapshot.csv",
    "task1835_rates_liquidity_observations.csv",
    "task1835_rates_liquidity_feature_panel.csv",
    "task1835_rates_liquidity_decision_asof_panel.csv",
    "task1836_sec_financing_dilution_source_packets.csv",
    "task1836_sec_companyfacts_denominator_packets.csv",
    "task1837_financing_dilution_extractor_contract.csv",
    "task1838_earnings_revision_vendor_gate.csv",
    "task1840_source_packet_schema.csv",
    "task1841_l2_targeted_meaning_contract.csv",
    "task1842_l3_targeted_edges.csv",
    "task1842_sec_dilution_decision_asof_links.csv",
    "task1843_l4_targeted_thesis_contract.csv",
    "task1844_frozen_policy_preregistration.csv",
    "task1845_controlled_replay_gate.csv",
    "task1846_validation_contract.csv",
    "task1847_closeout.csv",
    "task1847_closeout.json",
    "task1834_1847_summary.json",
    "artifact_manifest.csv",
]

FORBIDDEN_REPLAY_TOKENS = ("replay_trades", "replay_equity", "replay_metrics", "backtest")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name in REQUIRED_FILES:
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")


def validate_counts() -> None:
    summary = json.loads((OUT_DIR / "task1834_1847_summary.json").read_text(encoding="utf-8"))
    fail_if(int(summary["rates_source_packets"]) < 6, "expected at least 6 rates source packets")
    fail_if(int(summary["rates_observations"]) < 5000, "expected broad rates observations")
    fail_if(int(summary["rates_decision_rows"]) < 50, "expected monthly decision-asof rates rows")
    fail_if(int(summary["sec_packets"]) < 1000, "expected SEC financing/dilution packets")
    fail_if(int(summary["sec_denominator_packets"]) < 3000, "expected companyfacts denominator packets")
    fail_if(summary["earnings_gate_verdict"] != "vendor_blocked_schema_only", "earnings revision gate must remain vendor blocked")


def validate_authority() -> None:
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        rows = read_csv(path)
        for idx, row in enumerate(rows, start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority={row['authority']}")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome guard failed")


def validate_rates_asof() -> None:
    rows = read_csv(OUT_DIR / "task1835_rates_liquidity_decision_asof_panel.csv")
    for idx, row in enumerate(rows, start=2):
        fail_if(row["source_available_to_brain_ts"] > row["decision_asof_ts"], f"rates asof violation row {idx}")
        for field in [
            "winner_compounder_multiplier",
            "cyclical_beta_multiplier",
            "speculative_event_multiplier",
            "defensive_quality_multiplier",
        ]:
            value = float(row[field])
            fail_if(value <= 0, f"nonpositive rates multiplier row {idx} {field}")
    obs = read_csv(OUT_DIR / "task1835_rates_liquidity_observations.csv")
    for idx, row in enumerate(obs[:100], start=2):
        fail_if(row["latest_vintage_only_flag"] != "1", f"rates vintage flag missing row {idx}")
        fail_if(row["vintage_asof_certified_flag"] != "0", f"rates overclaims ALFRED vintage row {idx}")


def validate_sec_exact_and_asof() -> None:
    packets = read_csv(OUT_DIR / "task1836_sec_financing_dilution_source_packets.csv")
    for idx, row in enumerate(packets, start=2):
        fail_if(row["join_key_rule"] != "exact_cik_accession_only", f"SEC join rule violation row {idx}")
        fail_if(row["inferred_matching_used"] != "0", f"SEC inferred matching row {idx}")
        if row["source_time_pass"] == "1" and row["available_to_brain_ts"] and row["decision_asof_ts"]:
            fail_if(row["available_to_brain_ts"] > row["decision_asof_ts"], f"SEC asof violation row {idx}")
            fail_if(row["asof_guard_pass"] != "1", f"SEC asof guard flag violation row {idx}")
    links = read_csv(OUT_DIR / "task1842_sec_dilution_decision_asof_links.csv")
    for idx, row in enumerate(links, start=2):
        if row["latest_financing_source_packet_id"]:
            fail_if(row["asof_guard_pass"] != "1", f"SEC decision link asof violation row {idx}")


def validate_earnings_gate_and_no_replay() -> None:
    gate = read_csv(OUT_DIR / "task1838_earnings_revision_vendor_gate.csv")[0]
    fail_if(gate["gate_verdict"] != "vendor_blocked_schema_only", "earnings revision should be blocked")
    replay_gate = read_csv(OUT_DIR / "task1845_controlled_replay_gate.csv")[0]
    fail_if(replay_gate["gate_state"] != "blocked_no_replay_executed", "replay gate should be blocked")
    for path in OUT_DIR.iterdir():
        lower = path.name.lower()
        fail_if(any(token in lower for token in FORBIDDEN_REPLAY_TOKENS), f"unexpected replay artifact {path.name}")


def validate_report_and_status() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "No micro sizing work.",
        "No replay executed.",
        "FRED DGS10",
        "FINRA Margin Statistics",
        "SEC EDGAR APIs",
        "Nasdaq Data Link ZREV",
        "Strategy: NOT_ACCEPTED",
    ]:
        fail_if(phrase not in text, f"report missing phrase: {phrase}")
    closeout = read_csv(OUT_DIR / "task1847_closeout.csv")[0]
    fail_if(closeout["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(closeout["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(closeout["real_capital"] != "FORBIDDEN", "real capital status changed")


def main() -> None:
    try:
        validate_files()
        validate_counts()
        validate_authority()
        validate_rates_asof()
        validate_sec_exact_and_asof()
        validate_earnings_gate_and_no_replay()
        validate_report_and_status()
    except AssertionError as exc:
        print(f"[TASK1834_1847_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1834_1847_VALIDATE_OK] targeted sources are valid and replay remains blocked")


if __name__ == "__main__":
    main()
