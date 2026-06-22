from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
REPORT = ROOT / "docs/reports/task_1668_1687_l5_thesis_aware_action_engine/task_1668_1687_l5_thesis_aware_action_engine.md"
DECISION = ROOT / "docs/reports/task_1668_1687_l5_thesis_aware_action_engine/task_1668_1687_decision.csv"

REQUIRED = [
    "task1668_expert_review.csv",
    "task1669_drawdown_cause_panel.csv",
    "task1670_thesis_integrity_panel.csv",
    "task1671_exit_quorum_panel.csv",
    "task1672_action_revision_panel.csv",
    "task1673_thesis_aware_replay_trades.csv",
    "task1673_thesis_aware_replay_equity.csv",
    "task1673_thesis_aware_rerisk_events.csv",
    "task1674_thesis_aware_replay_metrics.csv",
    "task1675_split_oos_metrics.csv",
    "task1676_failure_attribution.csv",
    "task1686_acceptance_gate.csv",
    "task1687_closeout.csv",
    "task1687_closeout.json",
    "artifact_manifest.csv",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require_no_future_assignment(rows: list[dict[str, str]], name: str, errors: list[str]) -> None:
    for idx, row in enumerate(rows, 1):
        if row.get("assignment_uses_future_outcome", "0") != "0":
            errors.append(f"{name} row {idx} uses future outcome for assignment")
            return
        if row.get("outcome_used_for_assignment", "0") != "0":
            errors.append(f"{name} row {idx} uses outcome for assignment")
            return


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        if not (OUT_DIR / name).exists():
            errors.append(f"missing artifact: {name}")
    if not REPORT.exists():
        errors.append(f"missing report: {REPORT}")
    if not DECISION.exists():
        errors.append(f"missing decision: {DECISION}")
    if errors:
        for error in errors:
            print(f"[TASK1668_1687_ERROR] {error}")
        return 1

    experts = read_csv(OUT_DIR / "task1668_expert_review.csv")
    market = read_csv(OUT_DIR / "task1669_drawdown_cause_panel.csv")
    thesis = read_csv(OUT_DIR / "task1670_thesis_integrity_panel.csv")
    quorum = read_csv(OUT_DIR / "task1671_exit_quorum_panel.csv")
    revisions = read_csv(OUT_DIR / "task1672_action_revision_panel.csv")
    trades = read_csv(OUT_DIR / "task1673_thesis_aware_replay_trades.csv")
    equity = read_csv(OUT_DIR / "task1673_thesis_aware_replay_equity.csv")
    events = read_csv(OUT_DIR / "task1673_thesis_aware_rerisk_events.csv")
    metrics = read_csv(OUT_DIR / "task1674_thesis_aware_replay_metrics.csv")
    split = read_csv(OUT_DIR / "task1675_split_oos_metrics.csv")
    failures = read_csv(OUT_DIR / "task1676_failure_attribution.csv")
    gate = read_csv(OUT_DIR / "task1686_acceptance_gate.csv")
    closeout = read_csv(OUT_DIR / "task1687_closeout.csv")

    if len(experts) < 6:
        errors.append("expected at least six expert review rows")
    for label, rows, expected in [
        ("market context", market, 345),
        ("thesis integrity", thesis, 345),
        ("exit quorum", quorum, 345),
        ("action revisions", revisions, 690),
        ("replay trades", trades, 664),
        ("replay equity", equity, 240),
        ("metrics", metrics, 4),
        ("split", split, 8),
    ]:
        if len(rows) != expected:
            errors.append(f"{label} expected {expected} rows, got {len(rows)}")

    drawdown_causes = {row["drawdown_cause"] for row in market}
    for required in {"market_or_sector_linked_selloff", "idiosyncratic_breakdown", "stock_drawdown_unconfirmed"}:
        if required not in drawdown_causes:
            errors.append(f"missing drawdown cause: {required}")
    if not any(row["thesis_survives_damage"] == "1" for row in thesis):
        errors.append("no thesis-survival rows")
    if not any(row["exit_allowed"] == "1" for row in quorum):
        errors.append("no exit quorum rows")
    if not any(row["thesis_aware_reason"] == "market_linked_selloff_thesis_survives_hold" for row in revisions):
        errors.append("market-linked hold preservation did not fire")
    if not any(row["thesis_aware_reason"] == "exit_quorum_met" for row in revisions):
        errors.append("exit quorum did not fire")
    if not events:
        errors.append("expected thesis-aware rerisk event rows")
    if not failures:
        errors.append("expected failure attribution rows")
    if not any(row["policy_variant_id"] == "thesis_aware_no_rerisk_top3_v1" for row in metrics):
        errors.append("missing thesis-aware top3 metric")
    if not any(row["policy_variant_id"] == "thesis_aware_rerisk_top3_v1" for row in metrics):
        errors.append("missing thesis-aware rerisk top3 metric")
    if gate[0]["strategy_acceptance"] != "NOT_ACCEPTED":
        errors.append("gate overclaims strategy acceptance")
    if gate[0]["deployment_readiness"] != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
        errors.append("gate overclaims deployment readiness")
    if gate[0]["real_capital"] != "FORBIDDEN":
        errors.append("gate overclaims real capital")
    if gate[0]["cagr_30pct_met_by_any"] != "0":
        errors.append("gate should not claim CAGR target met")
    if closeout[0]["verdict"] != "l5_thesis_aware_action_engine_implemented_not_accepted":
        errors.append("closeout verdict mismatch")

    for name, rows in [
        ("market", market),
        ("thesis", thesis),
        ("quorum", quorum),
        ("revisions", revisions),
        ("trades", trades),
        ("metrics", metrics),
        ("events", events),
    ]:
        require_no_future_assignment(rows, name, errors)

    report_text = REPORT.read_text(encoding="utf-8")
    for required in [
        "Reduce now checks drawdown cause before cutting.",
        "Exit now requires a two-evidence quorum.",
        "Re-risk now requires thesis survival plus runtime recovery.",
        "Test results do not modify strategy acceptance status.",
    ]:
        if required not in report_text:
            errors.append(f"report missing text: {required}")

    if errors:
        for error in errors:
            print(f"[TASK1668_1687_ERROR] {error}")
        return 1
    print("[TASK1668_1687_OK] L5 thesis-aware action engine artifacts validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
