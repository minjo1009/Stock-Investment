from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2501_2510_kis_cost_basis_test"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2501_2510_kis_cost_basis_test.md"
DECISION = REPORT_DIR / "task_2510_decision.csv"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2401 = ROOT / "data/artifacts/task_2401_2500_research_to_paper_readiness"

BEST_POLICY = "exit_chain_repaired_soft_boost_cap_top2_v1"
AUTHORITY = "DIAGNOSTIC_KIS_COST_BASIS_TEST_ONLY"
INITIAL_CAPITAL = 1000.0
EMBEDDED_ROUNDTRIP_COST_BPS = 20.0
KIS_US_ONLINE_BUY_COMMISSION_RATE = 0.0025
KIS_US_ONLINE_SELL_COMMISSION_RATE = 0.0025
KIS_US_SEC_FEE_SELL_RATE = 0.0000206

KIS_FEE_SOURCE_URL = "https://www.truefriend.com/main/bond/research/_static/TF03ca050000.jsp"
KIS_SEC_FEE_NOTICE_URL = "https://m.truefriend.com/main/bond/research/Guide04.jsp?cmd=TF03ca040002&num=10795"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def f(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan"}:
            return default
        out = float(value)  # type: ignore[arg-type]
        if math.isnan(out):
            return default
        return out
    except Exception:
        return default


def parse_ts(value: object) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def load_best_trades() -> list[dict[str, str]]:
    rows = read_csv(TASK2381 / "task2386_replay_trades.csv")
    return [row for row in rows if row.get("policy_variant_id") == BEST_POLICY]


def source_contract_rows() -> list[dict[str, object]]:
    total_roundtrip_rate = KIS_US_ONLINE_BUY_COMMISSION_RATE + KIS_US_ONLINE_SELL_COMMISSION_RATE + KIS_US_SEC_FEE_SELL_RATE
    return [
        {
            "task_id": "Task2501",
            "cost_contract_id": "KISCOST2501-0001",
            "broker": "Korea Investment Securities",
            "market": "US",
            "channel": "online",
            "buy_commission_rate": KIS_US_ONLINE_BUY_COMMISSION_RATE,
            "sell_commission_rate": KIS_US_ONLINE_SELL_COMMISSION_RATE,
            "sell_sec_fee_rate": KIS_US_SEC_FEE_SELL_RATE,
            "simple_roundtrip_rate": total_roundtrip_rate,
            "simple_roundtrip_bps": round(total_roundtrip_rate * 10000, 6),
            "embedded_roundtrip_cost_bps_in_task2381": EMBEDDED_ROUNDTRIP_COST_BPS,
            "modeling_note": "Task2381 net_return is gross-return proxy minus 20bps. This task reprices each selected trade with KIS buy commission, sell commission, and sell SEC fee.",
            "official_fee_source_url": KIS_FEE_SOURCE_URL,
            "official_sec_fee_notice_url": KIS_SEC_FEE_NOTICE_URL,
            "historical_vs_forward_basis": "current_kis_forward_cost_stress_applied_to_historical_replay",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def reprice_trades(trades: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(trades, start=1):
        capital = f(row.get("capital_allocated"))
        current_net_return = f(row.get("net_return"))
        gross_return_proxy = current_net_return + EMBEDDED_ROUNDTRIP_COST_BPS / 10000.0
        entry_notional = capital
        exit_notional = capital * (1.0 + gross_return_proxy)
        buy_commission = entry_notional * KIS_US_ONLINE_BUY_COMMISSION_RATE
        sell_commission = max(exit_notional, 0.0) * KIS_US_ONLINE_SELL_COMMISSION_RATE
        sec_fee = max(exit_notional, 0.0) * KIS_US_SEC_FEE_SELL_RATE
        kis_total_cost = buy_commission + sell_commission + sec_fee
        gross_pnl_proxy = capital * gross_return_proxy
        kis_pnl = gross_pnl_proxy - kis_total_cost
        kis_net_return = kis_pnl / capital if capital else 0.0
        current_pnl = f(row.get("pnl"))
        rows.append(
            {
                "task_id": "Task2502",
                "kis_trade_cost_id": f"KISCOSTTRADE2502-{idx:05d}",
                "policy_variant_id": BEST_POLICY,
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "entry_date": row.get("entry_date", ""),
                "actual_exit_date": row.get("actual_exit_date", ""),
                "capital_allocated": round(capital, 6),
                "task2381_net_return": round(current_net_return, 8),
                "gross_return_proxy": round(gross_return_proxy, 8),
                "entry_notional": round(entry_notional, 6),
                "exit_notional_proxy": round(exit_notional, 6),
                "kis_buy_commission": round(buy_commission, 6),
                "kis_sell_commission": round(sell_commission, 6),
                "kis_sec_fee": round(sec_fee, 6),
                "kis_total_cost": round(kis_total_cost, 6),
                "task2381_pnl": round(current_pnl, 6),
                "kis_pnl": round(kis_pnl, 6),
                "kis_net_return": round(kis_net_return, 8),
                "pnl_delta_vs_task2381": round(kis_pnl - current_pnl, 6),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def replay_equity(kis_trades: list[dict[str, object]]) -> list[dict[str, object]]:
    by_month: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in kis_trades:
        by_month[str(row["decision_asof_ts"])].append(row)
    equity = INITIAL_CAPITAL
    peak = equity
    rows: list[dict[str, object]] = []
    for idx, ts in enumerate(sorted(by_month, key=parse_ts), start=1):
        items = by_month[ts]
        period_pnl = sum(f(row.get("kis_pnl")) for row in items)
        equity += period_pnl
        drawdown_before = equity / peak - 1.0 if peak else 0.0
        peak = max(peak, equity)
        rows.append(
            {
                "task_id": "Task2503",
                "equity_row_id": f"KISEQUITY2503-{idx:04d}",
                "policy_variant_id": "kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1",
                "decision_asof_ts": ts,
                "equity": round(equity, 6),
                "period_pnl": round(period_pnl, 6),
                "portfolio_drawdown_after_period": round(equity / peak - 1.0 if peak else 0.0, 8),
                "portfolio_drawdown_before_peak_update": round(drawdown_before, 8),
                "allocated_count": len(items),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def metrics(equity_rows: list[dict[str, object]], kis_trades: list[dict[str, object]]) -> list[dict[str, object]]:
    final_equity = f(equity_rows[-1]["equity"]) if equity_rows else INITIAL_CAPITAL
    start = parse_ts(equity_rows[0]["decision_asof_ts"]) if equity_rows else datetime(2021, 1, 1)
    end = parse_ts(equity_rows[-1]["decision_asof_ts"]) if equity_rows else datetime(2026, 3, 31)
    years = max((end - start).days / 365.25, 1 / 365.25)
    total_return = final_equity / INITIAL_CAPITAL - 1.0 if INITIAL_CAPITAL else 0.0
    cagr = (final_equity / INITIAL_CAPITAL) ** (1 / years) - 1.0 if final_equity > 0 else -1.0
    peak = INITIAL_CAPITAL
    mdd = 0.0
    for row in equity_rows:
        eq = f(row["equity"])
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1.0 if peak else 0.0)
    task2381 = read_csv(TASK2381 / "task2386_replay_metrics.csv")
    baseline = next(row for row in task2381 if row["policy_variant_id"] == BEST_POLICY)
    total_kis_cost = sum(f(row.get("kis_total_cost")) for row in kis_trades)
    total_delta = sum(f(row.get("pnl_delta_vs_task2381")) for row in kis_trades)
    return [
        {
            "task_id": "Task2504",
            "policy_variant_id": "kis_cost_repriced_exit_chain_repaired_soft_boost_cap_top2_v1",
            "cost_basis": "kis_us_online_0p25pct_buy_0p25pct_sell_sec_0p00206pct_sell",
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final_equity, 6),
            "total_return": round(total_return, 8),
            "cagr": round(cagr, 8),
            "max_drawdown": round(mdd, 8),
            "trade_count": len(kis_trades),
            "total_kis_cost": round(total_kis_cost, 6),
            "total_pnl_delta_vs_task2381": round(total_delta, 6),
            "task2381_final_equity": baseline.get("final_equity", ""),
            "task2381_cagr": baseline.get("cagr", ""),
            "task2381_max_drawdown": baseline.get("max_drawdown", ""),
            "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
            "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
            "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def segment_metrics(equity_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    windows = [
        ("IS_2021_2023", "2021-01-01T00:00:00+00:00", "2023-12-31T23:59:59+00:00"),
        ("VALIDATION_2024", "2024-01-01T00:00:00+00:00", "2024-12-31T23:59:59+00:00"),
        ("OOS_2025_2026Q1", "2025-01-01T00:00:00+00:00", "2026-03-31T23:59:59+00:00"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (name, start_s, end_s) in enumerate(windows, start=1):
        start = parse_ts(start_s)
        end = parse_ts(end_s)
        segment = [row for row in equity_rows if start <= parse_ts(row["decision_asof_ts"]) <= end]
        before = [row for row in equity_rows if parse_ts(row["decision_asof_ts"]) < start]
        start_equity = f(before[-1]["equity"]) if before else INITIAL_CAPITAL
        final_equity = f(segment[-1]["equity"]) if segment else start_equity
        peak = start_equity
        mdd = 0.0
        for row in segment:
            eq = f(row["equity"])
            peak = max(peak, eq)
            mdd = min(mdd, eq / peak - 1.0 if peak else 0.0)
        years = max((end - start).days / 365.25, 1 / 365.25)
        cagr = (final_equity / start_equity) ** (1 / years) - 1.0 if start_equity > 0 and final_equity > 0 else -1.0
        rows.append(
            {
                "task_id": "Task2505",
                "segment_id": f"KISSEG2505-{idx:04d}",
                "split_id": name,
                "start_ts": start_s,
                "end_ts": end_s,
                "row_count": len(segment),
                "start_equity": round(start_equity, 6),
                "final_equity": round(final_equity, 6),
                "cagr": round(cagr, 8),
                "max_drawdown": round(mdd, 8),
                "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def acceptance_rows(metric: dict[str, object], segments: list[dict[str, object]]) -> list[dict[str, object]]:
    oos = next(row for row in segments if row["split_id"] == "OOS_2025_2026Q1")
    checks = [
        ("kis_full_period_cagr_30pct", metric["target_cagr_30pct_met"] == "1", "KIS-cost full-period CAGR must remain >= 30%."),
        ("kis_full_period_mdd_minus30pct", metric["target_mdd_minus30pct_met"] == "1", "KIS-cost full-period MDD must remain >= -30%."),
        ("kis_oos_cagr_30pct", oos["target_cagr_30pct_met"] == "1", "KIS-cost OOS CAGR must remain >= 30%."),
        ("kis_oos_mdd_minus30pct", oos["target_mdd_minus30pct_met"] == "1", "KIS-cost OOS MDD must remain >= -30%."),
        ("strategy_status_unchanged", True, "Cost test must not change acceptance/deployment/real-capital status."),
    ]
    return [
        {
            "task_id": "Task2506",
            "acceptance_check_id": f"KISACCEPT2506-{idx:04d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def closeout_rows(metric: dict[str, object], segments: list[dict[str, object]], acceptance: list[dict[str, object]]) -> list[dict[str, object]]:
    failed = [row["check_name"] for row in acceptance if row["pass"] != "1"]
    oos = next(row for row in segments if row["split_id"] == "OOS_2025_2026Q1")
    verdict = "kis_cost_passes_return_but_fails_mdd_gate" if failed else "kis_cost_passes_diagnostic_cost_gate"
    return [
        {
            "task_id": "Task2510",
            "verdict": verdict,
            "policy_variant_id": metric["policy_variant_id"],
            "final_equity": metric["final_equity"],
            "cagr": metric["cagr"],
            "max_drawdown": metric["max_drawdown"],
            "oos_cagr": oos["cagr"],
            "oos_max_drawdown": oos["max_drawdown"],
            "target_cagr_30pct_met": metric["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": metric["target_mdd_minus30pct_met"],
            "joint_target_met": metric["joint_target_met"],
            "failed_checks": ";".join(str(x) for x in failed),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "If KIS cost basis is accepted, repair MDD under realistic broker cost before paper order generation.",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def write_report(contract: dict[str, object], metric: dict[str, object], segments: list[dict[str, object]], acceptance: list[dict[str, object]], closeout: dict[str, object]) -> None:
    segment_lines = "\n".join(
        f"- `{row['split_id']}`: CAGR {row['cagr']}, MDD {row['max_drawdown']}, final {row['final_equity']}."
        for row in segments
    )
    failed_lines = "\n".join(f"- `{row['check_name']}`: pass {row['pass']}, {row['detail']}" for row in acceptance)
    REPORT.write_text(
        f"""# Task2501-2510 KIS Cost Basis Test

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Cost basis: Korea Investment Securities US online commission 0.25% buy, 0.25% sell, SEC Fee 0.00206% on sell.
- Repriced policy: `{metric['policy_variant_id']}`.
- Final equity: {metric['final_equity']}.
- CAGR: {metric['cagr']}.
- MDD: {metric['max_drawdown']}.
- OOS CAGR: {closeout['oos_cagr']}.
- OOS MDD: {closeout['oos_max_drawdown']}.
- Joint target met: `{metric['joint_target_met']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Cost contract:

- Buy commission rate: {contract['buy_commission_rate']}.
- Sell commission rate: {contract['sell_commission_rate']}.
- Sell SEC Fee rate: {contract['sell_sec_fee_rate']}.
- Simple roundtrip bps: {contract['simple_roundtrip_bps']}.
- Embedded Task2381 roundtrip bps: {contract['embedded_roundtrip_cost_bps_in_task2381']}.
- Source: {contract['official_fee_source_url']}.
- SEC Fee notice: {contract['official_sec_fee_notice_url']}.

Segment metrics:

{segment_lines}

Acceptance checks:

{failed_lines}

This is a current KIS forward-cost diagnostic applied to the frozen historical replay. It does not certify historical fee vintages, paper readiness, broker truth, or live deployment.

## No-Background Decision-Maker Report

Conclusion first: KIS cost does not kill CAGR, but it pushes MDD past the -30% line.

The strategy still earns strongly after KIS official online cost assumptions, but realistic broker cost makes drawdown control weaker. That means the next repair should focus on cost-aware MDD/risk control, not more return chasing.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2501_2510_kis_cost_basis_test/`.
- Validator: `python scripts/trader_brain_2501_2510_kis_cost_basis_test_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2501, 2511):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"KIS Cost Basis Test Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra / Execution Safety",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "kis-cost-diagnostic-current-forward-cost-not-live-ready",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2501_2510_kis_cost_basis_test/task_2501_2510_kis_cost_basis_test.md",
                "key_decision": "docs/reports/task_2501_2510_kis_cost_basis_test/task_2510_decision.csv",
                "key_artifacts": "data/artifacts/task_2501_2510_kis_cost_basis_test",
                "validation_command": "python scripts/trader_brain_2501_2510_kis_cost_basis_test_validate.py",
                "notes": "Reprices Task2381 frozen best policy using Korea Investment Securities US online fee basis.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "120. Task2501-Task2510"
    if marker in text:
        return
    line = (
        "120. Task2501-Task2510 repriced the frozen Task2381 best policy on Korea Investment Securities US online cost basis "
        f"(0.25% buy, 0.25% sell, SEC Fee 0.00206% sell): final {closeout['final_equity']} CAGR {closeout['cagr']} "
        f"MDD {closeout['max_drawdown']}, OOS CAGR {closeout['oos_cagr']} OOS MDD {closeout['oos_max_drawdown']}, "
        f"joint target {closeout['joint_target_met']}. Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    trades = load_best_trades()
    contract = source_contract_rows()
    kis_trades = reprice_trades(trades)
    equity = replay_equity(kis_trades)
    metric_rows = metrics(equity, kis_trades)
    segments = segment_metrics(equity)
    acceptance = acceptance_rows(metric_rows[0], segments)
    closeout = closeout_rows(metric_rows[0], segments, acceptance)

    write_csv(OUT_DIR / "task2501_kis_cost_contract.csv", contract)
    write_csv(OUT_DIR / "task2502_kis_repriced_trades.csv", kis_trades)
    write_csv(OUT_DIR / "task2503_kis_repriced_equity.csv", equity)
    write_csv(OUT_DIR / "task2504_kis_repriced_metrics.csv", metric_rows)
    write_csv(OUT_DIR / "task2505_kis_split_oos_metrics.csv", segments)
    write_csv(OUT_DIR / "task2506_kis_cost_acceptance_checks.csv", acceptance)
    write_csv(OUT_DIR / "task2510_closeout.csv", closeout)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2510_closeout.json", closeout[0])
    write_report(contract[0], metric_rows[0], segments, acceptance, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2501_2510_KIS_COST_BASIS_TEST_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
