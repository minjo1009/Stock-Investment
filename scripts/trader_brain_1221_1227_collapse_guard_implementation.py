from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1171 = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
OUT_DIR = ROOT / "data/artifacts/task_1221_1227_collapse_guard_implementation"
REPORT_DIR = ROOT / "docs/reports/task_1221_1227_collapse_guard_implementation"

AUTHORITY = "DIAGNOSTIC_COLLAPSE_GUARD_IMPLEMENTATION_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
BASE_VARIANT = "l0_l3_slot5_v1"
POLICY_VARIANT = "collapse_guard_slot5_v1"
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


def is_complex_product(symbol: str, entity_name: str) -> bool:
    upper_name = entity_name.upper()
    upper_symbol = symbol.upper()
    product_tokens = ["PROSHARES", "TRUST", "ETF", "ETN", "FUND", "ULTRASHORT", "INVERSE"]
    known_complex = {"BOIL"}
    return upper_symbol in known_complex or any(token in upper_name for token in product_tokens)


def product_sleeve(symbol: str, entity_name: str) -> str:
    if is_complex_product(symbol, entity_name):
        return "leveraged_or_complex_product"
    return "ordinary_equity"


def risk_bucket(row: dict[str, object]) -> tuple[str, float, list[str]]:
    flags: list[str] = []
    sleeve = str(row["product_sleeve"])
    decision_close = to_float(row["decision_close"])
    momentum_126d = to_float(row["momentum_126d"])
    momentum_252d = to_float(row["momentum_252d"])
    realized_vol_90d = to_float(row["realized_vol_90d"])
    avg_dollar_volume_60d = to_float(row["avg_dollar_volume_60d"])
    filing_count_90d = to_float(row["filing_count_90d"])
    derived_theme = str(row["derived_theme"])

    if sleeve != "ordinary_equity":
        flags.append("product_sleeve_required")
    if decision_close < 5:
        flags.append("low_price_floor_watch")
    if avg_dollar_volume_60d < 10_000_000:
        flags.append("thin_liquidity_watch")
    if realized_vol_90d >= 1.25:
        flags.append("extreme_volatility")
    elif realized_vol_90d >= 0.85:
        flags.append("high_volatility")
    if momentum_252d <= -0.45 and momentum_126d <= -0.10:
        flags.append("persistent_downtrend")
    if filing_count_90d >= 80:
        flags.append("high_sec_event_density")
    if derived_theme == "unclassified":
        flags.append("theme_quality_watch")

    if "product_sleeve_required" in flags:
        return "product_sleeve", 0.25, flags
    if "persistent_downtrend" in flags and ("extreme_volatility" in flags or decision_close < 5):
        return "distress_haircut", 0.25, flags
    if "extreme_volatility" in flags or ("low_price_floor_watch" in flags and "thin_liquidity_watch" in flags):
        return "distress_haircut", 0.50, flags
    if flags:
        return "watch", 0.75, flags
    return "clean", 1.00, flags


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
        entity_name = pool_row.get("entity_name", "")
        sleeve = product_sleeve(row["symbol"], entity_name)
        merged: dict[str, object] = {
            **row,
            "entity_name": entity_name,
            "exchanges": pool_row.get("exchanges", ""),
            "historical_filing_count_2021_2026q1": pool_row.get("historical_filing_count_2021_2026q1", ""),
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
            "product_sleeve": sleeve,
        }
        bucket, multiplier, flags = risk_bucket(merged)
        merged["risk_bucket"] = bucket
        merged["position_multiplier"] = multiplier
        merged["collapse_guard_flags"] = ";".join(flags) if flags else "none"
        rows.append(merged)
    return rows


def task1221_listing_adapter(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        identity_pass = "1" if row.get("entity_name") and row.get("exchanges") else "0"
        rows.append(
            {
                "task_id": "Task1221",
                "listing_adapter_id": f"LIST1221-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "entity_name": row["entity_name"],
                "exchanges": row["exchanges"],
                "security_identity_clean": identity_pass,
                "listing_survival_status_proxy": "public_filer_exchange_listed_proxy" if identity_pass == "1" else "identity_missing_review",
                "corporate_action_identity_exact": "0",
                "corporate_action_identity_gap": "1",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1222_distress_panel(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        flags = str(row["collapse_guard_flags"])
        rows.append(
            {
                "task_id": "Task1222",
                "distress_panel_id": f"DIST1222-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "decision_close": row["decision_close"],
                "momentum_126d": row["momentum_126d"],
                "momentum_252d": row["momentum_252d"],
                "realized_vol_90d": row["realized_vol_90d"],
                "avg_dollar_volume_60d": row["avg_dollar_volume_60d"],
                "filing_count_90d": row["filing_count_90d"],
                "latest_filing_ts": row["latest_filing_ts"],
                "risk_bucket": row["risk_bucket"],
                "collapse_guard_flags": flags,
                "distress_evidence_basis": "public_filer_proxy_price_path_and_sec_event_density",
                "raw_going_concern_text_attached": "0",
                "raw_dilution_text_attached": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1223_product_classifier(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        rows.append(
            {
                "task_id": "Task1223",
                "product_classifier_id": f"PROD1223-{idx:06d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "entity_name": row["entity_name"],
                "product_sleeve": row["product_sleeve"],
                "leverage_allowed": "1",
                "ordinary_equity_ranking_allowed": "0" if row["product_sleeve"] != "ordinary_equity" else "1",
                "required_l5_handling": "shorter_holding_smaller_size_explicit_stop" if row["product_sleeve"] != "ordinary_equity" else "ordinary_equity_policy",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1224_relation_edges(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in base_rows:
        relation = "conditions"
        if row["risk_bucket"] == "product_sleeve":
            relation = "routes"
        elif row["risk_bucket"] == "distress_haircut":
            relation = "weakens"
        elif row["risk_bucket"] == "clean":
            relation = "passes"
        rows.append(
            {
                "task_id": "Task1224",
                "edge_id": f"EDGE1224-{len(rows)+1:07d}",
                "selection_id": row["selection_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "from_node": f"company:{row['symbol']}",
                "to_node": f"collapse_guard:{row['risk_bucket']}",
                "relation_primitive": relation,
                "edge_meaning": row["collapse_guard_flags"],
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1225_l4_cards(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(base_rows, start=1):
        contradiction = "none"
        if row["risk_bucket"] in {"product_sleeve", "distress_haircut"}:
            contradiction = "weakens"
        rows.append(
            {
                "task_id": "Task1225",
                "l4_collapse_card_id": f"L4COL1225-{idx:06d}",
                "selection_id": row["selection_id"],
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "listing_risk_state": "watch" if row["risk_bucket"] != "clean" else "clean",
                "distress_bucket": row["risk_bucket"],
                "product_sleeve": row["product_sleeve"],
                "contradiction_chain": contradiction,
                "new_evidence_required_for_reentry": "1" if row["risk_bucket"] != "clean" else "0",
                "collapse_guard_flags": row["collapse_guard_flags"],
                "selection_promoted": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def stop_exit(symbol: str, entry_date: str, scheduled_exit_date: str, entry_price: float, product: bool) -> tuple[str, float, str]:
    frame = load_price(symbol)
    if frame is None:
        return scheduled_exit_date, entry_price, "missing_price_hold_flat"
    start = datetime.fromisoformat(entry_date).date()
    end = datetime.fromisoformat(scheduled_exit_date).date()
    if product:
        end = min(end, start + timedelta(days=14))
    sub = frame[(frame["Date"] >= start) & (frame["Date"] <= end)]
    if sub.empty:
        return scheduled_exit_date, entry_price, "missing_window_hold_flat"
    peak = entry_price
    entry_stop = 0.85 if product else 0.75
    peak_stop = 0.80 if product else 0.65
    for price_row in sub.itertuples(index=False):
        close = float(price_row.Close)
        peak = max(peak, close)
        if close <= entry_price * entry_stop:
            return price_row.Date.isoformat(), close, "entry_drawdown_stop"
        if close <= peak * peak_stop:
            return price_row.Date.isoformat(), close, "peak_drawdown_stop"
    last = sub.iloc[-1]
    return last["Date"].isoformat(), float(last["Close"]), "scheduled_or_product_expiry"


def task1226_trade_specs(base_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    cooling_until: dict[str, date] = {}
    for row in sorted(base_rows, key=lambda item: (str(item["decision_asof_ts"]), int(str(item["candidate_rank"])))):
        decision_date = datetime.fromisoformat(str(row["decision_asof_ts"]).replace("Z", "+00:00")).date()
        symbol = str(row["symbol"])
        blocked = symbol in cooling_until and decision_date < cooling_until[symbol]
        entry_price = to_float(row["entry_price"])
        product = row["product_sleeve"] != "ordinary_equity"
        adjusted_exit_date, adjusted_exit_price, exit_reason = stop_exit(
            symbol,
            str(row["entry_date"]),
            str(row["exit_date"]),
            entry_price,
            product,
        )
        net_return = adjusted_exit_price / entry_price - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if entry_price > 0 else 0.0
        if exit_reason in {"entry_drawdown_stop", "peak_drawdown_stop"}:
            cooling_until[symbol] = datetime.fromisoformat(adjusted_exit_date).date() + timedelta(days=62)
        multiplier = 0.0 if blocked else float(row["position_multiplier"])
        rows.append(
            {
                "task_id": "Task1226",
                "collapse_trade_spec_id": f"L5COL1226-{len(rows)+1:06d}",
                "selection_id": row["selection_id"],
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": symbol,
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "risk_bucket": row["risk_bucket"],
                "product_sleeve": row["product_sleeve"],
                "entry_date": row["entry_date"],
                "entry_price": entry_price,
                "scheduled_exit_date": row["exit_date"],
                "scheduled_exit_price": row["exit_price"],
                "adjusted_exit_date": adjusted_exit_date,
                "adjusted_exit_price": round(adjusted_exit_price, 6),
                "exit_reason": "reentry_cooling_block" if blocked else exit_reason,
                "position_multiplier": multiplier,
                "diagnostic_net_return": round(net_return, 8) if not blocked else 0.0,
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
            if allocation <= 0:
                trades.append(
                    {
                        "task_id": "Task1227",
                        "policy_variant_id": POLICY_VARIANT,
                        "trade_id": f"TRADE1227-{len(trades)+1:07d}",
                        **item,
                        "capital_allocated": 0.0,
                        "pnl": 0.0,
                        "net_return": 0.0,
                    }
                )
                continue
            entry = float(item["entry_price"])
            exit_ = float(item["adjusted_exit_price"])
            net_return = exit_ / entry - 1.0 - ROUND_TRIP_COST_BPS / 10000.0
            pnl = allocation * net_return
            period_pnl += pnl
            new_capital += pnl
            trades.append(
                {
                    "task_id": "Task1227",
                    "policy_variant_id": POLICY_VARIANT,
                    "trade_id": f"TRADE1227-{len(trades)+1:07d}",
                    **item,
                    "capital_allocated": round(allocation, 4),
                    "pnl": round(pnl, 4),
                    "net_return": round(net_return, 8),
                }
            )
        cash_weight = max(0.0, 1.0 - invested / capital) if capital > 0 else 0.0
        period_return = new_capital / capital - 1.0 if capital > 0 else 0.0
        capital = max(new_capital, 0.01)
        equity.append(
            {
                "task_id": "Task1227",
                "policy_variant_id": POLICY_VARIANT,
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_return": round(period_return, 8),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(items),
                "cash_weight_after_risk_buckets": round(cash_weight, 6),
                "authority": AUTHORITY,
            }
        )
    return trades, equity


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


def metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = read_csv(TASK1201 / "task1207_replay_metrics.csv")
    base_slot5 = next(row for row in base_metrics if row["policy_variant_id"] == BASE_VARIANT)
    start = datetime.fromisoformat(str(equity[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
    end = max(datetime.fromisoformat(str(row["adjusted_exit_date"])).date() for row in trades)
    values = [INITIAL_CAPITAL] + [float(row["equity"]) for row in equity]
    final = values[-1]
    executed = [row for row in trades if float(row["capital_allocated"]) > 0]
    wins = sum(1 for row in executed if float(row["net_return"]) > 0)
    row = {
        "task_id": "Task1227",
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
    return [row]


def acceptance_gate(metric_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    row = metric_rows[0]
    return [
        {
            "task_id": "Task1227",
            "acceptance_gate_id": "ACCEPT1227-001",
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


def write_report(closeout: dict[str, object], metric_row: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1221_1227_collapse_guard_implementation.md"
    lines = [
        "# Task1221-1227 Collapse Guard Implementation",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Policy variant: `{metric_row['policy_variant_id']}`.",
        f"- Final equity: {metric_row['final_equity']}.",
        f"- CAGR: {metric_row['cagr']}.",
        f"- MDD: {metric_row['max_drawdown']}.",
        f"- Base slot5 final equity: {metric_row['base_slot5_final_equity']}.",
        f"- Beats base slot5: {metric_row['beats_base_slot5']}.",
        f"- QQQ final equity: {metric_row['benchmark_final_equity']}.",
        f"- Beats QQQ: {metric_row['beats_benchmark']}.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This task implements the Task1211-1220 collapse guard as a diagnostic controlled comparison.",
        "",
        "Implemented controls:",
        "",
        "- Public-filer proxy listing and identity adapter.",
        "- Distress panel using only decision-time price path, volatility, liquidity, and SEC event density fields.",
        "- Product classifier that allows leverage but routes complex products to smaller and shorter handling.",
        "- L3 relation edges that pass, condition, weaken, or route candidates.",
        "- L4 collapse-aware candidate card fields.",
        "- L5 risk-bucket sizing, drawdown exits, product-sleeve shortened holding, and reentry cooling.",
        "",
        "Limitations:",
        "",
        "- Raw text extraction for going concern and dilution is not yet implemented.",
        "- True exchange historical PIT listing remains incomplete.",
        "- This is diagnostic evidence only and cannot accept the strategy.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We tested whether a collapse guard can reduce near-zero tail risk without banning leverage.",
        "",
        "The result is diagnostic only.",
        "",
        "## Artifact Manifest",
        "",
        "- `task1221_listing_corporate_action_adapter.csv`",
        "- `task1222_distress_evidence_panel.csv`",
        "- `task1223_product_structure_classifier.csv`",
        "- `task1224_l3_collapse_relation_edges.csv`",
        "- `task1225_l4_collapse_candidate_cards.csv`",
        "- `task1226_l5_collapse_guard_trade_specs.csv`",
        "- `task1227_collapse_guard_replay_trades.csv`",
        "- `task1227_collapse_guard_replay_equity.csv`",
        "- `task1227_collapse_guard_metrics.csv`",
        "- `task1227_collapse_guard_acceptance_gate.csv`",
        "- `task1227_collapse_guard_closeout.csv/json`",
        "- `artifact_manifest.csv`",
        "",
        "Validation commands:",
        "",
        "- `python scripts/trader_brain_1221_1227_collapse_guard_implementation_validate.py`",
        "- `python -m unittest tests.test_trader_brain_1221_1227_collapse_guard_implementation`",
        "",
        "```text",
        "Test results do not modify strategy acceptance status.",
        "Strategy: NOT_ACCEPTED",
        "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "Real Capital: FORBIDDEN",
        "```",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1221_1227_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    base_rows = build_base_rows()
    rows1221 = task1221_listing_adapter(base_rows)
    rows1222 = task1222_distress_panel(base_rows)
    rows1223 = task1223_product_classifier(base_rows)
    rows1224 = task1224_relation_edges(base_rows)
    rows1225 = task1225_l4_cards(base_rows)
    rows1226 = task1226_trade_specs(base_rows)
    trades, equity = run_replay(rows1226)
    metric_rows = metrics(trades, equity)
    gate = acceptance_gate(metric_rows)
    metric = metric_rows[0]
    closeout = {
        "task_id": "Task1221-1227",
        "verdict": "collapse_guard_controlled_replay_executed_not_accepted",
        "policy_variant_id": POLICY_VARIANT,
        "base_selection_rows": len(base_rows),
        "listing_adapter_rows": len(rows1221),
        "distress_panel_rows": len(rows1222),
        "product_classifier_rows": len(rows1223),
        "l3_edge_rows": len(rows1224),
        "l4_card_rows": len(rows1225),
        "l5_trade_spec_rows": len(rows1226),
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
        "next_action": "review_collapse_guard_trade_attribution_and_add_raw_text_going_concern_dilution_extractors",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1221_listing_corporate_action_adapter.csv", rows1221)
    write_csv(OUT_DIR / "task1222_distress_evidence_panel.csv", rows1222)
    write_csv(OUT_DIR / "task1223_product_structure_classifier.csv", rows1223)
    write_csv(OUT_DIR / "task1224_l3_collapse_relation_edges.csv", rows1224)
    write_csv(OUT_DIR / "task1225_l4_collapse_candidate_cards.csv", rows1225)
    write_csv(OUT_DIR / "task1226_l5_collapse_guard_trade_specs.csv", rows1226)
    write_csv(OUT_DIR / "task1227_collapse_guard_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1227_collapse_guard_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1227_collapse_guard_metrics.csv", metric_rows)
    write_csv(OUT_DIR / "task1227_collapse_guard_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1227_collapse_guard_closeout.csv", [closeout])
    write_json(OUT_DIR / "task1227_collapse_guard_closeout.json", closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    write_report(closeout, metric)
    print(
        "[TRADER_BRAIN_1221_1227_COLLAPSE_GUARD_IMPLEMENTATION_OK] "
        f"final={metric['final_equity']} cagr={metric['cagr']} mdd={metric['max_drawdown']} "
        f"beats_base={metric['beats_base_slot5']} beats_qqq={metric['beats_benchmark']} trades={len(trades)}"
    )


if __name__ == "__main__":
    main()
