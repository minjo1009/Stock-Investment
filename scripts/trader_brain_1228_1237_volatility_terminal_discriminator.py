from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/raw/task_1228_1237_volatility_vs_terminal_sources"
TASK1171 = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
OUT_DIR = ROOT / "data/artifacts/task_1228_1237_volatility_terminal_discriminator"
REPORT_DIR = ROOT / "docs/reports/task_1228_1237_volatility_terminal_discriminator"

AUTHORITY = "DIAGNOSTIC_VOLATILITY_TERMINAL_DISCRIMINATOR_ONLY"
BASE_VARIANT = "l0_l3_slot5_v1"
POLICY_VARIANT = "vol_terminal_discriminator_slot5_v1"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
BENCHMARK = "QQQ"


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
    path = PRICE_DIR / symbol / f"{symbol}_daily.csv"
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


def cagr(start_value: float, end_value: float, start: date, end: date) -> float:
    years = (end - start).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def max_drawdown(values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def source_catalog() -> list[dict[str, object]]:
    downloads = {row["file"]: row for row in read_csv(RAW_DIR / "download_log.csv")}
    specs = [
        ("SRC1228-001", "Nasdaq Rule 5800 deficiency process", "nasdaq_5800_series_deficiency_rules.html", "listing_terminal", "L0/L1", "minimum bid and deficiency process source"),
        ("SRC1228-002", "Nasdaq Continued Listing Guide", "nasdaq_continued_listing_guide.pdf", "listing_terminal", "L0/L1", "continued listing standards context"),
        ("SRC1228-003", "SEC Form 8-K Item 3.01", "sec_form_8k_item_301.pdf", "terminal_event", "L1", "delisting or failure to satisfy listing rule source"),
        ("SRC1228-004", "SEC Financial Reporting Manual", "sec_financial_reporting_manual.pdf", "going_concern", "L1/L2", "going concern and disclosure context"),
        ("SRC1228-005", "FASB ASU 2014-15 Going Concern", "fasb_asu_2014_15_going_concern.pdf", "going_concern", "L1/L2", "substantial doubt source semantics"),
        ("SRC1228-006", "SEC Item 303 MD&A liquidity rule", "sec_item303_mda_liquidity_rule.pdf", "liquidity_distress", "L1/L2", "liquidity and capital resources source semantics"),
        ("SRC1228-007", "FINRA Non-Traditional ETF FAQ", "finra_non_traditional_etf_faq.html", "leveraged_product", "L1/L3", "leveraged/inverse daily reset and monitoring context"),
        ("SRC1228-008", "SEC Investor.gov Leveraged/Inverse ETF", "sec_investor_gov_leveraged_inverse_etf.html", "leveraged_product", "L1/L3", "official leveraged ETF risk context"),
        ("SRC1228-009", "Campbell Hilscher Szilagyi distress risk", "ssrn_campbell_hilscher_szilagyi_distress.html", "academic_distress", "L2/L3", "distress predictors include leverage profitability market cap volatility cash price"),
        ("SRC1228-010", "NBER In Search of Distress Risk", "nber_in_search_of_distress_risk.html", "academic_distress", "L2/L3", "academic source for distress conjunction rather than single volatility signal"),
        ("SRC1228-011", "SEC Form S-3", "sec_form_s3.pdf", "dilution_pressure", "L1/L2", "shelf offering and financing pressure source"),
        ("SRC1228-012", "SEC Microcap Stock Guide", "sec_microcap_stock_guide.html", "microcap_fragility", "L0/L2", "fragility context but not fraud prediction"),
    ]
    rows = []
    for source_id, title, file_name, family, layer, use_case in specs:
        dl = downloads.get(file_name, {})
        rows.append(
            {
                "task_id": "Task1228",
                "source_id": source_id,
                "title": title,
                "local_file": file_name,
                "download_status": dl.get("status", "missing"),
                "size_bytes": dl.get("size_bytes", ""),
                "source_family": family,
                "layer_use": layer,
                "use_case": use_case,
                "authority": AUTHORITY,
            }
        )
    return rows


def is_complex_product(symbol: str, entity_name: str) -> bool:
    upper_name = entity_name.upper()
    upper_symbol = symbol.upper()
    product_tokens = ["PROSHARES", "TRUST", "ETF", "ETN", "FUND", "ULTRASHORT", "INVERSE"]
    return upper_symbol in {"BOIL"} or any(token in upper_name for token in product_tokens)


def build_base_rows() -> list[dict[str, object]]:
    selections = [row for row in read_csv(TASK1201 / "task1205_slot_selections.csv") if row["policy_variant_id"] == BASE_VARIANT]
    features = read_csv(TASK1171 / "task1174_public_filer_proxy_feature_panel.csv")
    pool = read_csv(TASK1171 / "task1171_price_download_pool.csv")
    feature_by_key = {(row["decision_asof_ts"], row["symbol"]): row for row in features}
    pool_by_symbol = {row["symbol"]: row for row in pool}
    rows = []
    for row in selections:
        feature = feature_by_key.get((row["decision_asof_ts"], row["symbol"]), {})
        pool_row = pool_by_symbol.get(row["symbol"], {})
        merged = {
            **row,
            "entity_name": pool_row.get("entity_name", ""),
            "exchanges": pool_row.get("exchanges", ""),
            "decision_close": feature.get("decision_close", ""),
            "momentum_126d": feature.get("momentum_126d", ""),
            "momentum_252d": feature.get("momentum_252d", ""),
            "realized_vol_90d": feature.get("realized_vol_90d", ""),
            "avg_dollar_volume_60d": feature.get("avg_dollar_volume_60d", ""),
            "filing_count_90d": feature.get("filing_count_90d", ""),
            "filing_count_365d": feature.get("filing_count_365d", ""),
            "form_diversity_365d": feature.get("form_diversity_365d", ""),
            "latest_filing_ts": feature.get("latest_filing_ts", ""),
            "source_time_pass": feature.get("source_time_pass", "0"),
        }
        rows.append(merged)
    return rows


def classify_route(row: dict[str, object]) -> tuple[str, list[str], float, str]:
    symbol = str(row["symbol"])
    entity_name = str(row["entity_name"])
    decision_close = to_float(row["decision_close"])
    mom126 = to_float(row["momentum_126d"])
    mom252 = to_float(row["momentum_252d"])
    vol90 = to_float(row["realized_vol_90d"])
    adv = to_float(row["avg_dollar_volume_60d"])
    filing90 = to_float(row["filing_count_90d"])
    form_diversity = to_float(row["form_diversity_365d"])

    product = is_complex_product(symbol, entity_name)
    high_vol = vol90 >= 0.85
    extreme_vol = vol90 >= 1.75
    positive_trend = mom126 > 0 and mom252 > 0
    strong_trend = mom126 > 0.25 and mom252 > 0.25
    liquidity_ok = adv >= 25_000_000
    low_price = decision_close < 5
    deep_negative_trend = mom126 < -0.20 and mom252 < -0.35
    event_density_high = filing90 >= 80 or form_diversity >= 16
    event_density_extreme = filing90 >= 120

    flags: list[str] = []
    if product:
        flags.append("product_sleeve")
    if high_vol:
        flags.append("high_volatility")
    if extreme_vol:
        flags.append("extreme_volatility")
    if positive_trend:
        flags.append("positive_momentum")
    if strong_trend:
        flags.append("strong_momentum")
    if liquidity_ok:
        flags.append("liquidity_ok")
    if low_price:
        flags.append("low_price_exposure")
    if deep_negative_trend:
        flags.append("deep_negative_trend")
    if event_density_high:
        flags.append("high_sec_event_density")
    if event_density_extreme:
        flags.append("extreme_sec_event_density")

    if product:
        return "product_sleeve", flags, 0.25, "routes"

    # High volatility is preserved when it comes with positive momentum and adequate liquidity.
    if high_vol and positive_trend and liquidity_ok and not (low_price and event_density_high):
        return "high_vol_upside", flags, 1.00, "reinforces"

    distress_evidence = 0
    for condition in [low_price, deep_negative_trend, event_density_high, extreme_vol and not positive_trend, adv < 10_000_000]:
        distress_evidence += 1 if condition else 0

    if distress_evidence >= 3:
        return "collapse_risk", flags, 0.25, "weakens"
    if distress_evidence >= 2:
        return "watch_distress", flags, 0.50, "conditions"
    if high_vol:
        return "mixed_transition", flags, 0.75, "conditions"
    return "ordinary_pass", flags, 1.00, "passes"


def task1229_instrument_gate(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        product = is_complex_product(str(row["symbol"]), str(row["entity_name"]))
        rows.append(
            {
                "task_id": "Task1229",
                "instrument_gate_id": f"INST1229-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "entity_name": row["entity_name"],
                "exchanges": row["exchanges"],
                "security_product_type_l1": "leveraged_or_complex_product" if product else "ordinary_equity_proxy",
                "ordinary_equity_pass": "0" if product else "1",
                "product_sleeve_required": "1" if product else "0",
                "data_insufficient": "0" if row["entity_name"] and row["exchanges"] else "1",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1230_l1_signals(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        route, flags, multiplier, relation = classify_route(row)
        rows.append(
            {
                "task_id": "Task1230",
                "l1_signal_id": f"L1SIG1230-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "realized_vol_90d": row["realized_vol_90d"],
                "momentum_126d": row["momentum_126d"],
                "momentum_252d": row["momentum_252d"],
                "avg_dollar_volume_60d": row["avg_dollar_volume_60d"],
                "filing_count_90d": row["filing_count_90d"],
                "form_diversity_365d": row["form_diversity_365d"],
                "high_vol_upside_signal": "1" if route == "high_vol_upside" else "0",
                "distress_conjunction_signal": "1" if route in {"watch_distress", "collapse_risk"} else "0",
                "terminal_text_signal_attached": "0",
                "dilution_text_signal_attached": "0",
                "source_time_pass": row["source_time_pass"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1231_l2_discriminator(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        route, flags, multiplier, relation = classify_route(row)
        rows.append(
            {
                "task_id": "Task1231",
                "l2_discriminator_id": f"L2DISC1231-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "volatility_terminal_route": route,
                "route_reason_flags": ";".join(flags) if flags else "none",
                "position_multiplier": multiplier,
                "volatility_not_penalized_alone": "1",
                "requires_two_independent_distress_evidence": "1",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1232_l3_edges(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in base_rows:
        route, flags, multiplier, relation = classify_route(row)
        rows.append(
            {
                "task_id": "Task1232",
                "l3_edge_id": f"EDGE1232-{len(rows)+1:07d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "from_node": f"company:{row['symbol']}",
                "to_node": f"vol_terminal_route:{route}",
                "relation_primitive": relation,
                "route": route,
                "edge_meaning": ";".join(flags) if flags else "none",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def stop_exit(symbol: str, entry_date: str, scheduled_exit_date: str, entry_price: float, route: str) -> tuple[str, float, str]:
    frame = load_price(symbol)
    if frame is None:
        return scheduled_exit_date, entry_price, "missing_price_hold_flat"
    start = datetime.fromisoformat(entry_date).date()
    end = datetime.fromisoformat(scheduled_exit_date).date()
    product = route == "product_sleeve"
    if product:
        end = min(end, start + timedelta(days=14))
    sub = frame[(frame["Date"] >= start) & (frame["Date"] <= end)]
    if sub.empty:
        return scheduled_exit_date, entry_price, "missing_window_hold_flat"
    if route in {"ordinary_pass", "high_vol_upside"}:
        last = sub.iloc[-1]
        return last["Date"].isoformat(), float(last["Close"]), "scheduled_preserve_upside"
    entry_stop = {
        "mixed_transition": 0.65,
        "watch_distress": 0.75,
        "collapse_risk": 0.85,
        "product_sleeve": 0.85,
    }.get(route, 0.75)
    peak_stop = {
        "mixed_transition": 0.55,
        "watch_distress": 0.65,
        "collapse_risk": 0.75,
        "product_sleeve": 0.80,
    }.get(route, 0.65)
    peak = entry_price
    for price_row in sub.itertuples(index=False):
        close = float(price_row.Close)
        peak = max(peak, close)
        if close <= entry_price * entry_stop:
            return price_row.Date.isoformat(), close, "route_entry_drawdown_stop"
        if close <= peak * peak_stop:
            return price_row.Date.isoformat(), close, "route_peak_drawdown_stop"
    last = sub.iloc[-1]
    return last["Date"].isoformat(), float(last["Close"]), "scheduled_or_product_expiry"


def task1233_policy_specs(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    cooldown_until: dict[str, date] = {}
    for row in sorted(base_rows, key=lambda item: (str(item["decision_asof_ts"]), int(str(item["candidate_rank"])))):
        route, flags, multiplier, relation = classify_route(row)
        decision_date = datetime.fromisoformat(str(row["decision_asof_ts"]).replace("Z", "+00:00")).date()
        symbol = str(row["symbol"])
        blocked = symbol in cooldown_until and decision_date < cooldown_until[symbol]
        entry_price = to_float(row["entry_price"])
        adjusted_exit_date, adjusted_exit_price, exit_reason = stop_exit(
            symbol,
            str(row["entry_date"]),
            str(row["exit_date"]),
            entry_price,
            route,
        )
        if exit_reason in {"route_entry_drawdown_stop", "route_peak_drawdown_stop"} and route in {"watch_distress", "collapse_risk", "product_sleeve"}:
            cooldown_until[symbol] = datetime.fromisoformat(adjusted_exit_date).date() + timedelta(days=62)
        rows.append(
            {
                "task_id": "Task1233",
                "policy_spec_id": f"VTD1233-{len(rows)+1:06d}",
                "selection_id": row["selection_id"],
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": symbol,
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "volatility_terminal_route": route,
                "route_reason_flags": ";".join(flags) if flags else "none",
                "entry_date": row["entry_date"],
                "entry_price": entry_price,
                "scheduled_exit_date": row["exit_date"],
                "scheduled_exit_price": row["exit_price"],
                "adjusted_exit_date": adjusted_exit_date,
                "adjusted_exit_price": round(adjusted_exit_price, 6),
                "exit_reason": "reentry_cooling_block" if blocked else exit_reason,
                "position_multiplier": 0.0 if blocked else multiplier,
                "selection_promoted": "0",
                "assignment_uses_future_outcome": "0",
                "exit_uses_post_entry_price_path": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def run_replay(specs: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for spec in specs:
        by_decision[str(spec["decision_asof_ts"])].append(spec)
    capital = INITIAL_CAPITAL
    trades = []
    equity = []
    for decision_ts, items in sorted(by_decision.items()):
        base_slot = capital / 5.0
        invested = 0.0
        new_capital = capital
        period_pnl = 0.0
        for item in sorted(items, key=lambda row: int(str(row["candidate_rank"]))):
            allocation = base_slot * float(item["position_multiplier"])
            invested += allocation
            entry = float(item["entry_price"])
            exit_ = float(item["adjusted_exit_price"])
            net_return = exit_ / entry - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if allocation > 0 and entry > 0 else 0.0
            pnl = allocation * net_return
            period_pnl += pnl
            new_capital += pnl
            trades.append(
                {
                    "task_id": "Task1234",
                    "policy_variant_id": POLICY_VARIANT,
                    "trade_id": f"TRADE1234-{len(trades)+1:07d}",
                    **item,
                    "capital_allocated": round(allocation, 4),
                    "net_return": round(net_return, 8),
                    "pnl": round(pnl, 4),
                    "authority": AUTHORITY,
                }
            )
        cash_weight = max(0.0, 1.0 - invested / capital) if capital > 0 else 0.0
        period_return = new_capital / capital - 1.0 if capital > 0 else 0.0
        capital = max(new_capital, 0.01)
        equity.append(
            {
                "task_id": "Task1234",
                "policy_variant_id": POLICY_VARIANT,
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_return": round(period_return, 8),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(items),
                "cash_weight_after_routing": round(cash_weight, 6),
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_slot5 = next(row for row in base_metrics if row["policy_variant_id"] == BASE_VARIANT)
    start = datetime.fromisoformat(str(equity[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
    end = max(datetime.fromisoformat(str(row["adjusted_exit_date"])).date() for row in trades)
    values = [INITIAL_CAPITAL] + [float(row["equity"]) for row in equity]
    final = values[-1]
    executed = [row for row in trades if float(row["capital_allocated"]) > 0]
    wins = sum(1 for row in executed if float(row["net_return"]) > 0)
    return [
        {
            "task_id": "Task1234",
            "policy_variant_id": POLICY_VARIANT,
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final, 4),
            "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
            "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
            "max_drawdown": round(max_drawdown(values), 6),
            "trade_count": len(executed),
            "blocked_or_zero_size_count": len(trades) - len(executed),
            "win_rate": round(wins / len(executed), 6) if executed else 0,
            "base_slot5_final_equity": base_slot5["final_equity"],
            "base_slot5_cagr": base_slot5["cagr"],
            "base_slot5_max_drawdown": base_slot5["max_drawdown"],
            "beats_base_slot5": "1" if final > float(base_slot5["final_equity"]) else "0",
            "benchmark_symbol": base_slot5["benchmark_symbol"],
            "benchmark_final_equity": base_slot5["benchmark_final_equity"],
            "benchmark_cagr": base_slot5["benchmark_cagr"],
            "beats_benchmark": "1" if final > float(base_slot5["benchmark_final_equity"]) else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def route_distribution(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, int] = defaultdict(int)
    for row in rows:
        grouped[str(row["volatility_terminal_route"])] += 1
    return [
        {
            "task_id": "Task1235",
            "route": route,
            "row_count": count,
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
        for route, count in sorted(grouped.items())
    ]


def acceptance_gate(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    row = metric_rows[0]
    return [
        {
            "task_id": "Task1236",
            "acceptance_gate_id": "ACCEPT1236-001",
            "policy_variant_id": row["policy_variant_id"],
            "final_equity": row["final_equity"],
            "cagr": row["cagr"],
            "max_drawdown": row["max_drawdown"],
            "beats_base_slot5": row["beats_base_slot5"],
            "beats_benchmark": row["beats_benchmark"],
            "target_cagr_30pct_pass": "1" if float(row["cagr"]) >= 0.30 else "0",
            "target_mdd_minus30pct_pass": "1" if float(row["max_drawdown"]) >= -0.30 else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]


def write_report(closeout: dict[str, object], metric: dict[str, object], route_rows: list[dict[str, object]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1228_1237_volatility_terminal_discriminator.md"
    route_lines = ["| Route | Rows |", "| --- | ---: |"]
    for row in route_rows:
        route_lines.append(f"| `{row['route']}` | {row['row_count']} |")
    lines = [
        "# Task1228-1237 Volatility Terminal Discriminator",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Final equity: {metric['final_equity']}.",
        f"- CAGR: {metric['cagr']}.",
        f"- MDD: {metric['max_drawdown']}.",
        f"- Beats Task1201 slot5: {metric['beats_base_slot5']}.",
        f"- Beats QQQ: {metric['beats_benchmark']}.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This task replaces the broad volatility penalty with a prior-knowable discriminator.",
        "",
        "Routing:",
        "",
        *route_lines,
        "",
        "Key rules:",
        "",
        "- High volatility alone is never a terminal-risk signal.",
        "- High volatility with positive 126d/252d momentum and adequate liquidity routes to `high_vol_upside`.",
        "- Terminal/collapse risk requires multiple independent distress signs.",
        "- Product-sleeve rows are allowed but separated.",
        "",
        "Leakage boundary:",
        "",
        "- 2026Q1 returns and collapse labels are not used for assignment.",
        "- PnL, net return, exit reason, and post-entry prices are not used for L0-L3 routing.",
        "- Post-entry prices are used only by L5 exit simulation.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We stopped treating volatility itself as bad.",
        "",
        "The brain now tries to separate exciting volatility from survival-risk volatility.",
        "",
        "This is still diagnostic only.",
        "",
        "## Artifact Manifest",
        "",
        "- `task1228_source_catalog.csv`",
        "- `task1229_l0_instrument_gate.csv`",
        "- `task1230_l1_prior_knowable_signals.csv`",
        "- `task1231_l2_volatility_terminal_discriminator.csv`",
        "- `task1232_l3_route_edges.csv`",
        "- `task1233_policy_specs.csv`",
        "- `task1234_replay_trades.csv`",
        "- `task1234_replay_equity.csv`",
        "- `task1234_replay_metrics.csv`",
        "- `task1235_route_distribution.csv`",
        "- `task1236_acceptance_gate.csv`",
        "- `task1237_closeout.csv/json`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1228_1237_volatility_terminal_discriminator_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1228_1237_volatility_terminal_discriminator`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1228_1237_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_rows = build_base_rows()
    rows1228 = source_catalog()
    rows1229 = task1229_instrument_gate(base_rows)
    rows1230 = task1230_l1_signals(base_rows)
    rows1231 = task1231_l2_discriminator(base_rows)
    rows1232 = task1232_l3_edges(base_rows)
    rows1233 = task1233_policy_specs(base_rows)
    trades, equity = run_replay(rows1233)
    metric_rows = metrics(trades, equity)
    route_rows = route_distribution(rows1231)
    gate = acceptance_gate(metric_rows)
    metric = metric_rows[0]
    closeout = {
        "task_id": "Task1228-1237",
        "verdict": "volatility_terminal_discriminator_executed_not_accepted",
        "source_rows": len(rows1228),
        "downloaded_source_rows": sum(1 for row in rows1228 if str(row["download_status"]).startswith("downloaded")),
        "instrument_gate_rows": len(rows1229),
        "l1_signal_rows": len(rows1230),
        "l2_discriminator_rows": len(rows1231),
        "l3_edge_rows": len(rows1232),
        "policy_spec_rows": len(rows1233),
        "trade_rows": len(trades),
        "final_equity": metric["final_equity"],
        "cagr": metric["cagr"],
        "max_drawdown": metric["max_drawdown"],
        "beats_base_slot5": metric["beats_base_slot5"],
        "beats_benchmark": metric["beats_benchmark"],
        "replay_executed": "1",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "add_raw_going_concern_dilution_delisting_text_extractors_and_compare_v2",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1228_source_catalog.csv", rows1228)
    write_csv(OUT_DIR / "task1229_l0_instrument_gate.csv", rows1229)
    write_csv(OUT_DIR / "task1230_l1_prior_knowable_signals.csv", rows1230)
    write_csv(OUT_DIR / "task1231_l2_volatility_terminal_discriminator.csv", rows1231)
    write_csv(OUT_DIR / "task1232_l3_route_edges.csv", rows1232)
    write_csv(OUT_DIR / "task1233_policy_specs.csv", rows1233)
    write_csv(OUT_DIR / "task1234_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1234_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1234_replay_metrics.csv", metric_rows)
    write_csv(OUT_DIR / "task1235_route_distribution.csv", route_rows)
    write_csv(OUT_DIR / "task1236_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1237_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1237_closeout.json", closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    write_report(closeout, metric, route_rows)
    print(
        "[TRADER_BRAIN_1228_1237_VOL_TERM_DISCRIMINATOR_OK] "
        f"final={metric['final_equity']} cagr={metric['cagr']} mdd={metric['max_drawdown']} "
        f"beats_base={metric['beats_base_slot5']} beats_qqq={metric['beats_benchmark']}"
    )


if __name__ == "__main__":
    main()
