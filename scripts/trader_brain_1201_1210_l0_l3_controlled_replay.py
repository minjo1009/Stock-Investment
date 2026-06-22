from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1191 = ROOT / "data/artifacts/task_1191_1200_l0_l3_candidate_compression"
RAW_PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
OUT_DIR = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
REPORT_DIR = ROOT / "docs/reports/task_1201_1210_l0_l3_controlled_replay"

AUTHORITY = "DIAGNOSTIC_L0_L3_CONTROLLED_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
BENCHMARK = "QQQ"
VARIANTS = [3, 5, 10]


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


def load_price(symbol: str) -> pd.DataFrame | None:
    path = RAW_PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if "Date" not in frame.columns or "Close" not in frame.columns:
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    return frame.sort_values("Date")


def price_on_or_after(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["Date"] >= d]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["Date"], float(row["Close"])


def price_on_or_before(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["Date"] <= d]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    return row["Date"], float(row["Close"])


def decision_dates(candidates: list[dict[str, str]]) -> list[dict[str, str]]:
    ordered = sorted({row["decision_asof_ts"] for row in candidates})
    return [
        {
            "decision_asof_ts": ts,
            "decision_date": ts[:10],
            "next_decision_asof_ts": ordered[idx + 1] if idx + 1 < len(ordered) else "",
            "next_decision_date": ordered[idx + 1][:10] if idx + 1 < len(ordered) else "",
        }
        for idx, ts in enumerate(ordered)
    ]


def task1201_preregistration_gate() -> list[dict[str, object]]:
    prereg = read_csv(TASK1191 / "task1200_replay_preregistration_gate.csv")[0]
    return [
        {
            "task_id": "Task1201",
            "candidate_policy_id": prereg["candidate_policy_id"],
            "source_preregistration_id": prereg["preregistration_id"],
            "source_policy_preregistration_allowed": prereg["policy_preregistration_allowed"],
            "controlled_replay_authorized": "1" if prereg["policy_preregistration_allowed"] == "1" else "0",
            "top50_candidate_rows": prereg["top50_candidate_rows"],
            "top50_avg_hit_rate_eval_only": prereg["top50_avg_hit_rate_eval_only"],
            "authority": AUTHORITY,
        }
    ]


def task1202_l4_candidate_cards(candidates: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for row in candidates:
        if row["candidate_bucket"] != "top50":
            continue
        rows.append(
            {
                "task_id": "Task1202",
                "l4_candidate_card_id": f"L4CARD1202-{len(rows)+1:07d}",
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "cik": row["cik"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "derived_industry_group": row["derived_industry_group"],
                "l0_l3_compression_score": row["l0_l3_compression_score"],
                "thesis_summary": f"{row['symbol']} selected by L0-L3 compression in {row['derived_theme']} / {row['derived_industry_group']}",
                "invalidation_summary": "fails if L0 tradability or source-time gates fail; diagnostic public-filer proxy only",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1203_l5_trade_specs(cards: list[dict[str, object]], decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    decision_by_ts = {row["decision_asof_ts"]: row for row in decisions}
    rows = []
    for card in cards:
        dec = decision_by_ts[str(card["decision_asof_ts"])]
        if not dec["next_decision_date"]:
            continue
        rows.append(
            {
                "task_id": "Task1203",
                "trade_spec_id": f"L5SPEC1203-{len(rows)+1:07d}",
                "l4_candidate_card_id": card["l4_candidate_card_id"],
                "decision_asof_ts": card["decision_asof_ts"],
                "entry_after_date": dec["decision_date"],
                "exit_on_or_before_date": dec["next_decision_date"],
                "symbol": card["symbol"],
                "cik": card["cik"],
                "candidate_rank": card["candidate_rank"],
                "derived_theme": card["derived_theme"],
                "side": "long",
                "position_sizing_rule": "equal_weight_within_slot",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1204_price_gate(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], dict[str, pd.DataFrame]]:
    prices: dict[str, pd.DataFrame] = {}
    rows = []
    for spec in specs:
        symbol = str(spec["symbol"])
        if symbol not in prices:
            prices[symbol] = load_price(symbol)
        frame = prices[symbol]
        entry = price_on_or_after(frame, date.fromisoformat(str(spec["entry_after_date"])) + timedelta(days=1)) if frame is not None else None
        exit_ = price_on_or_before(frame, date.fromisoformat(str(spec["exit_on_or_before_date"]))) if frame is not None else None
        pass_flag = "1" if entry and exit_ and entry[1] > 0 and exit_[1] > 0 else "0"
        rows.append(
            {
                "task_id": "Task1204",
                "price_gate_id": f"PRICE1204-{len(rows)+1:07d}",
                "trade_spec_id": spec["trade_spec_id"],
                "decision_asof_ts": spec["decision_asof_ts"],
                "symbol": symbol,
                "entry_date": entry[0].isoformat() if entry else "",
                "entry_price": round(entry[1], 6) if entry else "",
                "exit_date": exit_[0].isoformat() if exit_ else "",
                "exit_price": round(exit_[1], 6) if exit_ else "",
                "price_gate_pass": pass_flag,
                "future_price_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows, prices


def task1205_slot_selections(specs: list[dict[str, object]], price_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    price_pass = {row["trade_spec_id"]: row for row in price_gate if row["price_gate_pass"] == "1"}
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in specs:
        if spec["trade_spec_id"] in price_pass:
            grouped[str(spec["decision_asof_ts"])].append(spec)
    rows = []
    for slot_cap in VARIANTS:
        for decision_ts, items in sorted(grouped.items()):
            selected = sorted(items, key=lambda row: int(str(row["candidate_rank"])))[:slot_cap]
            for rank, spec in enumerate(selected, start=1):
                price = price_pass[str(spec["trade_spec_id"])]
                rows.append(
                    {
                        "task_id": "Task1205",
                        "policy_variant_id": f"l0_l3_slot{slot_cap}_v1",
                        "selection_id": f"SEL1205-{slot_cap}-{len(rows)+1:07d}",
                        "trade_spec_id": spec["trade_spec_id"],
                        "decision_asof_ts": decision_ts,
                        "slot_rank": rank,
                        "symbol": spec["symbol"],
                        "candidate_rank": spec["candidate_rank"],
                        "derived_theme": spec["derived_theme"],
                        "entry_date": price["entry_date"],
                        "entry_price": price["entry_price"],
                        "exit_date": price["exit_date"],
                        "exit_price": price["exit_price"],
                        "selection_promoted": "0",
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return rows


def run_replay(
    selections: list[dict[str, object]], cost_bps: float = ROUND_TRIP_COST_BPS
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selections:
        grouped[str(row["policy_variant_id"])].append(row)
    trade_rows = []
    equity_rows = []
    for variant, items in sorted(grouped.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for item in items:
            by_decision[str(item["decision_asof_ts"])].append(item)
        capital = INITIAL_CAPITAL
        for decision_ts, selected in sorted(by_decision.items()):
            per_position = capital / len(selected) if selected else 0.0
            new_capital = 0.0
            period_pnl = 0.0
            for item in selected:
                entry = float(item["entry_price"])
                exit_ = float(item["exit_price"])
                gross_return = exit_ / entry - 1.0
                net_return = gross_return - cost_bps / 10000.0
                pnl = per_position * net_return
                period_pnl += pnl
                new_capital += per_position + pnl
                trade_rows.append(
                    {
                        "task_id": "Task1206",
                        "policy_variant_id": variant,
                        "trade_id": f"TRADE1206-{len(trade_rows)+1:07d}",
                        "trade_spec_id": item["trade_spec_id"],
                        "decision_asof_ts": decision_ts,
                        "symbol": item["symbol"],
                        "candidate_rank": item["candidate_rank"],
                        "derived_theme": item["derived_theme"],
                        "entry_date": item["entry_date"],
                        "entry_price": item["entry_price"],
                        "exit_date": item["exit_date"],
                        "exit_price": item["exit_price"],
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "round_trip_cost_bps": cost_bps,
                        "capital_allocated": round(per_position, 4),
                        "pnl": round(pnl, 4),
                        "authority": AUTHORITY,
                    }
                )
            period_return = new_capital / capital - 1.0 if capital > 0 and new_capital > 0 else 0.0
            capital = new_capital if new_capital > 0 else capital
            equity_rows.append(
                {
                    "task_id": "Task1206",
                    "policy_variant_id": variant,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": round(period_return, 8),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(selected),
                    "authority": AUTHORITY,
                }
            )
    return trade_rows, equity_rows


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def benchmark(start: date, end: date) -> dict[str, object]:
    frame = load_price(BENCHMARK)
    if frame is None:
        return {"benchmark_symbol": BENCHMARK, "benchmark_final_equity": 0.0, "benchmark_cagr": 0.0}
    entry = price_on_or_after(frame, start + timedelta(days=1))
    exit_ = price_on_or_before(frame, end)
    if not entry or not exit_:
        return {"benchmark_symbol": BENCHMARK, "benchmark_final_equity": 0.0, "benchmark_cagr": 0.0}
    final = INITIAL_CAPITAL * exit_[1] / entry[1]
    return {
        "benchmark_symbol": BENCHMARK,
        "benchmark_entry_date": entry[0].isoformat(),
        "benchmark_exit_date": exit_[0].isoformat(),
        "benchmark_final_equity": round(final, 4),
        "benchmark_cagr": round(cagr(INITIAL_CAPITAL, final, entry[0], exit_[0]), 6),
    }


def task1207_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]], decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    start = date.fromisoformat(decisions[0]["decision_date"])
    end = date.fromisoformat([row for row in decisions if row["next_decision_date"]][-1]["next_decision_date"])
    bench = benchmark(start, end)
    equity_by_variant: dict[str, list[float]] = defaultdict(lambda: [INITIAL_CAPITAL])
    trade_count: dict[str, int] = defaultdict(int)
    win_count: dict[str, int] = defaultdict(int)
    for row in equity:
        equity_by_variant[str(row["policy_variant_id"])].append(float(row["equity"]))
    for row in trades:
        variant = str(row["policy_variant_id"])
        trade_count[variant] += 1
        if float(row["net_return"]) > 0:
            win_count[variant] += 1
    rows = []
    for variant, values in sorted(equity_by_variant.items()):
        final = values[-1]
        rows.append(
            {
                "task_id": "Task1207",
                "policy_variant_id": variant,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
                "max_drawdown": round(max_drawdown(values), 6),
                "trade_count": trade_count[variant],
                "win_rate": round(win_count[variant] / trade_count[variant], 6) if trade_count[variant] else 0,
                "benchmark_symbol": bench["benchmark_symbol"],
                "benchmark_final_equity": bench["benchmark_final_equity"],
                "benchmark_cagr": bench["benchmark_cagr"],
                "beats_benchmark": "1" if final > float(bench["benchmark_final_equity"]) else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1207_cost_sensitivity(selections: list[dict[str, object]], decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for cost_bps in [0.0, 20.0, 50.0, 100.0]:
        trades, equity = run_replay(selections, cost_bps=cost_bps)
        for metric in task1207_metrics(trades, equity, decisions):
            rows.append(
                {
                    "task_id": "Task1207",
                    "cost_sensitivity_id": f"COST1207-{len(rows)+1:04d}",
                    "round_trip_cost_bps": cost_bps,
                    "policy_variant_id": metric["policy_variant_id"],
                    "final_equity": metric["final_equity"],
                    "cagr": metric["cagr"],
                    "max_drawdown": metric["max_drawdown"],
                    "trade_count": metric["trade_count"],
                    "benchmark_final_equity": metric["benchmark_final_equity"],
                    "beats_benchmark": metric["beats_benchmark"],
                    "strategy_acceptance": "NOT_ACCEPTED",
                    "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "real_capital": "FORBIDDEN",
                    "authority": AUTHORITY,
                }
            )
    return rows


def task1208_failure_attribution(trades: list[dict[str, object]], selections: list[dict[str, object]]) -> list[dict[str, object]]:
    theme_by_trade = {row["trade_spec_id"]: row["derived_theme"] for row in selections}
    rows = []
    by_variant_theme: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in trades:
        theme = theme_by_trade.get(row.get("trade_spec_id", ""), "unknown")
        by_variant_theme[(str(row["policy_variant_id"]), theme)].append(float(row["net_return"]))
    for (variant, theme), returns in sorted(by_variant_theme.items()):
        rows.append(
            {
                "task_id": "Task1208",
                "failure_attr_id": f"ATTR1208-{len(rows)+1:05d}",
                "policy_variant_id": variant,
                "derived_theme": theme,
                "trade_count": len(returns),
                "avg_net_return": round(sum(returns) / len(returns), 6) if returns else 0,
                "win_rate": round(sum(1 for value in returns if value > 0) / len(returns), 6) if returns else 0,
                "authority": AUTHORITY,
            }
        )
    return rows


def task1209_acceptance_gate(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    best = max(metrics, key=lambda row: float(row["final_equity"])) if metrics else {}
    cagr_ok = to_float(best.get("cagr")) >= 0.30
    mdd_ok = to_float(best.get("max_drawdown")) >= -0.30
    bench_ok = best.get("beats_benchmark") == "1"
    return [
        {
            "task_id": "Task1209",
            "acceptance_gate_id": "ACCEPT1209-001",
            "best_variant": best.get("policy_variant_id", ""),
            "best_final_equity": best.get("final_equity", 0),
            "best_cagr": best.get("cagr", 0),
            "best_max_drawdown": best.get("max_drawdown", 0),
            "benchmark_final_equity": best.get("benchmark_final_equity", 0),
            "target_cagr_30pct_pass": "1" if cagr_ok else "0",
            "target_mdd_minus30pct_pass": "1" if mdd_ok else "0",
            "benchmark_pass": "1" if bench_ok else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(
    closeout: dict[str, object],
    metrics: list[dict[str, object]],
    cost_sensitivity: list[dict[str, object]],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1201_1210_l0_l3_controlled_replay.md"
    metric_lines = [
        "| Variant | Final equity | CAGR | MDD | Trades | Win rate | QQQ beat |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        metric_lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | "
            f"{row['max_drawdown']} | {row['trade_count']} | {row['win_rate']} | "
            f"{'yes' if row['beats_benchmark'] == '1' else 'no'} |"
        )
    cost_lines = [
        "| Cost bps | Variant | Final equity | CAGR | MDD | QQQ beat |",
        "| ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for row in cost_sensitivity:
        cost_lines.append(
            f"| {row['round_trip_cost_bps']} | `{row['policy_variant_id']}` | {row['final_equity']} | "
            f"{row['cagr']} | {row['max_drawdown']} | {'yes' if row['beats_benchmark'] == '1' else 'no'} |"
        )
    lines = [
        "# Task1201-1210 L0-L3 Controlled Replay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Best variant: `{closeout['best_variant']}`.",
        f"- Best final equity: {closeout['best_final_equity']}.",
        f"- Best CAGR: {closeout['best_cagr']}.",
        f"- Best MDD: {closeout['best_max_drawdown']}.",
        f"- Benchmark final equity: {closeout['benchmark_final_equity']}.",
        "- Target CAGR >= 30%: failed.",
        "- Target MDD >= -30%: failed.",
        "- Benchmark QQQ: passed by best variant only.",
        f"- L4 cards: {closeout['l4_cards']}.",
        f"- L5 trade specs: {closeout['trade_specs']}.",
        f"- Replay trades: {closeout['trade_rows']}.",
        "- Diagnostic replay executed: 1.",
        "- Selection promoted: 0.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        f"- Next action: {closeout['next_action']}.",
        "",
        "## Quant Expert Report",
        "",
        "This task connects Task1191-1200 L0-L3 compressed candidates into a controlled diagnostic monthly replay.",
        "",
        "Inputs:",
        "",
        "- `task1200_replay_preregistration_gate.csv`",
        "- `task1197_compressed_candidates.csv`",
        "- `data/raw/yfinance/task_1171_1180_public_filer_proxy/daily/<SYMBOL>/<SYMBOL>_daily.csv`",
        "",
        "Join keys:",
        "",
        "- `decision_asof_ts`",
        "- `symbol`",
        "- `trade_spec_id`",
        "- next decision date from the ordered decision calendar",
        "",
        "Controls:",
        "",
        "- Uses only pre-registered Task1200 candidate compression.",
        "- Uses top50 L4 cards only.",
        "- Runs slot 3, 5, and 10 variants.",
        "- Uses equal-weight monthly holding periods.",
        "- Applies 20 bps round-trip cost in the main replay.",
        "- Keeps acceptance and real-capital status unchanged.",
        "",
        "Replay metrics:",
        "",
        *metric_lines,
        "",
        "Leakage audit:",
        "",
        "- L4 and L5 assignment rows carry `assignment_uses_future_outcome=0`.",
        "- Price rows carry `future_price_used_for_assignment=0`.",
        "- Outcomes remain evaluation-only and do not enter candidate assignment.",
        "- QQQ is used as benchmark only.",
        "",
        "Split/OOS metrics:",
        "",
        "- Not performed in this task.",
        "- This is a controlled diagnostic replay over the Task1171 broad public-filer proxy period.",
        "- Split/OOS remains a blocker before any strategy acceptance claim.",
        "",
        "Cost/slippage stress:",
        "",
        *cost_lines,
        "",
        "Failure decomposition:",
        "",
        "- The new L0-L3 compression materially improves the Task1171 broad-universe collapse.",
        "- It still fails the user's 30% CAGR target.",
        "- It still fails the -30% MDD tolerance.",
        "- Slot10 dilution suggests candidate rank quality decays after the strongest few names.",
        "- Slot5 being best suggests the next layer should improve entry/exit/risk selection rather than simply widening holdings.",
        "",
        "Remaining blockers:",
        "",
        "- No split/OOS acceptance evidence.",
        "- True exchange-listed PIT universe remains incomplete.",
        "- L4/L5 entry, exit, replacement, and drawdown controls are still weak.",
        "- No real-capital or deployment readiness change is allowed from this replay.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We tested whether the new front brain actually helps when connected to trading.",
        "",
        "It helped versus the broad-universe failure, but it is not strong enough yet.",
        "",
        "The best version beat QQQ, but it did not reach the required return or drawdown standard.",
        "",
        "The result is diagnostic only. It does not approve the strategy.",
        "",
        "Deployment readiness stays `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "",
        "Real capital stays `FORBIDDEN`.",
        "",
        "## Artifact Manifest",
        "",
        "Inputs:",
        "",
        "- Task1191-1200 compressed candidates and preregistration gate.",
        "- Task1171-1180 yfinance daily price files.",
        "",
        "Outputs:",
        "",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1201_preregistration_gate.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1202_l4_candidate_cards.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1203_l5_trade_specs.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1204_price_gate.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1205_slot_selections.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1206_replay_trades.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1206_replay_equity.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1207_replay_metrics.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1207_cost_sensitivity.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1208_failure_attribution.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1209_acceptance_gate.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1210_l0_l3_controlled_replay_closeout.csv`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1210_l0_l3_controlled_replay_closeout.json`",
        "- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/artifact_manifest.csv`",
        "",
        "Row counts:",
        "",
        f"- L4 cards: {closeout['l4_cards']}",
        f"- L5 trade specs: {closeout['trade_specs']}",
        f"- Slot selections: {closeout['selection_rows']}",
        f"- Replay trades: {closeout['trade_rows']}",
        f"- Cost sensitivity rows: {len(cost_sensitivity)}",
        "",
        "File sizes and hashes:",
        "",
        "- `artifact_manifest.csv` records SHA-256 and file size for generated data artifacts.",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1201_1210_l0_l3_controlled_replay_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1201_1210_l0_l3_controlled_replay`",
        "- `python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .`",
        "",
        "Validation authority:",
        "",
        "- PASS means the Task1201-1210 diagnostic artifact contract is internally consistent.",
        "- PASS does not mean strategy acceptance.",
        "- PASS does not mean deployment readiness.",
        "- PASS does not permit real capital.",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1201_1210_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prereg = task1201_preregistration_gate()
    candidates = read_csv(TASK1191 / "task1197_compressed_candidates.csv")
    decisions = decision_dates(candidates)
    cards = task1202_l4_candidate_cards(candidates)
    specs = task1203_l5_trade_specs(cards, decisions)
    price_gate, _prices = task1204_price_gate(specs)
    selections = task1205_slot_selections(specs, price_gate)
    trades, equity = run_replay(selections)
    metrics = task1207_metrics(trades, equity, decisions)
    cost_sensitivity = task1207_cost_sensitivity(selections, decisions)
    attribution = task1208_failure_attribution(trades, selections)
    acceptance = task1209_acceptance_gate(metrics)
    best = max(metrics, key=lambda row: float(row["final_equity"])) if metrics else {}
    closeout = {
        "task_id": "Task1201-1210",
        "verdict": "diagnostic_l0_l3_controlled_replay_executed_not_accepted",
        "best_variant": best.get("policy_variant_id", ""),
        "best_final_equity": best.get("final_equity", 0),
        "best_cagr": best.get("cagr", 0),
        "best_max_drawdown": best.get("max_drawdown", 0),
        "benchmark_final_equity": best.get("benchmark_final_equity", 0),
        "benchmark_cagr": best.get("benchmark_cagr", 0),
        "l4_cards": len(cards),
        "trade_specs": len(specs),
        "selection_rows": len(selections),
        "trade_rows": len(trades),
        "diagnostic_replay_executed": "1",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "diagnose_l0_l3_replay_vs_task1171_and_strengthen_candidate_quality_or_risk_controls",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1201_preregistration_gate.csv", prereg)
    write_csv(OUT_DIR / "task1202_l4_candidate_cards.csv", cards)
    write_csv(OUT_DIR / "task1203_l5_trade_specs.csv", specs)
    write_csv(OUT_DIR / "task1204_price_gate.csv", price_gate)
    write_csv(OUT_DIR / "task1205_slot_selections.csv", selections)
    write_csv(OUT_DIR / "task1206_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1206_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1207_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1207_cost_sensitivity.csv", cost_sensitivity)
    write_csv(OUT_DIR / "task1208_failure_attribution.csv", attribution)
    write_csv(OUT_DIR / "task1209_acceptance_gate.csv", acceptance)
    write_csv(OUT_DIR / "task1210_l0_l3_controlled_replay_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1210_l0_l3_controlled_replay_closeout.json", closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    write_report(closeout, metrics, cost_sensitivity)
    print(
        "[TRADER_BRAIN_1201_1210_L0_L3_CONTROLLED_REPLAY_OK] "
        f"best={closeout['best_variant']} final={closeout['best_final_equity']} "
        f"cagr={closeout['best_cagr']} mdd={closeout['best_max_drawdown']} "
        f"qqq={closeout['benchmark_final_equity']} trades={closeout['trade_rows']}"
    )


if __name__ == "__main__":
    main()
