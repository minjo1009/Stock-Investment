from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1971_1980_free_source_l0_l5_replay"
REPORT = ROOT / "docs/reports/task_1971_1980_free_source_l0_l5_replay/task_1971_1980_free_source_l0_l5_replay.md"
DECISION = ROOT / "docs/reports/task_1971_1980_free_source_l0_l5_replay/task_1971_1980_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_SOURCE_L0_L5_REPLAY_ONLY"

REQUIRED_COUNTS = {
    "task1971_input_manifest.csv": 7,
    "task1971_l0_free_source_admission.csv": 377,
    "task1972_l1_alfred_macro_vintage_panel.csv": 61,
    "task1973_l2_free_source_semantics.csv": 377,
    "task1974_l3_free_source_relation_edges.csv": 1154,
    "task1975_l4_free_source_thesis_cards.csv": 377,
    "task1976_free_source_top3_replay_trades.csv": 160,
    "task1976_free_source_top3_replay_equity.csv": 61,
    "task1976_free_source_top3_replay_metrics.csv": 1,
    "task1976_split_oos_metrics.csv": 2,
    "task1976_cost_stress_metrics.csv": 4,
    "task1977_free_source_attribution.csv": 3,
    "task1978_expert_subagent_audit.csv": 6,
    "task1980_acceptance_gate.csv": 1,
    "task1980_closeout.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing csv: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def fail_if(condition: bool, message: str) -> None:
    if condition:
        raise AssertionError(message)


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value[:10])


def validate_files_counts_authority() -> None:
    for name, expected in REQUIRED_COUNTS.items():
        fail_if(not (OUT_DIR / name).exists(), f"missing artifact: {name}")
        count = len(read_csv(OUT_DIR / name))
        fail_if(count != expected, f"{name} expected {expected} got {count}")
    fail_if(not (OUT_DIR / "artifact_manifest.csv").exists(), "missing artifact manifest")
    fail_if(not (OUT_DIR / "task1980_closeout.json").exists(), "missing closeout json")
    fail_if(not REPORT.exists(), "missing report")
    fail_if(not DECISION.exists(), "missing decision csv")
    for path in OUT_DIR.glob("*.csv"):
        if path.name == "artifact_manifest.csv":
            continue
        for idx, row in enumerate(read_csv(path), start=2):
            if "authority" in row:
                fail_if(row["authority"] != AUTHORITY, f"{path.name}:{idx} authority mismatch")
            if "assignment_uses_future_outcome" in row:
                fail_if(row["assignment_uses_future_outcome"] != "0", f"{path.name}:{idx} future outcome assignment")
            if "outcome_used_for_assignment" in row:
                fail_if(row["outcome_used_for_assignment"] != "0", f"{path.name}:{idx} outcome assignment")


def validate_source_gates() -> None:
    macro = read_csv(OUT_DIR / "task1972_l1_alfred_macro_vintage_panel.csv")
    fail_if(not any(row["macro_assignment_permission"] == "active_small_adjustment_certified_fred_only" for row in macro), "no active certified macro rows")
    for idx, row in enumerate(macro, start=2):
        decision = parse_date(row["decision_asof_ts"])
        fail_if(decision is None, f"missing decision date at macro row {idx}")
        for series in ["DGS2", "DGS10", "DFF", "VIXCLS", "BAMLH0A0HYM2"]:
            obs = row.get(f"{series}_observation_date", "")
            if obs:
                fail_if(parse_date(obs) > decision, f"{series} observation after decision at macro row {idx}")
    l2 = read_csv(OUT_DIR / "task1973_l2_free_source_semantics.csv")
    fail_if(any(row["analyst_revision_certified"] != "0" for row in l2), "analyst revision was certified")
    fail_if(not any(row["price_crosscheck_state"] == "raw_price_sustained_acceptance" for row in l2), "price crosscheck not computed")
    l4 = read_csv(OUT_DIR / "task1975_l4_free_source_thesis_cards.csv")
    fail_if(any(to_float(row["free_source_price_adjustment"]) != 0.0 for row in l4), "Yahoo price was used in assignment score")
    fail_if(any(row["price_crosscheck_score_permission"] != "audit_only_not_assignment" for row in l4), "price permission mismatch")
    fail_if(not any(to_float(row["free_source_macro_adjustment"]) != 0.0 for row in l4), "macro adjustment never applied")
    fail_if(not any(to_float(row["free_source_guidance_adjustment"]) != 0.0 for row in l4), "guidance adjustment never applied")


def validate_replay_and_status() -> None:
    metric = read_csv(OUT_DIR / "task1976_free_source_top3_replay_metrics.csv")[0]
    fail_if(metric["policy_variant_id"] != "free_source_l0_l5_top3_v1", "unexpected policy")
    fail_if(metric["joint_target_met"] != "1", "diagnostic joint target not met")
    fail_if(to_float(metric["final_equity"]) <= to_float(metric["previous_final_equity"]), "free source replay did not improve previous diagnostic")
    fail_if(metric["strategy_acceptance"] != "NOT_ACCEPTED", "strategy status changed")
    fail_if(metric["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "deployment status changed")
    fail_if(metric["real_capital"] != "FORBIDDEN", "real capital status changed")
    trades = read_csv(OUT_DIR / "task1976_free_source_top3_replay_trades.csv")
    fail_if(any(row["outcome_used_for_assignment"] != "0" for row in trades), "trade outcome used for assignment")
    gate = read_csv(OUT_DIR / "task1980_acceptance_gate.csv")[0]
    fail_if(gate["strategy_acceptance"] != "NOT_ACCEPTED", "gate strategy changed")
    closeout = read_csv(OUT_DIR / "task1980_closeout.csv")[0]
    fail_if(closeout["real_capital"] != "FORBIDDEN", "closeout real capital changed")
    payload = json.loads((OUT_DIR / "task1980_closeout.json").read_text(encoding="utf-8"))
    fail_if(payload["verdict"] != "free_source_l0_l5_replay_complete_diagnostic_only", "json verdict mismatch")


def validate_report() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for phrase in [
        "Free Source L0-L5 Replay",
        "ALFRED/FRED vintage is active only as small adjustment",
        "SEC issuer guidance is support-only",
        "Yahoo price data is cross-check-only",
        "Strategy acceptance status: `NOT_ACCEPTED`",
        "Real capital: `FORBIDDEN`",
    ]:
        fail_if(phrase not in text, f"report missing phrase {phrase}")


def main() -> None:
    try:
        validate_files_counts_authority()
        validate_source_gates()
        validate_replay_and_status()
        validate_report()
    except AssertionError as exc:
        print(f"[TASK1971_1980_VALIDATE_ERROR] {exc}")
        sys.exit(1)
    print("[TASK1971_1980_VALIDATE_OK] free source L0-L5 replay artifacts are valid")


if __name__ == "__main__":
    main()
