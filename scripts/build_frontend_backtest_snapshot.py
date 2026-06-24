from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASK_ID = "task_3903_stage1_sec_neutral_attach_same_experiment_replay"
DEFAULT_TASK_LABEL = "Task3903"
SNAPSHOT_PATH = ROOT / "data" / "frontend_snapshots" / "current_backtest_snapshot.json"
TS_FIXTURE_PATH = ROOT / "apps" / "ios-trader-brain" / "src" / "read-models" / "backtestSnapshotFixture.ts"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def f(value: Any) -> float:
    return float(value)


def build_equity_curve(equity_rows: list[dict[str, str]], initial_capital: float) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    peak = initial_capital
    for row in equity_rows:
        equity = f(row["equity"])
        peak = max(peak, equity)
        drawdown = (equity / peak) - 1.0 if peak else 0.0
        points.append(
            {
                "timestamp": row["decision_asof_ts"],
                "equity": round(equity, 6),
                "portfolioReturnPct": round(((equity / initial_capital) - 1.0) * 100.0, 6),
                "drawdownPct": round(drawdown * 100.0, 6),
            }
        )
    return points


def build_snapshot(task_id: str = DEFAULT_TASK_ID, task_label: str = DEFAULT_TASK_LABEL) -> dict[str, Any]:
    artifact_dir = ROOT / "data" / "artifacts" / task_id
    report_dir = ROOT / "docs" / "reports" / task_id
    summary_path = artifact_dir / "stage1_sec_same_experiment_replay_summary.json"
    metrics_path = artifact_dir / "stage1_sec_same_experiment_replay_metrics.csv"
    equity_path = artifact_dir / "stage1_sec_same_experiment_replay_equity.csv"
    decision_path = report_dir / "task_3903_decision.csv"
    report_path = report_dir / "stage1_sec_neutral_attach_same_experiment_replay_report.md"
    manifest_path = report_dir / "artifact_manifest.csv"

    summary = read_json(summary_path)
    metrics_rows = read_csv(metrics_path)
    decision_rows = read_csv(decision_path)
    best_policy = str(summary["best_policy_variant_id"])
    selected_metrics = next(row for row in metrics_rows if row["policy_variant_id"] == best_policy)
    equity_rows = [row for row in read_csv(equity_path) if row["policy_variant_id"] == best_policy]
    initial_capital = f(selected_metrics["initial_capital"])
    equity_curve = build_equity_curve(equity_rows, initial_capital)

    hard_state = {
        "strategyAcceptance": "NOT_ACCEPTED",
        "deploymentReadiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "realCapital": "FORBIDDEN",
        "brokerMutationPermitted": False,
        "paperPermission": False,
        "livePermission": False,
    }
    for row in [summary, selected_metrics, decision_rows[0]]:
        if row.get("strategy_acceptance") != "NOT_ACCEPTED":
            raise ValueError("strategy acceptance changed")
        if row.get("deployment_readiness") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            raise ValueError("deployment readiness changed")
        if row.get("real_capital") != "FORBIDDEN":
            raise ValueError("real capital status changed")

    chart_status = "READY" if equity_curve else "SOURCE_NOT_ATTACHED"
    return {
        "contractVersion": "frontend-backtest-snapshot-v1",
        "snapshotType": "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT",
        "authority": "NOT_AUTHORITY",
        "displayState": "DIAGNOSTIC_ONLY",
        "selectedTaskId": task_label,
        "selectedReportPath": relative(report_path),
        "currentSnapshotPath": relative(SNAPSHOT_PATH),
        "sourceArtifacts": [relative(manifest_path), relative(decision_path), relative(summary_path), relative(metrics_path), relative(equity_path)],
        "generatedAt": utc_now(),
        "governance": hard_state,
        "selectedPolicy": {
            "policyId": best_policy,
            "universeRows": int(summary["full_l5_rows"]),
            "secAttachedRows": int(summary["sec_attached_asof_rows"]),
            "neutralGapRows": int(summary["sec_neutral_gap_rows"]),
            "sameExperimentParityPass": bool(int(summary["same_experiment_parity_pass"])),
        },
        "metrics": {
            "initialCapital": initial_capital,
            "finalEquity": f(summary["best_final_equity"]),
            "totalReturnPct": f(selected_metrics["total_return"]) * 100.0,
            "cagr": f(summary["best_cagr"]),
            "maxDrawdown": f(summary["best_max_drawdown"]),
            "trades": int(summary["best_trade_count"]),
            "qqqBenchmarkFinal": f(selected_metrics["qqq_benchmark_final"]),
            "beatsQqq": selected_metrics["beats_qqq"] == "1",
        },
        "chartSource": {
            "status": chart_status,
            "reason": "Selected diagnostic equity curve is attached; QQQ point-by-point benchmark curve remains not attached."
            if chart_status == "READY"
            else "Frontend display has selected summary metrics only; equity curve and benchmark chart sources are not attached yet.",
        },
        "equityCurve": equity_curve,
        "forbiddenInterpretations": [
            "strategy acceptance",
            "deployment readiness",
            "paper permission",
            "live permission",
            "broker truth",
            "real-capital permission",
            "account valuation",
        ],
    }


def ts_literal(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)


def write_ts_fixture(snapshot: dict[str, Any]) -> None:
    text = f"""// AUTO-GENERATED by scripts/build_frontend_backtest_snapshot.py.
// READ_ONLY_SELECTED_BACKTEST_SNAPSHOT.
// NOT_AUTHORITY: not account truth, broker truth, paper truth, deployment
// readiness, strategy acceptance, or real-capital permission.

export type BacktestSnapshotReadModel = {{
  contractVersion: \"frontend-backtest-snapshot-v1\";
  snapshotType: \"READ_ONLY_SELECTED_BACKTEST_SNAPSHOT\";
  authority: \"NOT_AUTHORITY\";
  displayState: \"DIAGNOSTIC_ONLY\";
  selectedTaskId: string;
  selectedReportPath: string;
  currentSnapshotPath: string;
  sourceArtifacts: string[];
  generatedAt: string;
  governance: {{
    strategyAcceptance: \"NOT_ACCEPTED\";
    deploymentReadiness: \"DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY\";
    realCapital: \"FORBIDDEN\";
    brokerMutationPermitted: false;
    paperPermission: false;
    livePermission: false;
  }};
  selectedPolicy: {{
    policyId: string;
    universeRows: number;
    secAttachedRows: number;
    neutralGapRows: number;
    sameExperimentParityPass: boolean;
  }};
  metrics: {{
    initialCapital: number;
    finalEquity: number;
    totalReturnPct: number;
    cagr: number;
    maxDrawdown: number;
    trades: number;
    qqqBenchmarkFinal: number;
    beatsQqq: boolean;
  }};
  chartSource: {{
    status: \"READY\" | \"SOURCE_NOT_ATTACHED\";
    reason: string;
  }};
  equityCurve: Array<{{
    timestamp: string;
    equity: number;
    portfolioReturnPct: number;
    drawdownPct: number;
  }}>;
  forbiddenInterpretations: string[];
}};

export const backtestSnapshotFixture = {ts_literal(snapshot)} satisfies BacktestSnapshotReadModel;
"""
    TS_FIXTURE_PATH.write_text(text, encoding="utf-8")


def build_frontend_backtest_snapshot(task_id: str = DEFAULT_TASK_ID, task_label: str = DEFAULT_TASK_LABEL) -> dict[str, Any]:
    snapshot = build_snapshot(task_id, task_label)
    write_json(SNAPSHOT_PATH, snapshot)
    write_ts_fixture(snapshot)
    return snapshot


def main() -> None:
    snapshot = build_frontend_backtest_snapshot()
    print("[FRONTEND_BACKTEST_SNAPSHOT_BUILT]")
    print(json.dumps(snapshot, ensure_ascii=True, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
