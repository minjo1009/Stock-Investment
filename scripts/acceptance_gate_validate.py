from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_DIR = Path("docs/reports/task_603_6_acceptance_promotion_program/program_e_acceptance_gate")


def _first_row(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else {}


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip()
    if text == "":
        return default
    try:
        return float(text)
    except ValueError:
        return default


def _metric_from_rows(root: Path, candidates: list[tuple[Path, str]]) -> tuple[float | None, str]:
    for rel_path, column in candidates:
        path = root / rel_path
        row = _first_row(path)
        if column in row:
            value = _to_float(row.get(column))
            if value is not None:
                return value, rel_path.as_posix()
    return None, ""


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _db_lineage_metrics(db_path: Path) -> dict[str, float]:
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, "broker_trade_lineage"):
            return {}
        total = conn.execute("SELECT COUNT(*) FROM broker_trade_lineage").fetchone()[0]
        linked = conn.execute(
            """
            SELECT COUNT(*)
            FROM broker_trade_lineage
            WHERE broker_fill_id IS NOT NULL
              AND CAST(broker_fill_id AS TEXT) <> ''
            """
        ).fetchone()[0]
        coverage = float(linked / total) if total else 0.0
        return {
            "broker_truth_sell_fills": float(linked),
            "lineage_coverage": coverage,
            "broker_fill_linkage": coverage,
        }
    finally:
        conn.close()


def _db_snapshot_metrics(db_path: Path) -> dict[str, float]:
    if not db_path.exists():
        return {}
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, "entry_risk_snapshot") or not _table_exists(conn, "position_lifecycle"):
            return {}
        positions = conn.execute("SELECT COUNT(*) FROM position_lifecycle").fetchone()[0]
        snapshots = conn.execute("SELECT COUNT(*) FROM entry_risk_snapshot").fetchone()[0]
        stop_populated = conn.execute(
            "SELECT COUNT(*) FROM entry_risk_snapshot WHERE stop_price IS NOT NULL"
        ).fetchone()[0]
        tp_populated = conn.execute(
            "SELECT COUNT(*) FROM entry_risk_snapshot WHERE take_profit_price IS NOT NULL"
        ).fetchone()[0]
        return {
            "snapshot_coverage": float(snapshots / positions) if positions else 0.0,
            "stop_price_populated": float(stop_populated / positions) if positions else 0.0,
            "take_profit_price_populated": float(tp_populated / positions) if positions else 0.0,
        }
    finally:
        conn.close()


def collect_acceptance_gate_metrics(root: Path = ROOT, *, db_path: Path | None = None) -> dict[str, Any]:
    db = db_path or root / "trading.db"
    evidence: dict[str, str] = {}

    broker_truth_sell_fills, source = _metric_from_rows(
        root,
        [
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_a_broker_truth/broker_fill_coverage_summary.csv"
                ),
                "broker_truth_sell_fills",
            ),
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_a_broker_truth/broker_trade_lineage_summary.csv"
                ),
                "broker_truth_sell_fills",
            ),
            (
                Path("docs/reports/task_600_4_broker_truth_exit_lifecycle/broker_truth_exit_summary.csv"),
                "broker_truth_sell_fills",
            ),
        ],
    )
    if source:
        evidence["broker_truth_sell_fills"] = source

    snapshot_coverage, source = _metric_from_rows(
        root,
        [
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_b_entry_risk/entry_risk_snapshot_summary.csv"
                ),
                "snapshot_coverage",
            ),
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_b_entry_risk/stop_tp_coverage_summary.csv"
                ),
                "snapshot_coverage",
            ),
        ],
    )
    if source:
        evidence["snapshot_coverage"] = source

    position_match_rate, source = _metric_from_rows(
        root,
        [
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_c_replay_completeness/replay_completeness_summary.csv"
                ),
                "position_match_rate",
            ),
            (Path("docs/reports/task_602_4_order_replay_recovery/task_602_4_decision.csv"), "position_match_rate"),
        ],
    )
    if source:
        evidence["position_match_rate"] = source

    replay_completeness_score, source = _metric_from_rows(
        root,
        [
            (
                Path(
                    "docs/reports/task_603_6_acceptance_promotion_program/"
                    "program_c_replay_completeness/replay_completeness_summary.csv"
                ),
                "replay_completeness_score",
            ),
        ],
    )
    if source:
        evidence["replay_completeness_score"] = source

    top3_share, source = _metric_from_rows(
        root,
        [
            (Path("docs/reports/task_601_4_concentration_stability/concentration_recent_window_metrics.csv"), "top3_share"),
            (Path("docs/reports/task_601_4_concentration_stability/concentration_before_after_metrics.csv"), "top3_share_after"),
        ],
    )
    if source:
        evidence["top3_share"] = source

    lineage_metrics = _db_lineage_metrics(db)
    if broker_truth_sell_fills is None and "broker_truth_sell_fills" in lineage_metrics:
        broker_truth_sell_fills = lineage_metrics["broker_truth_sell_fills"]
        evidence["broker_truth_sell_fills"] = db.as_posix()

    snapshot_metrics = _db_snapshot_metrics(db)
    if snapshot_coverage is None and "snapshot_coverage" in snapshot_metrics:
        snapshot_coverage = snapshot_metrics["snapshot_coverage"]
        evidence["snapshot_coverage"] = db.as_posix()

    return {
        "broker_truth_sell_fills": broker_truth_sell_fills,
        "snapshot_coverage": snapshot_coverage,
        "position_match_rate": position_match_rate,
        "replay_completeness_score": replay_completeness_score,
        "top3_share": top3_share,
        "lineage_coverage": lineage_metrics.get("lineage_coverage"),
        "broker_fill_linkage": lineage_metrics.get("broker_fill_linkage"),
        "stop_price_populated": snapshot_metrics.get("stop_price_populated"),
        "take_profit_price_populated": snapshot_metrics.get("take_profit_price_populated"),
        "evidence": evidence,
    }


def evaluate_acceptance_gate(metrics: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {
            "check_id": "BROKER_TRUTH_SELL_FILLS",
            "metric": "broker_truth_sell_fills",
            "value": metrics.get("broker_truth_sell_fills"),
            "threshold": "> 0",
            "passed": (metrics.get("broker_truth_sell_fills") or 0.0) > 0.0,
            "blocker": "broker_truth_sell_fills <= 0",
        },
        {
            "check_id": "ENTRY_RISK_SNAPSHOT_COVERAGE",
            "metric": "snapshot_coverage",
            "value": metrics.get("snapshot_coverage"),
            "threshold": "> 0.95",
            "passed": (metrics.get("snapshot_coverage") or 0.0) > 0.95,
            "blocker": "snapshot_coverage <= 95%",
        },
        {
            "check_id": "POSITION_REPLAY_MATCH_RATE",
            "metric": "position_match_rate",
            "value": metrics.get("position_match_rate"),
            "threshold": "> 0.99",
            "passed": (metrics.get("position_match_rate") or 0.0) > 0.99,
            "blocker": "position_match_rate <= 99%",
        },
        {
            "check_id": "CONCENTRATION_TOP3_SHARE",
            "metric": "top3_share",
            "value": metrics.get("top3_share"),
            "threshold": "< 0.80",
            "passed": metrics.get("top3_share") is not None and float(metrics["top3_share"]) < 0.80,
            "blocker": "top3_share >= 0.80 or missing",
        },
    ]
    blockers = [check["blocker"] for check in checks if not check["passed"]]
    return {
        "status": "PASS" if not blockers else "FAIL",
        "checks": checks,
        "blockers": blockers,
    }


def _format_metric(value: Any) -> str:
    if value is None:
        return "MISSING"
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def write_acceptance_gate_outputs(
    root: Path,
    metrics: dict[str, Any],
    evaluation: dict[str, Any],
    *,
    report_dir: Path = DEFAULT_REPORT_DIR,
) -> None:
    out_dir = root / report_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "acceptance_gate_validation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_id", "metric", "value", "threshold", "status", "blocker"])
        writer.writeheader()
        for check in evaluation["checks"]:
            writer.writerow(
                {
                    "check_id": check["check_id"],
                    "metric": check["metric"],
                    "value": _format_metric(check["value"]),
                    "threshold": check["threshold"],
                    "status": "PASS" if check["passed"] else "FAIL",
                    "blocker": "" if check["passed"] else check["blocker"],
                }
            )

    with (out_dir / "acceptance_gate_blockers.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["blocker_rank", "blocker"])
        writer.writeheader()
        for idx, blocker in enumerate(evaluation["blockers"], start=1):
            writer.writerow({"blocker_rank": idx, "blocker": blocker})

    decision = {
        "task_id": "T603-6",
        "decision_status": evaluation["status"],
        "strategy_acceptance_status": "NOT_ACCEPTED",
        "deployment_readiness_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital_status": "FORBIDDEN",
        "broker_truth_sell_fills": _format_metric(metrics.get("broker_truth_sell_fills")),
        "snapshot_coverage": _format_metric(metrics.get("snapshot_coverage")),
        "position_match_rate": _format_metric(metrics.get("position_match_rate")),
        "top3_share": _format_metric(metrics.get("top3_share")),
        "blocker_count": len(evaluation["blockers"]),
    }
    with (out_dir / "task_603_6_decision.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(decision))
        writer.writeheader()
        writer.writerow(decision)

    blockers_text = "\n".join(f"- {blocker}" for blocker in evaluation["blockers"]) or "- None"
    evidence_lines = "\n".join(
        f"- {metric}: {source}" for metric, source in sorted(metrics.get("evidence", {}).items())
    ) or "- No source file found for at least one gate; validator treated missing metrics as blockers."
    report = f"""# T603-6 Program E Acceptance Gate Enforcement

## Problem
Manual promotion from `NOT_ACCEPTED` to `ACCEPTANCE_REVIEW` must be blocked unless the broker truth, entry risk snapshot, replay, and concentration gates pass.

## Evidence
- Status: {evaluation['status']}
- broker_truth_sell_fills: {_format_metric(metrics.get('broker_truth_sell_fills'))}
- snapshot_coverage: {_format_metric(metrics.get('snapshot_coverage'))}
- position_match_rate: {_format_metric(metrics.get('position_match_rate'))}
- replay_completeness_score: {_format_metric(metrics.get('replay_completeness_score'))}
- top3_share: {_format_metric(metrics.get('top3_share'))}

Evidence sources:
{evidence_lines}

## Root Cause
The validator found these active blockers:
{blockers_text}

## Fix Candidate
Resolve only the failing acceptance blockers: broker truth SELL lineage, exact entry risk snapshot coverage, replay position match above 99%, and concentration below the top3 threshold. Do not modify strategy, entry logic, universe, factors, regime filters, or alpha logic.

## Acceptance Impact
`ACCEPTANCE_REVIEW` promotion is `{evaluation['status']}`. Real capital remains `FORBIDDEN`; deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
"""
    (out_dir / "acceptance_gate_report.md").write_text(report, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    db_path = args.db_path.resolve() if args.db_path else root / "trading.db"
    metrics = collect_acceptance_gate_metrics(root, db_path=db_path)
    metrics["validated_at_utc"] = datetime.now(tz=UTC).isoformat()
    evaluation = evaluate_acceptance_gate(metrics)
    if not args.no_write:
        write_acceptance_gate_outputs(root, metrics, evaluation, report_dir=args.report_dir)

    if args.json:
        print(json.dumps({"metrics": metrics, "evaluation": evaluation}, ensure_ascii=False, indent=2))
    else:
        print(evaluation["status"])
        if evaluation["blockers"]:
            print("Blockers:")
            for blocker in evaluation["blockers"]:
                print(f"- {blocker}")
    return 0 if evaluation["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
