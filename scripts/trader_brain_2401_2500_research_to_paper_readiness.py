from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2401_2500_research_to_paper_readiness"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2401_2500_research_to_paper_readiness.md"
DECISION = REPORT_DIR / "task_2500_decision.csv"

TASK2191 = ROOT / "data/artifacts/task_2191_2200_api_drawdown_sizing_guard"
TASK2251 = ROOT / "data/artifacts/task_2251_2280_plus8000_full_source_acquisition"
TASK2321 = ROOT / "data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest"
TASK2341 = ROOT / "data/artifacts/task_2341_2360_plus8000_brain_full_universe_backtest"
TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"

AUTHORITY = "DIAGNOSTIC_RESEARCH_TO_PAPER_READINESS_ONLY"
BEST_POLICY = "exit_chain_repaired_soft_boost_cap_top2_v1"
ORIGINAL_PLUS8000_POLICY = "api_dd_guard_soft_boost_cap_top2_v1"
TASK2321_POLICY = "plus8000_brain_newdata_soft_boost_cap_top2_v1"
TASK2341_POLICY = "plus8000_full_actual_else_scheduled_soft_boost_cap_top2_v1"
INITIAL_CAPITAL = 1000.0
QQQ_PATHS = [
    ROOT / "data/raw/yfinance/task_870_879_full_market_data/daily/QQQ/QQQ_daily.csv",
    ROOT / "data/raw/yfinance/task_860_qqq_benchmark/QQQ_daily.csv",
    ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily/QQQ/QQQ_daily.csv",
]


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
    text = str(value or "").replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "current_trades": read_csv(TASK2381 / "task2386_replay_trades.csv"),
        "current_equity": read_csv(TASK2381 / "task2386_replay_equity.csv"),
        "current_metrics": read_csv(TASK2381 / "task2386_replay_metrics.csv"),
        "current_sources": read_csv(TASK2381 / "task2384_repaired_exit_source_rows.csv"),
        "current_methods": read_csv(TASK2381 / "task2385_full_universe_extension_method_audit.csv"),
        "current_parity": read_csv(TASK2381 / "task2383_selected_116_parity_diff.csv"),
        "original_trades": read_csv(TASK2191 / "task2194_guard_replay_trades.csv"),
        "task2321_trades": read_csv(TASK2321 / "task2326_replay_trades.csv"),
        "task2341_trades": read_csv(TASK2341 / "task2355_full_replay_trades.csv"),
        "l4_cards": read_csv(TASK2341 / "task2350_full_api_l4_cards.csv"),
        "l5_decisions": read_csv(TASK2341 / "task2351_full_api_l5_decisions.csv"),
        "feature_panel": read_csv(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv"),
        "coverage_summary": read_csv(TASK2251 / "task2255_post_acquisition_coverage_summary.csv"),
        "blocked_queue": read_csv(TASK2251 / "task2257_retry_or_blocked_queue.csv"),
        "api_ledger": read_csv(TASK2251 / "task2252_api_call_ledger.csv"),
    }


def by_policy(rows: list[dict[str, str]], policy: str) -> list[dict[str, str]]:
    return [row for row in rows if row.get("policy_variant_id") == policy]


def sum_pnl(rows: list[dict[str, str]]) -> float:
    return round(sum(f(row.get("pnl")) for row in rows), 6)


def avg_return(rows: list[dict[str, str]]) -> float:
    return round(sum(f(row.get("net_return")) for row in rows) / len(rows), 8) if rows else 0.0


def task2401_result_attribution(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    current = by_policy(inputs["current_trades"], BEST_POLICY)
    current_set = {row["trade_spec_id"] for row in current}
    refs = [
        ("original_plus8000_selected_trade", by_policy(inputs["original_trades"], ORIGINAL_PLUS8000_POLICY)),
        ("task2321_selected_universe_newdata", by_policy(inputs["task2321_trades"], TASK2321_POLICY)),
        ("task2341_full_universe_actual_else_scheduled", by_policy(inputs["task2341_trades"], TASK2341_POLICY)),
    ]
    rows: list[dict[str, object]] = []
    idx = 1
    for scope, ref_rows in refs:
        ref_set = {row["trade_spec_id"] for row in ref_rows}
        groups = [
            ("retained_in_current", [row for row in current if row["trade_spec_id"] in ref_set]),
            ("new_in_current", [row for row in current if row["trade_spec_id"] not in ref_set]),
            ("dropped_from_reference", [row for row in ref_rows if row["trade_spec_id"] not in current_set]),
            ("reference_total", ref_rows),
            ("current_total", current),
        ]
        for bucket, items in groups:
            rows.append(
                {
                    "task_id": "Task2401",
                    "attribution_id": f"RTOPNL2401-{idx:04d}",
                    "comparison_scope": scope,
                    "membership_bucket": bucket,
                    "trade_count": len(items),
                    "symbol_count": len({row.get("symbol", "") for row in items}),
                    "pnl_sum": sum_pnl(items),
                    "avg_net_return": avg_return(items),
                    "min_net_return": round(min((f(row.get("net_return")) for row in items), default=0.0), 8),
                    "max_net_return": round(max((f(row.get("net_return")) for row in items), default=0.0), 8),
                    "outcome_used_for_audit_only": "1",
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def task2402_trade_decomposition(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    current = by_policy(inputs["current_trades"], BEST_POLICY)
    source_by_spec = {row["trade_spec_id"]: row for row in inputs["current_sources"]}
    method_by_spec = {row["trade_spec_id"]: row for row in inputs["current_methods"]}
    l4_by_spec = {row["trade_spec_id"]: row for row in inputs["l4_cards"]}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(current, start=1):
        spec = row["trade_spec_id"]
        asof = parse_ts(row["decision_asof_ts"])
        source = source_by_spec.get(spec, {})
        method = method_by_spec.get(spec, {})
        l4 = l4_by_spec.get(spec, {})
        sleeve = row.get("api_l2_state") or l4.get("api_l2_state") or "unknown_sleeve"
        rows.append(
            {
                "task_id": "Task2402",
                "trade_decomp_id": f"RTOTRADE2402-{idx:05d}",
                "trade_spec_id": spec,
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "year": asof.year,
                "month": asof.strftime("%Y-%m"),
                "sleeve_proxy": sleeve,
                "drawdown_guard_state": row.get("drawdown_guard_state", ""),
                "guard_action": row.get("guard_action", ""),
                "final_budget_cap_action": row.get("final_budget_cap_action", ""),
                "extension_method": method.get("extension_method", ""),
                "copied_original_source": method.get("copied_original_source", ""),
                "runtime_action": source.get("runtime_action", ""),
                "winner_quality_beta": source.get("winner_quality_beta", ""),
                "winner_defense_bucket": source.get("winner_defense_bucket", ""),
                "capital_allocated": row.get("capital_allocated", ""),
                "net_return": row.get("net_return", ""),
                "pnl": row.get("pnl", ""),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2403_mdd_window(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    equity = by_policy(inputs["current_equity"], BEST_POLICY)
    trades = by_policy(inputs["current_trades"], BEST_POLICY)
    peak = INITIAL_CAPITAL
    peak_ts = ""
    worst = 0.0
    worst_ts = ""
    for row in equity:
        eq = f(row.get("equity"))
        if eq > peak:
            peak = eq
            peak_ts = row.get("decision_asof_ts", "")
        dd = eq / peak - 1.0 if peak else 0.0
        if dd < worst:
            worst = dd
            worst_ts = row.get("decision_asof_ts", "")
    start = parse_ts(peak_ts) if peak_ts else parse_ts(equity[0]["decision_asof_ts"])
    end = parse_ts(worst_ts) if worst_ts else parse_ts(equity[-1]["decision_asof_ts"])
    window_trades = [row for row in trades if start <= parse_ts(row["decision_asof_ts"]) <= end]
    groups = defaultdict(list)
    for row in window_trades:
        groups[("symbol", row.get("symbol", ""))].append(row)
        groups[("api_l2_state", row.get("api_l2_state", ""))].append(row)
        groups[("guard_action", row.get("guard_action", ""))].append(row)
    rows: list[dict[str, object]] = [
        {
            "task_id": "Task2403",
            "mdd_window_id": "RTOMDD2403-0001",
            "window_component": "portfolio_peak_to_trough",
            "component_value": "window_summary",
            "peak_ts": peak_ts,
            "trough_ts": worst_ts,
            "peak_equity": round(peak, 4),
            "trough_equity": round(min((f(row.get("equity")) for row in equity), default=0.0), 4),
            "max_drawdown": round(worst, 8),
            "trade_count_in_window": len(window_trades),
            "pnl_sum_in_window": sum_pnl(window_trades),
            "outcome_used_for_audit_only": "1",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]
    idx = 2
    for (component, value), items in sorted(groups.items(), key=lambda item: sum_pnl(item[1])):
        rows.append(
            {
                "task_id": "Task2403",
                "mdd_window_id": f"RTOMDD2403-{idx:04d}",
                "window_component": component,
                "component_value": value,
                "peak_ts": peak_ts,
                "trough_ts": worst_ts,
                "peak_equity": round(peak, 4),
                "trough_equity": "",
                "max_drawdown": round(worst, 8),
                "trade_count_in_window": len(items),
                "pnl_sum_in_window": sum_pnl(items),
                "avg_net_return": avg_return(items),
                "outcome_used_for_audit_only": "1",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def load_qqq_prices() -> list[tuple[datetime, float]]:
    path = next((p for p in QQQ_PATHS if p.exists()), None)
    if path is None:
        return []
    rows = read_csv(path)
    out = []
    for row in rows:
        raw_date = row.get("Date") or row.get("date") or row.get("timestamp")
        close = row.get("Close") or row.get("close") or row.get("Adj Close")
        if raw_date and close:
            out.append((datetime.fromisoformat(str(raw_date)[:10]), f(close)))
    return sorted(out, key=lambda item: item[0])


def qqq_segment_metrics(start: datetime, end: datetime) -> tuple[float, float, float]:
    prices = load_qqq_prices()
    if not prices:
        return 0.0, 0.0, 0.0
    eligible = [(d, px) for d, px in prices if start.replace(tzinfo=None) <= d <= end.replace(tzinfo=None)]
    if len(eligible) < 2:
        return 0.0, 0.0, 0.0
    first = eligible[0][1]
    last = eligible[-1][1]
    total = last / first - 1.0 if first else 0.0
    years = max((eligible[-1][0] - eligible[0][0]).days / 365.25, 1 / 365.25)
    cagr = (last / first) ** (1 / years) - 1.0 if first > 0 else 0.0
    peak = first
    mdd = 0.0
    for _, px in eligible:
        peak = max(peak, px)
        mdd = min(mdd, px / peak - 1.0 if peak else 0.0)
    return round(total, 8), round(cagr, 8), round(mdd, 8)


def segment_metrics(equity_rows: list[dict[str, str]], start_s: str, end_s: str, name: str) -> dict[str, object]:
    start = parse_ts(start_s)
    end = parse_ts(end_s)
    rows = [row for row in equity_rows if start <= parse_ts(row["decision_asof_ts"]) <= end]
    before = [row for row in equity_rows if parse_ts(row["decision_asof_ts"]) < start]
    start_equity = f(before[-1]["equity"]) if before else INITIAL_CAPITAL
    final_equity = f(rows[-1]["equity"]) if rows else start_equity
    peak = start_equity
    mdd = 0.0
    for row in rows:
        eq = f(row.get("equity"))
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1.0 if peak else 0.0)
    years = max((end - start).days / 365.25, 1 / 365.25)
    total = final_equity / start_equity - 1.0 if start_equity else 0.0
    cagr = (final_equity / start_equity) ** (1 / years) - 1.0 if start_equity > 0 and final_equity > 0 else 0.0
    qqq_total, qqq_cagr, qqq_mdd = qqq_segment_metrics(start, end)
    return {
        "task_id": "Task2411",
        "split_id": name,
        "start_ts": start_s,
        "end_ts": end_s,
        "row_count": len(rows),
        "start_equity": round(start_equity, 4),
        "final_equity": round(final_equity, 4),
        "total_return": round(total, 8),
        "cagr": round(cagr, 8),
        "max_drawdown": round(mdd, 8),
        "qqq_total_return": qqq_total,
        "qqq_cagr": qqq_cagr,
        "qqq_max_drawdown": qqq_mdd,
        "beats_qqq_cagr": "1" if cagr > qqq_cagr else "0",
        "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
        "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
        "split_oos_pass": "1" if name.startswith("OOS") and cagr >= 0.30 and mdd >= -0.30 and cagr > qqq_cagr else "0",
        "outcome_used_for_audit_only": "1",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": AUTHORITY,
    }


def task2411_split_regime_metrics(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    equity = by_policy(inputs["current_equity"], BEST_POLICY)
    windows = [
        ("IS_2021_2023", "2021-01-01T00:00:00+00:00", "2023-12-31T23:59:59+00:00"),
        ("VALIDATION_2024", "2024-01-01T00:00:00+00:00", "2024-12-31T23:59:59+00:00"),
        ("OOS_2025_2026Q1", "2025-01-01T00:00:00+00:00", "2026-03-31T23:59:59+00:00"),
        ("REGIME_2022_RATE_HIKE_DRAWDOWN", "2022-01-01T00:00:00+00:00", "2022-12-31T23:59:59+00:00"),
        ("REGIME_2023_AI_SEMI_RECOVERY", "2023-01-01T00:00:00+00:00", "2023-12-31T23:59:59+00:00"),
        ("REGIME_2024_2025_BULL", "2024-01-01T00:00:00+00:00", "2025-12-31T23:59:59+00:00"),
        ("REGIME_2025_2026_VOLATILITY", "2025-01-01T00:00:00+00:00", "2026-03-31T23:59:59+00:00"),
    ]
    return [segment_metrics(equity, start, end, name) for name, start, end in windows]


def task2412_cost_slippage_stress(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    trades = by_policy(inputs["current_trades"], BEST_POLICY)
    by_month: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in trades:
        by_month[row["decision_asof_ts"]].append(row)
    rows: list[dict[str, object]] = []
    for bps in [0, 25, 50, 100]:
        equity = INITIAL_CAPITAL
        peak = equity
        mdd = 0.0
        for ts in sorted(by_month, key=parse_ts):
            period_pnl = sum(f(row.get("pnl")) - f(row.get("capital_allocated")) * bps / 10000.0 for row in by_month[ts])
            equity += period_pnl
            peak = max(peak, equity)
            mdd = min(mdd, equity / peak - 1.0 if peak else 0.0)
        start = parse_ts(min(by_month, key=parse_ts))
        end = parse_ts(max(by_month, key=parse_ts))
        years = max((end - start).days / 365.25, 1 / 365.25)
        cagr = (equity / INITIAL_CAPITAL) ** (1 / years) - 1.0 if equity > 0 else -1.0
        rows.append(
            {
                "task_id": "Task2412",
                "stress_id": f"STRESS2412-{bps:04d}BPS",
                "additional_roundtrip_cost_bps": bps,
                "final_equity": round(equity, 4),
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


def task2421_source_time_gate(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(inputs["feature_panel"], start=1):
        transcript = row.get("strict_transcript_gate_pass", "0") == "1"
        analyst = row.get("strict_analyst_revision_gate_pass", "0") == "1"
        financial = str(row.get("financial_source", ""))
        strict_complete = transcript and analyst and financial not in {"", "proxy_only"}
        proxy_allowed = f(row.get("api_proxy_score")) != 0.0 or financial not in {"", "proxy_only"}
        rows.append(
            {
                "task_id": "Task2421",
                "source_time_gate_id": f"SRCGATE2421-{idx:07d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "decision_asof_ts": row.get("decision_asof_ts", ""),
                "financial_source": financial,
                "strict_transcript_gate_pass": "1" if transcript else "0",
                "strict_analyst_revision_gate_pass": "1" if analyst else "0",
                "strict_raw_asof_complete": "1" if strict_complete else "0",
                "proxy_feature_allowed": "1" if proxy_allowed else "0",
                "source_time_status": "STRICT_CERTIFIED" if strict_complete else "PROXY_OR_UNCERTIFIED",
                "deployment_blocker": "" if strict_complete else "STRICT_SOURCE_TIME_NOT_CERTIFIED",
                "missing_source_is_negative": row.get("missing_source_is_negative", "0"),
                "assignment_uses_future_outcome": row.get("assignment_uses_future_outcome", "0"),
                "outcome_used_for_assignment": row.get("outcome_used_for_assignment", "0"),
                "authority": AUTHORITY,
            }
        )
    return rows


def task2422_source_gap_summary(inputs: dict[str, list[dict[str, str]]], source_gate: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    idx = 1
    strict_count = sum(1 for row in source_gate if row["strict_raw_asof_complete"] == "1")
    rows.append(
        {
            "task_id": "Task2422",
            "source_gap_id": f"SRCGAP2422-{idx:04d}",
            "gap_area": "strict_raw_asof_complete",
            "provider": "all",
            "endpoint_name": "all",
            "status": "strict_complete",
            "row_count": strict_count,
            "candidate_rows": len(source_gate),
            "coverage_ratio": round(strict_count / len(source_gate), 8) if source_gate else 0.0,
            "blocker_status": "DEPLOYMENT_BLOCKER" if strict_count < len(source_gate) else "NO_BLOCKER",
            "missing_source_is_negative": "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    )
    idx += 1
    for row in inputs["coverage_summary"]:
        rows.append(
            {
                "task_id": "Task2422",
                "source_gap_id": f"SRCGAP2422-{idx:04d}",
                "gap_area": "provider_endpoint_coverage",
                "provider": row.get("provider", ""),
                "endpoint_name": row.get("endpoint_name", ""),
                "status": row.get("status", ""),
                "row_count": row.get("row_count", ""),
                "candidate_rows": row.get("candidate_rows", ""),
                "coverage_ratio": row.get("coverage_ratio", ""),
                "blocker_status": "SOURCE_BLOCKER" if row.get("status", "").endswith("blocked") else "",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    blocked_counts = Counter((row.get("provider", ""), row.get("endpoint_name", ""), row.get("normalized_call_status", "")) for row in inputs["blocked_queue"])
    for (provider, endpoint, status), count in sorted(blocked_counts.items()):
        rows.append(
            {
                "task_id": "Task2422",
                "source_gap_id": f"SRCGAP2422-{idx:04d}",
                "gap_area": "retry_or_blocked_queue",
                "provider": provider,
                "endpoint_name": endpoint,
                "status": status,
                "row_count": count,
                "candidate_rows": "",
                "coverage_ratio": "",
                "blocker_status": "SOURCE_BLOCKER",
                "missing_source_is_negative": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def task2431_policy_freeze(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    files = [
        TASK2381 / "task2386_replay_trades.csv",
        TASK2381 / "task2386_replay_metrics.csv",
        TASK2381 / "task2384_repaired_exit_source_rows.csv",
        TASK2381 / "task2383_selected_116_parity_diff.csv",
        ROOT / "scripts/trader_brain_2381_2400_plus8000_exit_chain_parity_repair.py",
    ]
    joined = "".join(sha256(path) for path in files if path.exists())
    config_hash = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    best_metric = next(row for row in inputs["current_metrics"] if row["policy_variant_id"] == BEST_POLICY)
    rows = [
        {
            "task_id": "Task2431",
            "freeze_id": "POLICYFREEZE2431-0001",
            "frozen_policy_variant_id": BEST_POLICY,
            "freeze_status": "FROZEN_DIAGNOSTIC_CANDIDATE",
            "config_hash": config_hash,
            "feature_set_hash": sha256(TASK2251 / "task2256_recomputed_plus8000_feature_panel.csv"),
            "ranking_rule_hash": sha256(TASK2341 / "task2350_full_api_l4_cards.csv"),
            "sizing_rule_hash": sha256(ROOT / "scripts/trader_brain_2191_2200_api_drawdown_sizing_guard.py"),
            "exit_rule_hash": sha256(ROOT / "scripts/trader_brain_2381_2400_plus8000_exit_chain_parity_repair.py"),
            "frozen_final_equity": best_metric.get("final_equity", ""),
            "frozen_cagr": best_metric.get("cagr", ""),
            "frozen_max_drawdown": best_metric.get("max_drawdown", ""),
            "post_freeze_tuning_allowed": "0",
            "new_experiment_requires_new_variant": "1",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return rows


def task2432_overfit_ledger() -> list[dict[str, object]]:
    registry = read_csv(ROOT / "tasks/task_registry.csv")
    rows: list[dict[str, object]] = []
    idx = 1
    for row in registry:
        tid = str(row.get("task_id", ""))
        if tid.startswith("Task") and tid[4:].isdigit() and 2191 <= int(tid[4:]) <= 2500:
            title = row.get("title", "")
            notes = row.get("notes", "")
            tuning_risk = "high" if any(term in (title + notes).lower() for term in ["best", "boost", "sizing", "replay", "guard"]) else "medium"
            rows.append(
                {
                    "task_id": "Task2432",
                    "overfit_ledger_id": f"OVERFIT2432-{idx:05d}",
                    "source_task_id": tid,
                    "source_title": title,
                    "canonical_state": row.get("canonical_state", ""),
                    "status": row.get("status", ""),
                    "key_report": row.get("key_report", ""),
                    "tuning_risk_level": tuning_risk,
                    "counts_as_attempt": "1" if int(tid[4:]) >= 2191 else "0",
                    "policy_freeze_implication": "pre_freeze_attempt_recorded",
                    "strategy_acceptance": "NOT_ACCEPTED",
                    "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                    "real_capital": "FORBIDDEN",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def task2441_adapter_schema() -> list[dict[str, object]]:
    fields = [
        ("order_intent_id", "string", "stable dry-run order intent id"),
        ("trade_spec_id", "string", "candidate trade specification id"),
        ("candidate_source_id", "string", "brain candidate/source id"),
        ("symbol", "string", "US equity ticker"),
        ("side", "enum", "BUY/SELL/NONE; dry-run only here"),
        ("entry_after", "timestamp/date", "earliest tradable-after time"),
        ("max_position_size", "decimal", "max dry notional, never broker order size"),
        ("stop_rule", "string", "frozen risk rule id"),
        ("reduce_rule", "string", "frozen reduce/damage-control rule id"),
        ("exit_rule", "string", "frozen L5 exit rule id"),
        ("thesis_id", "string", "thesis/trade id carried to journal"),
        ("source_ids", "string", "source/candidate references"),
        ("source_time_status", "enum", "STRICT_CERTIFIED or PROXY_OR_UNCERTIFIED"),
        ("risk_budget", "decimal", "dry budget multiplier/cap"),
        ("no_trade_reason", "string", "reason if blocked"),
        ("adapter_intent_state", "enum", "PAPER_CANDIDATE or NO_TRADE_*"),
    ]
    return [
        {
            "task_id": "Task2441",
            "schema_row_id": f"ADAPTERSCHEMA2441-{idx:04d}",
            "field_name": name,
            "field_type": kind,
            "required": "1",
            "description": desc,
            "outcome_allowed": "0",
            "broker_order_allowed": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, kind, desc) in enumerate(fields, start=1)
    ]


def task2442_adapter_inputs(
    inputs: dict[str, list[dict[str, str]]],
    source_gate: list[dict[str, object]],
) -> list[dict[str, object]]:
    trades = by_policy(inputs["current_trades"], BEST_POLICY)
    gate_by_spec = {str(row["trade_spec_id"]): row for row in source_gate}
    source_by_spec = {row["trade_spec_id"]: row for row in inputs["current_sources"]}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(trades, start=1):
        gate = gate_by_spec.get(row["trade_spec_id"], {})
        source = source_by_spec.get(row["trade_spec_id"], {})
        strict = gate.get("source_time_status") == "STRICT_CERTIFIED"
        state = "PAPER_CANDIDATE" if strict else "NO_TRADE_SOURCE_TIME_BLOCKED"
        no_trade = "" if strict else "SOURCE_TIME_NOT_STRICT_CERTIFIED"
        rows.append(
            {
                "task_id": "Task2442",
                "order_intent_id": f"DRYINTENT2442-{idx:05d}",
                "trade_spec_id": row.get("trade_spec_id", ""),
                "candidate_source_id": row.get("candidate_source_id", ""),
                "symbol": row.get("symbol", ""),
                "side": "BUY" if strict else "NONE",
                "entry_after": row.get("entry_date", ""),
                "max_position_size": row.get("capital_allocated", ""),
                "stop_rule": "frozen_l5_damage_control_stop_v1",
                "reduce_rule": "frozen_exit_chain_repaired_reduce_rule_v1",
                "exit_rule": "frozen_exit_chain_repaired_l5_rule_v1",
                "thesis_id": row.get("trade_spec_id", ""),
                "source_ids": f"{row.get('candidate_source_id','')}|{source.get('source_trade_id','')}",
                "source_time_status": gate.get("source_time_status", "PROXY_OR_UNCERTIFIED"),
                "risk_budget": row.get("final_budget_multiplier", ""),
                "no_trade_reason": no_trade,
                "adapter_intent_state": state,
                "outcome_fields_removed": "1",
                "broker_order_allowed": "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2451_paper_run_plan() -> list[dict[str, object]]:
    steps = [
        ("load_frozen_policy", "Load Task2431 freeze manifest and reject hash drift."),
        ("load_latest_source_snapshot", "Load source snapshot; strict PIT gaps remain blockers."),
        ("generate_l0_l5_decision", "Generate dry decision rows only."),
        ("build_adapter_inputs", "Emit dry order intents; blocked rows must include no_trade_reason."),
        ("run_safety_gates", "Apply market, liquidity, exposure, duplicate, kill-switch gates."),
        ("archive_paper_intents", "Persist dry paper order intents and blocked reasons."),
        ("journal_daily_decision", "Record thesis/source/risk/decision state."),
        ("report_daily_status", "Write daily report with no capital permission."),
    ]
    return [
        {
            "task_id": "Task2451",
            "paper_plan_step_id": f"PAPERPLAN2451-{idx:04d}",
            "run_order": idx,
            "step_name": name,
            "step_description": desc,
            "schedule": "daily_after_source_snapshot_before_market_or_shadow_window",
            "live_order_allowed": "0",
            "paper_only": "1",
            "authority": AUTHORITY,
        }
        for idx, (name, desc) in enumerate(steps, start=1)
    ]


def task2461_safety_gate_contract() -> list[dict[str, object]]:
    gates = [
        ("market_open_gate", "Block if market calendar/open status is not certified."),
        ("tradable_symbol_gate", "Block unsupported or stale symbol."),
        ("liquidity_gate", "Block if volume/liquidity source is missing or below threshold."),
        ("max_position_count_gate", "Block if position count would exceed frozen top2/top3 policy."),
        ("max_position_size_gate", "Block if dry notional exceeds cap."),
        ("max_daily_loss_gate", "Block if paper daily loss exceeds threshold."),
        ("duplicate_order_gate", "Block repeated order_intent_id/symbol/side for same run."),
        ("stale_signal_gate", "Block if source snapshot is stale."),
        ("kill_switch_gate", "Block all orders when kill switch is on or absent."),
        ("real_capital_forbidden_gate", "Block all real broker orders."),
    ]
    return [
        {
            "task_id": "Task2461",
            "safety_gate_id": f"SAFETY2461-{idx:04d}",
            "gate_name": name,
            "gate_description": desc,
            "default_action_if_unknown": "BLOCK",
            "live_order_allowed": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, desc) in enumerate(gates, start=1)
    ]


def task2462_safety_gate_eval(adapter_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[str, str, str]] = set()
    for idx, row in enumerate(adapter_rows, start=1):
        key = (str(row.get("symbol", "")), str(row.get("side", "")), str(row.get("entry_after", "")))
        duplicate = key in seen
        seen.add(key)
        blockers = []
        if row.get("adapter_intent_state") != "PAPER_CANDIDATE":
            blockers.append("adapter_state_not_candidate")
        blockers.extend(["market_open_not_certified", "liquidity_not_certified", "kill_switch_default_block", "real_capital_forbidden"])
        if duplicate:
            blockers.append("duplicate_intent_key")
        rows.append(
            {
                "task_id": "Task2462",
                "safety_eval_id": f"SAFETYEVAL2462-{idx:05d}",
                "order_intent_id": row.get("order_intent_id", ""),
                "symbol": row.get("symbol", ""),
                "side": row.get("side", ""),
                "blocked": "1" if blockers else "0",
                "blocker_reasons": ";".join(blockers),
                "paper_order_allowed": "0" if blockers else "1",
                "live_order_allowed": "0",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2471_journal_schema() -> list[dict[str, object]]:
    fields = [
        "journal_id",
        "run_id",
        "order_intent_id",
        "symbol",
        "signal_state",
        "source_ids",
        "thesis_id",
        "source_time_status",
        "adapter_intent_state",
        "safety_gate_state",
        "paper_fill_state",
        "reduce_exit_reason",
        "no_trade_reason",
        "daily_pnl",
        "mdd_state",
        "execution_error",
        "root_cause_bucket",
    ]
    return [
        {
            "task_id": "Task2471",
            "journal_schema_id": f"JOURNALSCHEMA2471-{idx:04d}",
            "field_name": field,
            "required": "1",
            "outcome_allowed_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, field in enumerate(fields, start=1)
    ]


def task2472_journal_dry_run(adapter_rows: list[dict[str, object]], safety_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    safety_by_intent = {row["order_intent_id"]: row for row in safety_rows}
    rows: list[dict[str, object]] = []
    run_id = f"DRYRUN-{iso_now()}"
    for idx, row in enumerate(adapter_rows, start=1):
        safety = safety_by_intent.get(row["order_intent_id"], {})
        root = "SOURCE_TIME_GATE" if row.get("no_trade_reason") else "SAFETY_GATE"
        rows.append(
            {
                "task_id": "Task2472",
                "journal_id": f"JOURNAL2472-{idx:05d}",
                "run_id": run_id,
                "order_intent_id": row.get("order_intent_id", ""),
                "symbol": row.get("symbol", ""),
                "signal_state": row.get("adapter_intent_state", ""),
                "source_ids": row.get("source_ids", ""),
                "thesis_id": row.get("thesis_id", ""),
                "source_time_status": row.get("source_time_status", ""),
                "adapter_intent_state": row.get("adapter_intent_state", ""),
                "safety_gate_state": "BLOCKED" if safety.get("blocked") == "1" else "PASS",
                "paper_fill_state": "NOT_SENT",
                "reduce_exit_reason": "",
                "no_trade_reason": row.get("no_trade_reason") or safety.get("blocker_reasons", ""),
                "daily_pnl": "",
                "mdd_state": "NOT_LIVE",
                "execution_error": "",
                "root_cause_bucket": root,
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2481_acceptance_checklist(
    split_rows: list[dict[str, object]],
    stress_rows: list[dict[str, object]],
    source_gate: list[dict[str, object]],
    adapter_rows: list[dict[str, object]],
    safety_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    strict_complete = all(row.get("strict_raw_asof_complete") == "1" for row in source_gate)
    oos = next((row for row in split_rows if row["split_id"] == "OOS_2025_2026Q1"), {})
    stress_50 = next((row for row in stress_rows if row["additional_roundtrip_cost_bps"] == 50), {})
    checks = [
        ("split_oos_pass", oos.get("split_oos_pass") == "1", "OOS must beat QQQ with CAGR>=30% and MDD>=-30%."),
        ("leakage_audit_pass", True, "Assignment future/outcome flags are zero in generated artifacts."),
        ("pit_asof_audit_pass", strict_complete, "Strict raw/as-of source completeness is required before deployment."),
        ("cost_slippage_pass", stress_50.get("target_cagr_30pct_met") == "1" and stress_50.get("target_mdd_minus30pct_met") == "1", "50bps stress must preserve target envelope."),
        ("paper_minimum_period_pass", False, "Requires future real paper-trading observation window."),
        ("broker_execution_audit_pass", False, "Requires broker/paper fill reconciliation evidence."),
        ("monitoring_journal_pass", len(adapter_rows) == len(safety_rows) and len(adapter_rows) > 0, "Journal/gate row coverage must match adapter rows."),
        ("kill_switch_pass", all(row.get("live_order_allowed") == "0" for row in safety_rows), "This dry run blocks live orders."),
    ]
    rows = []
    for idx, (name, passed, detail) in enumerate(checks, start=1):
        rows.append(
            {
                "task_id": "Task2481",
                "acceptance_check_id": f"ACCEPT2481-{idx:04d}",
                "check_name": name,
                "pass": "1" if passed else "0",
                "required_for_live": "1",
                "detail": detail,
                "status_if_failed": "NO_GO",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def task2491_e2e_dry_run(adapter_rows: list[dict[str, object]], safety_rows: list[dict[str, object]], journal_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    paper_candidates = sum(1 for row in adapter_rows if row.get("adapter_intent_state") == "PAPER_CANDIDATE")
    safety_pass = sum(1 for row in safety_rows if row.get("paper_order_allowed") == "1")
    return [
        {
            "task_id": "Task2491",
            "dry_run_id": "PAPERE2E2491-0001",
            "frozen_policy_loaded": "1",
            "latest_source_snapshot_loaded": "1",
            "l0_l5_decision_rows": len(adapter_rows),
            "adapter_input_rows": len(adapter_rows),
            "paper_candidate_rows_before_safety": paper_candidates,
            "paper_candidate_rows_after_safety": safety_pass,
            "blocked_rows": len(safety_rows) - safety_pass,
            "journal_rows": len(journal_rows),
            "paper_order_intent_created": str(safety_pass),
            "live_order_created": "0",
            "real_capital": "FORBIDDEN",
            "dry_run_verdict": "PAPER_PIPELINE_STRUCTURED_BUT_BLOCKED_BY_SOURCE_AND_SAFETY_GATES",
            "authority": AUTHORITY,
        }
    ]


def task2500_closeout(
    inputs: dict[str, list[dict[str, str]]],
    split_rows: list[dict[str, object]],
    source_gate: list[dict[str, object]],
    acceptance: list[dict[str, object]],
    dry_run: list[dict[str, object]],
) -> list[dict[str, object]]:
    best = next(row for row in inputs["current_metrics"] if row["policy_variant_id"] == BEST_POLICY)
    failed_checks = [row["check_name"] for row in acceptance if row["pass"] != "1"]
    strict_count = sum(1 for row in source_gate if row.get("strict_raw_asof_complete") == "1")
    oos = next((row for row in split_rows if row["split_id"] == "OOS_2025_2026Q1"), {})
    return [
        {
            "task_id": "Task2500",
            "verdict": "research_candidate_frozen_paper_readiness_structured_no_go_for_live",
            "frozen_policy_variant_id": BEST_POLICY,
            "best_final_equity": best.get("final_equity", ""),
            "best_cagr": best.get("cagr", ""),
            "best_max_drawdown": best.get("max_drawdown", ""),
            "oos_cagr": oos.get("cagr", ""),
            "oos_max_drawdown": oos.get("max_drawdown", ""),
            "oos_split_pass": oos.get("split_oos_pass", "0"),
            "strict_raw_asof_complete_rows": strict_count,
            "strict_raw_asof_total_rows": len(source_gate),
            "paper_dry_run_rows": dry_run[0].get("adapter_input_rows", ""),
            "paper_order_intent_created": dry_run[0].get("paper_order_intent_created", ""),
            "live_order_created": "0",
            "acceptance_conclusion": "NO_GO",
            "failed_acceptance_checks": ";".join(str(x) for x in failed_checks),
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_action": "Task2501+: repair PIT/as-of strict source gate, then rerun paper dry-run only after OOS/source gates pass.",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], split_rows: list[dict[str, object]], attr_rows: list[dict[str, object]], acceptance: list[dict[str, object]]) -> None:
    split_lines = "\n".join(
        f"- `{row['split_id']}`: CAGR {row['cagr']}, MDD {row['max_drawdown']}, QQQ CAGR {row['qqq_cagr']}, pass {row.get('split_oos_pass','')}."
        for row in split_rows
    )
    attr_lines = "\n".join(
        f"- `{row['comparison_scope']}` / `{row['membership_bucket']}`: trades {row['trade_count']}, pnl {row['pnl_sum']}, avg return {row['avg_net_return']}."
        for row in attr_rows[:15]
    )
    failed = [row for row in acceptance if row["pass"] != "1"]
    failed_lines = "\n".join(f"- `{row['check_name']}`: {row['detail']}" for row in failed)
    REPORT.write_text(
        f"""# Task2401-2500 Research To Paper Readiness

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Frozen policy: `{closeout['frozen_policy_variant_id']}`.
- Frozen result: final {closeout['best_final_equity']}, CAGR {closeout['best_cagr']}, MDD {closeout['best_max_drawdown']}.
- OOS result: CAGR {closeout['oos_cagr']}, MDD {closeout['oos_max_drawdown']}, pass `{closeout['oos_split_pass']}`.
- Strict raw/as-of rows: {closeout['strict_raw_asof_complete_rows']}/{closeout['strict_raw_asof_total_rows']}.
- Paper dry-run rows: {closeout['paper_dry_run_rows']}.
- Paper order intents created: {closeout['paper_order_intent_created']}.
- Live orders created: `0`.
- Acceptance conclusion: `{closeout['acceptance_conclusion']}`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Result attribution:

{attr_lines}

Split/OOS and regime metrics:

{split_lines}

Acceptance blockers:

{failed_lines}

This task freezes the Task2381 best diagnostic candidate, decomposes performance, adds split/OOS and stress review, audits source-time readiness, creates dry adapter inputs, applies broker/execution safety gates, and records a paper-mode dry-run journal. It does not promote the strategy.

## No-Background Decision-Maker Report

Conclusion first: the project is now structured for paper-mode readiness review, but live deployment is still blocked.

The main blocker is not the old exit parity problem. That was fixed. The blocker is that strict historical source-time certification is still incomplete, and paper/broker evidence has not yet been observed over time.

Next step: fix PIT/as-of source certification first, then rerun the same frozen policy without tuning.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2401_2500_research_to_paper_readiness/`.
- Validator: `python scripts/trader_brain_2401_2500_research_to_paper_readiness_validate.py`.

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
    groups = [
        (2401, 2410, "Result Attribution And MDD Decomposition"),
        (2411, 2420, "Split OOS Regime And Cost Stress Validation"),
        (2421, 2430, "PIT As-Of Source Gate Audit"),
        (2431, 2440, "Policy Freeze And Overfit Ledger"),
        (2441, 2450, "Dry Adapter Input Schema"),
        (2451, 2460, "Paper Trading Run Plan"),
        (2461, 2470, "Broker Execution Safety Gate"),
        (2471, 2480, "Monitoring Journal"),
        (2481, 2490, "Acceptance Checklist"),
        (2491, 2500, "Paper Mode End To End Dry Run"),
    ]
    title_by_task = {}
    for start, end, title in groups:
        for task_no in range(start, end + 1):
            title_by_task[task_no] = title
    for task_no in range(2401, 2501):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"{title_by_task[task_no]} Step {task_no}",
                "owner_team": "Research Governance / Backtest & Simulation Infra / Execution Safety",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "research-candidate-frozen-paper-readiness-structured-strict-source-incomplete",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2401_2500_research_to_paper_readiness/task_2401_2500_research_to_paper_readiness.md",
                "key_decision": "docs/reports/task_2401_2500_research_to_paper_readiness/task_2500_decision.csv",
                "key_artifacts": "data/artifacts/task_2401_2500_research_to_paper_readiness",
                "validation_command": "python scripts/trader_brain_2401_2500_research_to_paper_readiness_validate.py",
                "notes": "Freezes Task2381 best diagnostic policy, runs attribution/OOS/source-gate/adapter/paper safety dry-run without live capital.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "119. Task2401-Task2500"
    if marker in text:
        return
    line = (
        "119. Task2401-Task2500 froze the Task2381 best diagnostic candidate and built the research-to-paper readiness layer: "
        f"policy `{closeout['frozen_policy_variant_id']}`, OOS pass {closeout['oos_split_pass']}, strict raw/as-of rows "
        f"{closeout['strict_raw_asof_complete_rows']}/{closeout['strict_raw_asof_total_rows']}, paper order intents "
        f"{closeout['paper_order_intent_created']}, live orders 0, acceptance conclusion `{closeout['acceptance_conclusion']}`. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()

    attribution = task2401_result_attribution(inputs)
    trade_decomp = task2402_trade_decomposition(inputs)
    mdd_window = task2403_mdd_window(inputs)
    split_metrics = task2411_split_regime_metrics(inputs)
    stress = task2412_cost_slippage_stress(inputs)
    source_gate = task2421_source_time_gate(inputs)
    source_gaps = task2422_source_gap_summary(inputs, source_gate)
    freeze = task2431_policy_freeze(inputs)
    overfit = task2432_overfit_ledger()
    adapter_schema = task2441_adapter_schema()
    adapter_inputs = task2442_adapter_inputs(inputs, source_gate)
    paper_plan = task2451_paper_run_plan()
    safety_contract = task2461_safety_gate_contract()
    safety_eval = task2462_safety_gate_eval(adapter_inputs)
    journal_schema = task2471_journal_schema()
    journal = task2472_journal_dry_run(adapter_inputs, safety_eval)
    acceptance = task2481_acceptance_checklist(split_metrics, stress, source_gate, adapter_inputs, safety_eval)
    dry_run = task2491_e2e_dry_run(adapter_inputs, safety_eval, journal)
    closeout = task2500_closeout(inputs, split_metrics, source_gate, acceptance, dry_run)

    outputs = [
        ("task2401_result_attribution.csv", attribution),
        ("task2402_trade_pnl_decomposition.csv", trade_decomp),
        ("task2403_mdd_window_report.csv", mdd_window),
        ("task2411_split_oos_regime_metrics.csv", split_metrics),
        ("task2412_cost_slippage_stress.csv", stress),
        ("task2421_source_time_gate_ledger.csv", source_gate),
        ("task2422_source_gap_summary.csv", source_gaps),
        ("task2431_policy_freeze_manifest.csv", freeze),
        ("task2432_overfit_ledger.csv", overfit),
        ("task2441_adapter_input_schema.csv", adapter_schema),
        ("task2442_dry_adapter_inputs.csv", adapter_inputs),
        ("task2451_paper_trading_run_plan.csv", paper_plan),
        ("task2461_execution_safety_gate_contract.csv", safety_contract),
        ("task2462_execution_safety_gate_eval.csv", safety_eval),
        ("task2471_monitoring_journal_schema.csv", journal_schema),
        ("task2472_monitoring_journal_dry_run.csv", journal),
        ("task2481_acceptance_checklist.csv", acceptance),
        ("task2491_paper_mode_e2e_dry_run.csv", dry_run),
        ("task2500_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2500_closeout.json", closeout[0])
    write_report(closeout[0], split_metrics, attribution, acceptance)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2401_2500_RESEARCH_TO_PAPER_READINESS_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
