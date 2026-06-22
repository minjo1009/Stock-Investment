from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1488 = ROOT / "data/artifacts/task_1488_1507_semantic_v6_replay"
OUT_DIR = ROOT / "data/artifacts/task_1508_1517_bottleneck_verification"
REPORT_DIR = ROOT / "docs/reports/task_1508_1517_bottleneck_verification"

AUTHORITY = "DIAGNOSTIC_BOTTLENECK_VERIFICATION_ONLY"
POLICIES = {
    "semantic_v6_top3_v1": 3,
    "semantic_v6_top5_v1": 5,
    "semantic_v6_top10_v1": 10,
}
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def rank_bucket(rank: int) -> str:
    if rank <= 3:
        return "rank_001_003"
    if rank <= 5:
        return "rank_004_005"
    if rank <= 10:
        return "rank_006_010"
    if rank <= 20:
        return "rank_011_020"
    return "rank_021_050"


def candidate_return_panel() -> list[dict[str, object]]:
    specs = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    ranks = read_csv(TASK1488 / "task1494_payoff_ranker_v6.csv")
    price_cache: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(ranks, 1):
        spec = specs[row["trade_spec_id"]]
        frame = replay.load_price(row["symbol"], price_cache)
        entry_after = replay.parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
        scheduled_exit = replay.parse_date(spec["exit_on_or_before_date"]) or entry_after
        entry = replay.price_on_or_after(frame, entry_after)
        close = replay.close_on_or_before(frame, scheduled_exit)
        if entry and close:
            gross = replay.pct_return(entry[1], close[1])
            net = gross - ROUND_TRIP_COST_BPS / 10000.0
            return_state = "return_available"
            entry_date = entry[0].isoformat()
            exit_date = close[0].isoformat()
        else:
            gross = 0.0
            net = 0.0
            return_state = "price_gap"
            entry_date = ""
            exit_date = ""
        rank = int(to_float(row["semantic_v6_rank_within_decision"], 9999))
        rows.append(
            {
                "task_id": "Task1509",
                "return_row_id": f"BOTRET1509-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "semantic_v6_rank_within_decision": rank,
                "rank_bucket": rank_bucket(rank),
                "event_family": row["event_family"],
                "expectation_v6_state": row["expectation_v6_state"],
                "absorption_v6_state": row["absorption_v6_state"],
                "materiality_v6_state": row["materiality_v6_state"],
                "entry_date": entry_date,
                "scheduled_exit_date": exit_date,
                "scheduled_gross_return": round(gross, 8),
                "scheduled_net_return": round(net, 8),
                "return_state": return_state,
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def rank_bucket_summary(return_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_bucket: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in return_rows:
        if row["return_state"] == "return_available":
            by_bucket[str(row["rank_bucket"])].append(row)
    rows: list[dict[str, object]] = []
    for idx, bucket in enumerate(["rank_001_003", "rank_004_005", "rank_006_010", "rank_011_020", "rank_021_050"], 1):
        items = by_bucket[bucket]
        returns = [to_float(row["scheduled_net_return"]) for row in items]
        rows.append(
            {
                "task_id": "Task1510",
                "rank_bucket": bucket,
                "bucket_order": idx,
                "candidate_count": len(items),
                "avg_scheduled_net_return": round(mean(returns), 8),
                "median_scheduled_net_return": round(median(returns), 8),
                "win_rate": round(mean([1.0 if value > 0 else 0.0 for value in returns]), 6),
                "loss_tail_minus20pct_count": sum(1 for value in returns if value <= -0.20),
                "gain_tail_plus20pct_count": sum(1 for value in returns if value >= 0.20),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def selected_l5_delta_panel(return_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    scheduled = {row["trade_spec_id"]: row for row in return_rows}
    trades = read_csv(TASK1488 / "task1497_replay_trades.csv")
    rows: list[dict[str, object]] = []
    for idx, trade in enumerate(trades, 1):
        sched = scheduled.get(trade["trade_spec_id"], {})
        scheduled_return = to_float(sched.get("scheduled_net_return"))
        actual_return = to_float(trade.get("net_return"))
        delta = actual_return - scheduled_return
        rows.append(
            {
                "task_id": "Task1511",
                "l5_delta_id": f"L5DELTA1511-{idx:07d}",
                "policy_variant_id": trade["policy_variant_id"],
                "trade_spec_id": trade["trade_spec_id"],
                "candidate_source_id": trade["candidate_source_id"],
                "symbol": trade["symbol"],
                "decision_asof_ts": trade["decision_asof_ts"],
                "exit_reason": trade["exit_reason"],
                "scheduled_net_return": round(scheduled_return, 8),
                "actual_net_return": round(actual_return, 8),
                "l5_exit_delta": round(delta, 8),
                "l5_helped_vs_scheduled": "1" if delta > 0 else "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def l5_delta_summary(delta_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in delta_rows:
        groups[(str(row["policy_variant_id"]), str(row["exit_reason"]))].append(row)
    rows: list[dict[str, object]] = []
    for idx, ((policy, reason), items) in enumerate(sorted(groups.items()), 1):
        deltas = [to_float(row["l5_exit_delta"]) for row in items]
        actuals = [to_float(row["actual_net_return"]) for row in items]
        scheduled = [to_float(row["scheduled_net_return"]) for row in items]
        rows.append(
            {
                "task_id": "Task1512",
                "summary_id": f"L5SUMMARY1512-{idx:04d}",
                "policy_variant_id": policy,
                "exit_reason": reason,
                "trade_count": len(items),
                "avg_scheduled_net_return": round(mean(scheduled), 8),
                "avg_actual_net_return": round(mean(actuals), 8),
                "avg_l5_exit_delta": round(mean(deltas), 8),
                "l5_help_rate": round(mean([1.0 if value > 0 else 0.0 for value in deltas]), 6),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def scheduled_only_replay(policy_specs: list[dict[str, str]], return_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scheduled = {row["trade_spec_id"]: row for row in return_rows}
    by_policy_decision: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for spec in policy_specs:
        by_policy_decision[(spec["policy_variant_id"], spec["decision_asof_ts"])].append(spec)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    for policy_id in POLICIES:
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == policy_id}):
            items = by_policy_decision[(policy_id, decision_ts)]
            per_position = capital / len(items)
            new_capital = capital
            period_pnl = 0.0
            for item in items:
                ret = to_float(scheduled.get(item["trade_spec_id"], {}).get("scheduled_net_return"))
                pnl = per_position * ret
                new_capital += pnl
                period_pnl += pnl
                trades.append(
                    {
                        "task_id": "Task1513",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": item["trade_spec_id"],
                        "candidate_source_id": item["candidate_source_id"],
                        "symbol": item["symbol"],
                        "decision_asof_ts": decision_ts,
                        "scheduled_only_net_return": round(ret, 8),
                        "pnl": round(pnl, 4),
                        "exit_reason": "scheduled_only_counterfactual",
                        "outcome_used_for_assignment": "0",
                        "outcome_used_for_audit_only": "1",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1513",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def scheduled_only_metrics(actual_metrics: list[dict[str, str]], equity: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    replay.POLICIES = POLICIES
    replay.AUTHORITY = AUTHORITY
    metrics = replay.build_metrics([], [])
    # replay.build_metrics requires actual_exit_date fields, so use a compact local metric instead.
    actual_by_policy = {row["policy_variant_id"]: row for row in actual_metrics}
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    trade_count = Counter(row["policy_variant_id"] for row in trades)
    rows: list[dict[str, object]] = []
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    for policy, eq_rows in sorted(equity_by_policy.items()):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        mdd = replay.max_drawdown(values)
        actual = actual_by_policy[policy]
        rows.append(
            {
                "task_id": "Task1513",
                "policy_variant_id": policy,
                "scheduled_only_final_equity": round(final, 4),
                "scheduled_only_total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "scheduled_only_max_drawdown": round(mdd, 6),
                "trade_count": trade_count[policy],
                "actual_final_equity": actual["final_equity"],
                "actual_max_drawdown": actual["max_drawdown"],
                "actual_minus_scheduled_final_equity": round(to_float(actual["final_equity"]) - final, 4),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def verdict_rows(bucket_summary: list[dict[str, object]], l5_summary: list[dict[str, object]], scheduled_metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    bucket = {row["rank_bucket"]: row for row in bucket_summary}
    top5_avg = (
        to_float(bucket["rank_001_003"]["avg_scheduled_net_return"]) * to_float(bucket["rank_001_003"]["candidate_count"])
        + to_float(bucket["rank_004_005"]["avg_scheduled_net_return"]) * to_float(bucket["rank_004_005"]["candidate_count"])
    ) / (to_float(bucket["rank_001_003"]["candidate_count"]) + to_float(bucket["rank_004_005"]["candidate_count"]))
    lower_avg = (
        to_float(bucket["rank_011_020"]["avg_scheduled_net_return"]) * to_float(bucket["rank_011_020"]["candidate_count"])
        + to_float(bucket["rank_021_050"]["avg_scheduled_net_return"]) * to_float(bucket["rank_021_050"]["candidate_count"])
    ) / (to_float(bucket["rank_011_020"]["candidate_count"]) + to_float(bucket["rank_021_050"]["candidate_count"]))
    top10 = next(row for row in scheduled_metrics if row["policy_variant_id"] == "semantic_v6_top10_v1")
    top5 = next(row for row in scheduled_metrics if row["policy_variant_id"] == "semantic_v6_top5_v1")
    exit_drag_rows = [row for row in l5_summary if row["exit_reason"] != "scheduled_exit"]
    exit_drag = mean([to_float(row["avg_l5_exit_delta"]) for row in exit_drag_rows])
    rank_signal = "partial_pass" if top5_avg > lower_avg else "fail"
    l5_exit = "fail" if exit_drag < 0 else "mixed_or_helpful"
    breadth = "fail" if to_float(top10["actual_minus_scheduled_final_equity"]) < 0 and to_float(top5["actual_minus_scheduled_final_equity"]) < 0 else "mixed"
    if rank_signal == "partial_pass" and l5_exit == "fail":
        bottleneck = "L5_IS_A_MAJOR_BOTTLENECK_BUT_L2L3_BREADTH_REMAINS_INCOMPLETE"
    elif rank_signal == "fail":
        bottleneck = "L2L3_RANK_QUALITY_REMAINS_PRIMARY_BOTTLENECK"
    else:
        bottleneck = "MIXED_BOTTLENECK_REQUIRES_NEXT_AUDIT"
    return [
        {
            "task_id": "Task1516",
            "check_name": "l2_l3_rank_signal",
            "verdict": rank_signal,
            "evidence": f"top5_avg_scheduled_net_return={top5_avg:.6f}; lower_rank_11_50_avg={lower_avg:.6f}",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1516",
            "check_name": "l5_exit_delta",
            "verdict": l5_exit,
            "evidence": f"non_scheduled_exit_avg_delta={exit_drag:.6f}",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1516",
            "check_name": "slot_breadth_and_holding",
            "verdict": breadth,
            "evidence": f"top5_actual_minus_scheduled={top5['actual_minus_scheduled_final_equity']}; top10_actual_minus_scheduled={top10['actual_minus_scheduled_final_equity']}",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1517",
            "check_name": "overall_bottleneck",
            "verdict": bottleneck,
            "evidence": "L2/L3 shows top-end signal, but L5 exits/holding do not control drawdown and rank breadth decays beyond top5.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        },
    ]


def write_report(
    bucket_summary: list[dict[str, object]],
    scheduled_metrics: list[dict[str, object]],
    verdict: list[dict[str, object]],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    overall = verdict[-1]
    report = f"""# Task1508-1517 Bottleneck Verification

## Decision Summary

- Verdict: `{overall['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Conclusion: L5 is a major bottleneck, but not the only bottleneck. L2/L3 has top-end signal; rank breadth still decays after the best few names.

## Quant Expert Report

Rank bucket scheduled-return audit:

| Rank bucket | Count | Avg net return | Median net return | Win rate | <= -20% | >= +20% |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in bucket_summary:
        report += (
            f"| `{row['rank_bucket']}` | {row['candidate_count']} | {row['avg_scheduled_net_return']} | "
            f"{row['median_scheduled_net_return']} | {row['win_rate']} | {row['loss_tail_minus20pct_count']} | {row['gain_tail_plus20pct_count']} |\n"
        )
    report += "\nScheduled-only versus actual L5 replay:\n\n"
    report += "| Policy | Scheduled final | Scheduled MDD | Actual final | Actual MDD | Actual minus scheduled |\n"
    report += "| --- | ---: | ---: | ---: | ---: | ---: |\n"
    for row in scheduled_metrics:
        report += (
            f"| `{row['policy_variant_id']}` | {row['scheduled_only_final_equity']} | {row['scheduled_only_max_drawdown']} | "
            f"{row['actual_final_equity']} | {row['actual_max_drawdown']} | {row['actual_minus_scheduled_final_equity']} |\n"
        )
    report += """

## No-Background Decision-Maker Report

짧게 말하면, L5가 큰 병목인 건 맞다.

하지만 L5만 문제는 아니다.

L2/L3는 상위 3~5개를 고를 때 신호가 있다.

그런데 10개까지 넓히면 잡음이 섞인다.

그리고 L5는 언제 팔지, 언제 버틸지, 몇 개를 들고 갈지 판단이 아직 약하다.

그래서 다음 작업은 L5 entry/hold/exit/replacement를 고치는 게 맞다.

단, L2/L3 rank breadth도 같이 감시해야 한다.

## Artifact Manifest

- `task1509_candidate_scheduled_return_panel.csv`
- `task1510_rank_bucket_return_summary.csv`
- `task1511_selected_l5_delta_panel.csv`
- `task1512_l5_delta_summary.csv`
- `task1513_scheduled_only_replay_trades.csv`
- `task1513_scheduled_only_replay_equity.csv`
- `task1513_scheduled_only_replay_metrics.csv`
- `task1516_bottleneck_verdict.csv`
- `task1517_closeout.json`

Validation commands:

- `python scripts/trader_brain_1508_1517_bottleneck_verification_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1508_1517_bottleneck_verification.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1508_1517_decision.csv", [overall])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return_rows = candidate_return_panel()
    bucket_summary = rank_bucket_summary(return_rows)
    delta_rows = selected_l5_delta_panel(return_rows)
    delta_summary = l5_delta_summary(delta_rows)
    policy_specs = read_csv(TASK1488 / "task1495_policy_specs.csv")
    scheduled_trades, scheduled_equity = scheduled_only_replay(policy_specs, return_rows)
    scheduled_metrics = scheduled_only_metrics(read_csv(TASK1488 / "task1497_replay_metrics.csv"), scheduled_equity, scheduled_trades)
    verdict = verdict_rows(bucket_summary, delta_summary, scheduled_metrics)
    outputs = [
        ("task1509_candidate_scheduled_return_panel.csv", return_rows),
        ("task1510_rank_bucket_return_summary.csv", bucket_summary),
        ("task1511_selected_l5_delta_panel.csv", delta_rows),
        ("task1512_l5_delta_summary.csv", delta_summary),
        ("task1513_scheduled_only_replay_trades.csv", scheduled_trades),
        ("task1513_scheduled_only_replay_equity.csv", scheduled_equity),
        ("task1513_scheduled_only_replay_metrics.csv", scheduled_metrics),
        ("task1516_bottleneck_verdict.csv", verdict),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    closeout = {
        "task_id": "Task1517",
        "verdict": verdict[-1]["verdict"],
        "candidate_return_rows": len(return_rows),
        "l5_delta_rows": len(delta_rows),
        "scheduled_only_metric_rows": len(scheduled_metrics),
        "next_action": "design L5 entry_hold_exit_replacement upgrade while monitoring L2L3 breadth decay",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    write_json(OUT_DIR / "task1517_closeout.json", closeout)
    write_report(bucket_summary, scheduled_metrics, verdict)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
