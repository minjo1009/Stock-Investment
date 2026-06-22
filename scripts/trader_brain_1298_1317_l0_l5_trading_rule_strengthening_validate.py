from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1298_1317_l0_l5_trading_rule_strengthening"
REPORT = ROOT / "docs/reports/task_1298_1317_l0_l5_trading_rule_strengthening/task_1298_1317_l0_l5_trading_rule_strengthening.md"
AUTHORITY = "DIAGNOSTIC_L0_L5_TRADING_RULE_STRENGTHENING_ONLY"

REQUIRED_FILES = {
    "task1298_expert_source_context.csv": 8,
    "task1299_l0_l5_strengthening_plan.csv": 20,
    "task1299_l0_l5_layer_rulebook.csv": 10,
    "task1300_l0_coverage_gate.csv": 310,
    "task1301_l1_signal_quality_scores.csv": 310,
    "task1302_l2_trading_judgment_scores.csv": 310,
    "task1303_l3_rule_action_edges.csv": 1860,
    "task1304_l4_rank_route_panel.csv": 310,
    "task1305_l5_rule_policy_specs.csv": 1240,
    "task1306_replay_trades.csv": 1240,
    "task1307_replay_equity.csv": 248,
    "task1308_replay_metrics.csv": 4,
    "task1309_layer_gap_ledger.csv": 5,
    "task1310_acceptance_gate.csv": 1,
    "task1316_expert_audit_findings.csv": 9,
    "task1317_closeout.csv": 1,
    "artifact_manifest.csv": 1,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_files() -> None:
    for name, expected_rows in REQUIRED_FILES.items():
        path = OUT_DIR / name
        require(path.exists(), f"missing required artifact: {name}")
        rows = read_csv(path)
        require(len(rows) >= expected_rows, f"{name} row count {len(rows)} < {expected_rows}")


def validate_no_future_assignment() -> None:
    for name in [
        "task1299_l0_l5_layer_rulebook.csv",
        "task1300_l0_coverage_gate.csv",
        "task1301_l1_signal_quality_scores.csv",
        "task1302_l2_trading_judgment_scores.csv",
        "task1303_l3_rule_action_edges.csv",
        "task1304_l4_rank_route_panel.csv",
        "task1305_l5_rule_policy_specs.csv",
        "task1306_replay_trades.csv",
    ]:
        rows = read_csv(OUT_DIR / name)
        for row in rows:
            if "assignment_uses_future_outcome" in row:
                require(row["assignment_uses_future_outcome"] == "0", f"future assignment flag in {name}")
            require(row.get("authority") == AUTHORITY, f"bad authority in {name}")


def validate_metrics_and_gate() -> None:
    metrics = read_csv(OUT_DIR / "task1308_replay_metrics.csv")
    policies = {row["policy_variant_id"] for row in metrics}
    require(
        policies
        == {
            "l0_l5_shadow_slot5_v1",
            "l0_l5_conviction_tilt_slot5_v1",
            "l0_l5_quality_hurdle_slot5_v1",
            "l0_l5_trader_rulebook_slot5_v1",
        },
        "unexpected policy set",
    )
    for row in metrics:
        require(row["strategy_acceptance"] == "NOT_ACCEPTED", "metrics changed strategy acceptance")
        require(row["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "metrics changed deployment readiness")
        require(row["real_capital"] == "FORBIDDEN", "metrics changed real-capital status")
        require(float(row["final_equity"]) > 0.0, "non-positive final equity")
    gate = read_csv(OUT_DIR / "task1310_acceptance_gate.csv")[0]
    require(gate["strategy_acceptance"] == "NOT_ACCEPTED", "gate changed strategy acceptance")
    require(gate["deployment_readiness"] == "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", "gate changed deployment readiness")
    require(gate["real_capital"] == "FORBIDDEN", "gate changed real-capital status")
    require(gate["decision"] == "diagnostic_only_not_accepted", "gate overclaimed acceptance")


def validate_report_footer() -> None:
    text = REPORT.read_text(encoding="utf-8")
    require("Test results do not modify strategy acceptance status." in text, "missing test authority footer")
    require("Strategy: NOT_ACCEPTED" in text, "missing strategy footer")
    require("Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY" in text, "missing deployment footer")
    require("Real Capital: FORBIDDEN" in text, "missing real-capital footer")


def main() -> None:
    validate_files()
    validate_no_future_assignment()
    validate_metrics_and_gate()
    validate_report_footer()
    print("[PASS] Task1298-1317 L0-L5 trading rule strengthening validation")


if __name__ == "__main__":
    main()
