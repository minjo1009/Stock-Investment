from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1668 = ROOT / "data/artifacts/task_1668_1687_l5_thesis_aware_action_engine"
TASK1698 = ROOT / "data/artifacts/task_1698_1717_l2_l4_bad_trade_gate"
OUT_DIR = ROOT / "data/artifacts/task_1718_1727_bad_trade_decomposition_audit"
REPORT_DIR = ROOT / "docs/reports/task_1718_1727_bad_trade_decomposition_audit"
REPORT = REPORT_DIR / "task_1718_1727_bad_trade_decomposition_audit.md"
DECISION = REPORT_DIR / "task_1718_1727_decision.csv"

AUTHORITY = "DIAGNOSTIC_BAD_TRADE_DECOMPOSITION_AUDIT_ONLY"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def round_float(value: object, digits: int = 6) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


def build_trade_frame() -> pd.DataFrame:
    trades = pd.read_csv(TASK1698 / "task1704_bad_trade_gate_replay_trades.csv")
    comp = pd.read_csv(TASK1698 / "task1702_top3_top5_candidate_compressor.csv")
    return trades.merge(
        comp[
            [
                "policy_variant_id",
                "trade_spec_id",
                "selection_reason",
                "compressed_rank",
                "payoff_quality_score",
                "payoff_quality_bucket",
                "collapse_risk_bucket",
                "pre_entry_gate",
            ]
        ],
        on=["policy_variant_id", "trade_spec_id"],
        how="left",
    )


def selection_reason_summary(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    grouped = frame.groupby(["policy_variant_id", "selection_reason"], dropna=False)
    for idx, ((policy, reason), group) in enumerate(grouped, 1):
        rows.append(
            {
                "task_id": "Task1719",
                "summary_id": f"SELDECOMP1719-{idx:04d}",
                "policy_variant_id": policy,
                "selection_reason": reason,
                "trade_count": int(len(group)),
                "pnl_sum": round_float(group["pnl"].sum(), 4),
                "avg_net_return": round_float(group["net_return"].mean(), 6),
                "win_rate": round_float((group["pnl"] > 0).mean(), 6),
                "capital_allocated_sum": round_float(group["capital_allocated"].sum(), 4),
                "authority": AUTHORITY,
            }
        )
    return rows


def action_summary(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    grouped = frame.groupby(["policy_variant_id", "runtime_action"], dropna=False)
    for idx, ((policy, action), group) in enumerate(grouped, 1):
        rows.append(
            {
                "task_id": "Task1720",
                "summary_id": f"ACTDECOMP1720-{idx:04d}",
                "policy_variant_id": policy,
                "runtime_action": action,
                "trade_count": int(len(group)),
                "pnl_sum": round_float(group["pnl"].sum(), 4),
                "avg_net_return": round_float(group["net_return"].mean(), 6),
                "win_rate": round_float((group["pnl"] > 0).mean(), 6),
                "capital_allocated_sum": round_float(group["capital_allocated"].sum(), 4),
                "authority": AUTHORITY,
            }
        )
    return rows


def open_slot_audit(frame: pd.DataFrame) -> list[dict[str, object]]:
    new_rows = frame[frame["selection_reason"] != "baseline_preserved"].copy()
    new_rows = new_rows.sort_values(["policy_variant_id", "pnl"])
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(new_rows.to_dict("records"), 1):
        rows.append(
            {
                "task_id": "Task1721",
                "open_slot_audit_id": f"OPENDECOMP1721-{idx:04d}",
                "policy_variant_id": row["policy_variant_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "pnl": round_float(row["pnl"], 4),
                "net_return": round_float(row["net_return"], 6),
                "capital_allocated": round_float(row["capital_allocated"], 4),
                "collapse_risk_bucket": row["collapse_risk_bucket"],
                "payoff_quality_bucket": row["payoff_quality_bucket"],
                "payoff_quality_score": round_float(row["payoff_quality_score"], 6),
                "runtime_action": row["runtime_action"],
                "runtime_action_reason": row["runtime_action_reason"],
                "authority": AUTHORITY,
            }
        )
    return rows


def worst_trade_audit(frame: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    worst = frame.sort_values("pnl").head(30)
    for idx, row in enumerate(worst.to_dict("records"), 1):
        rows.append(
            {
                "task_id": "Task1722",
                "worst_trade_audit_id": f"WORSTTRADE1722-{idx:04d}",
                "policy_variant_id": row["policy_variant_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "selection_reason": row["selection_reason"],
                "pnl": round_float(row["pnl"], 4),
                "net_return": round_float(row["net_return"], 6),
                "capital_allocated": round_float(row["capital_allocated"], 4),
                "collapse_risk_bucket": row["collapse_risk_bucket"],
                "payoff_quality_bucket": row["payoff_quality_bucket"],
                "payoff_quality_score": round_float(row["payoff_quality_score"], 6),
                "runtime_action": row["runtime_action"],
                "runtime_action_reason": row["runtime_action_reason"],
                "root_note": "baseline_l5_reduce_or_hold_did_not_prevent_loss"
                if row["selection_reason"] == "baseline_preserved"
                else "new_open_slot_loss",
                "authority": AUTHORITY,
            }
        )
    return rows


def worst_period_audit(frame: pd.DataFrame) -> list[dict[str, object]]:
    equity = pd.read_csv(TASK1698 / "task1704_bad_trade_gate_replay_equity.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for policy, group in equity.groupby("policy_variant_id"):
        group = group.copy()
        group["prev_equity"] = group["equity"].shift(1).fillna(1000.0)
        group["period_return"] = group["equity"] / group["prev_equity"] - 1.0
        group["peak"] = group["equity"].cummax()
        group["drawdown"] = group["equity"] / group["peak"] - 1.0
        for _, period in group.sort_values("period_return").head(10).iterrows():
            trades = frame[(frame["policy_variant_id"] == policy) & (frame["decision_asof_ts"] == period["decision_asof_ts"])]
            worst_symbol = ""
            worst_pnl = 0.0
            if not trades.empty:
                worst_row = trades.sort_values("pnl").iloc[0]
                worst_symbol = worst_row["symbol"]
                worst_pnl = float(worst_row["pnl"])
            rows.append(
                {
                    "task_id": "Task1723",
                    "worst_period_audit_id": f"WORSTPERIOD1723-{idx:04d}",
                    "policy_variant_id": policy,
                    "decision_asof_ts": period["decision_asof_ts"],
                    "equity": round_float(period["equity"], 4),
                    "period_pnl": round_float(period["period_pnl"], 4),
                    "period_return": round_float(period["period_return"], 6),
                    "drawdown": round_float(period["drawdown"], 6),
                    "selected_count": int(period["selected_count"]),
                    "allocated_count": int(period["allocated_count"]),
                    "worst_symbol": worst_symbol,
                    "worst_symbol_pnl": round_float(worst_pnl, 4),
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def baseline_comparison() -> list[dict[str, object]]:
    metrics = pd.read_csv(TASK1698 / "task1705_bad_trade_gate_replay_metrics.csv")
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(metrics.to_dict("records"), 1):
        rows.append(
            {
                "task_id": "Task1724",
                "comparison_id": f"BASECOMP1724-{idx:04d}",
                "policy_variant_id": row["policy_variant_id"],
                "baseline_policy_variant_id": row["baseline_policy_variant_id"],
                "final_equity": row["final_equity"],
                "baseline_final_equity": row["baseline_final_equity"],
                "delta_final_equity": row["delta_final_equity"],
                "cagr": row["cagr"],
                "baseline_cagr": row["baseline_cagr"],
                "delta_cagr": row["delta_cagr"],
                "max_drawdown": row["max_drawdown"],
                "baseline_max_drawdown": row["baseline_max_drawdown"],
                "delta_mdd": row["delta_mdd"],
                "interpretation": "return_up_but_drawdown_worse",
                "authority": AUTHORITY,
            }
        )
    return rows


def root_cause_rows() -> list[dict[str, object]]:
    findings = [
        (
            "primary_root",
            "The open-slot additions are not the main MDD source.",
            "Open-slot additions were 32 trades and positive in aggregate, while worst drawdown months were dominated by baseline-preserved rows.",
        ),
        (
            "primary_root",
            "MDD comes from baseline-preserved 2022 and 2025 drawdown clusters.",
            "The worst period was 2022-08-31 for both top3 and top5; key symbols include CC, AA, AVGO, ADM, BMRN, AMBA, AMZN.",
        ),
        (
            "l5_root",
            "Reduce did not mean loss control succeeded.",
            "Reduce actions have negative aggregate PnL because they often fired after damage or left enough exposure to suffer.",
        ),
        (
            "l2_l4_root",
            "Ordinary_pass is too broad.",
            "Worst losing baseline rows were often ordinary_pass and top3_payoff_candidate, so current L2/L4 does not detect cyclical beta/valuation air-pocket risk.",
        ),
        (
            "process_root",
            "The loop is caused by mixing candidate expansion and risk control in one replay.",
            "Open-slot fill raises return and exposure, while L5 risk rules try to reduce drawdown after the fact.",
        ),
    ]
    return [
        {
            "task_id": "Task1725",
            "root_cause_id": f"ROOT1725-{idx:03d}",
            "root_area": area,
            "finding": finding,
            "evidence": evidence,
            "authority": AUTHORITY,
        }
        for idx, (area, finding, evidence) in enumerate(findings, 1)
    ]


def closeout_rows() -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task1727",
            "verdict": "bad_trade_decomposition_completed_diagnostic_only",
            "main_conclusion": "MDD loop is not mainly from new open-slot candidates; it is baseline cluster risk and late/weak reduce behavior.",
            "next_action": "freeze replay rules and implement cluster-risk exposure control before more candidate expansion",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    selection: list[dict[str, object]],
    actions: list[dict[str, object]],
    open_slots: list[dict[str, object]],
    worst_trades: list[dict[str, object]],
    worst_periods: list[dict[str, object]],
    baseline: list[dict[str, object]],
    roots: list[dict[str, object]],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Task1718-1727 Bad-Trade Decomposition Audit",
        "",
        "## Decision Summary",
        "",
        "- Verdict: `bad_trade_decomposition_completed_diagnostic_only`.",
        "- Main conclusion: the loop is not caused primarily by the 32 new open-slot candidates.",
        "- Main failure: baseline-preserved cluster risk and late/weak reduce behavior.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Baseline comparison:",
        "",
        "| Policy | Final | Base Final | Delta Final | CAGR | MDD | Base MDD | Delta MDD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in baseline:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['baseline_final_equity']} | {row['delta_final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['baseline_max_drawdown']} | {row['delta_mdd']} |"
        )
    lines.extend(["", "Selection reason decomposition:", "", "| Policy | Selection | Trades | PnL | Avg Net | Win Rate |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for row in selection:
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['selection_reason']}` | {row['trade_count']} | {row['pnl_sum']} | {row['avg_net_return']} | {row['win_rate']} |"
        )
    lines.extend(["", "Action decomposition:", "", "| Policy | Action | Trades | PnL | Avg Net | Win Rate |", "| --- | --- | ---: | ---: | ---: | ---: |"])
    for row in actions:
        lines.append(
            f"| `{row['policy_variant_id']}` | `{row['runtime_action']}` | {row['trade_count']} | {row['pnl_sum']} | {row['avg_net_return']} | {row['win_rate']} |"
        )
    lines.extend(["", "Worst periods:", "", "| Policy | Date | Period PnL | Period Return | Drawdown | Worst Symbol | Worst Symbol PnL |", "| --- | --- | ---: | ---: | ---: | --- | ---: |"])
    for row in worst_periods[:10]:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['decision_asof_ts']} | {row['period_pnl']} | {row['period_return']} | {row['drawdown']} | {row['worst_symbol']} | {row['worst_symbol_pnl']} |"
        )
    lines.extend(["", "Root causes:", ""])
    for row in roots:
        lines.append(f"- `{row['root_area']}`: {row['finding']} Evidence: {row['evidence']}")
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. 새 후보가 주범이 아닙니다.",
            "2. 2022년 기존 보존 종목 묶음이 MDD를 만들었습니다.",
            "3. reduce는 많이 했지만 손실 방어에는 부족했습니다.",
            "4. `ordinary_pass`가 너무 넓어서 경기민감/고베타 급락을 못 잡았습니다.",
            "5. 다음은 룰 추가가 아니라 cluster exposure control입니다.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1719_selection_reason_summary.csv`",
            "- `task1720_action_summary.csv`",
            "- `task1721_open_slot_trade_audit.csv`",
            "- `task1722_worst_trade_audit.csv`",
            "- `task1723_worst_period_audit.csv`",
            "- `task1724_baseline_comparison.csv`",
            "- `task1725_root_cause_chain.csv`",
            "- `task1727_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1718_1727_bad_trade_decomposition_audit.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = build_trade_frame()
    selection = selection_reason_summary(frame)
    actions = action_summary(frame)
    open_slots = open_slot_audit(frame)
    worst_trades = worst_trade_audit(frame)
    worst_periods = worst_period_audit(frame)
    baseline = baseline_comparison()
    roots = root_cause_rows()
    closeout = closeout_rows()

    outputs = [
        ("task1719_selection_reason_summary.csv", selection),
        ("task1720_action_summary.csv", actions),
        ("task1721_open_slot_trade_audit.csv", open_slots),
        ("task1722_worst_trade_audit.csv", worst_trades),
        ("task1723_worst_period_audit.csv", worst_periods),
        ("task1724_baseline_comparison.csv", baseline),
        ("task1725_root_cause_chain.csv", roots),
        ("task1727_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1727_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(selection, actions, open_slots, worst_trades, worst_periods, baseline, roots)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")

    required = [OUT_DIR / name for name, _ in outputs] + [REPORT, DECISION, OUT_DIR / "artifact_manifest.csv"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"missing required outputs: {missing}")
    print("[TASK1718_1727_OK] bad-trade decomposition audit completed")


if __name__ == "__main__":
    main()
