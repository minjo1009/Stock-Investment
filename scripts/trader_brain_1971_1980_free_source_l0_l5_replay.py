from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import trader_brain_1408_1427_ruler_acquisition_replay as replay
import trader_brain_1951_1960_source_receipt_and_ablation as receipt
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1788 = ROOT / "data/artifacts/task_1788_1807_winner_defense_budget"
TASK1808 = ROOT / "data/artifacts/task_1808_1827_sleeve_split_playbook"
TASK1951 = ROOT / "data/artifacts/task_1951_1960_source_receipt_and_ablation"
TASK1961 = ROOT / "data/artifacts/task_1961_1970_free_source_acquisition"
RAW1961 = ROOT / "data/raw/task_1961_1970_free_source_acquisition"
OUT_DIR = ROOT / "data/artifacts/task_1971_1980_free_source_l0_l5_replay"
REPORT_DIR = ROOT / "docs/reports/task_1971_1980_free_source_l0_l5_replay"
REPORT = REPORT_DIR / "task_1971_1980_free_source_l0_l5_replay.md"
DECISION = REPORT_DIR / "task_1971_1980_decision.csv"
AUTHORITY = "DIAGNOSTIC_FREE_SOURCE_L0_L5_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
QQQ_BENCHMARK_FINAL = 1847.0265
CERTIFIED_FRED_SERIES = {"DGS2", "DGS10", "DFF", "VIXCLS", "BAMLH0A0HYM2"}


def read_csv(path: Path) -> list[dict[str, str]]:
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
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in {"", None, "nan", "."}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_date(value: object) -> date | None:
    try:
        if value in {"", None}:
            return None
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def parse_ts(value: object) -> datetime | None:
    try:
        if value in {"", None}:
            return None
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def load_inputs() -> dict[str, object]:
    return {
        "budget": read_csv(TASK1808 / "task1815_sleeve_risk_budget.csv"),
        "winner_trades": read_csv(TASK1788 / "task1792_winner_defense_replay_trades.csv"),
        "sleeve_metrics": read_csv(TASK1808 / "task1823_sleeve_replay_metrics.csv"),
        "receipt_l4": read_csv(TASK1951 / "task1957_source_receipt_hardened_l4.csv"),
        "receipt_metrics": read_csv(TASK1951 / "task1958_source_receipt_top3_replay_metrics.csv"),
        "free_scope": read_csv(TASK1961 / "task1961_free_source_scope_manifest.csv"),
        "alfred_ledger": read_csv(TASK1961 / "task1962_alfred_fred_acquisition_ledger.csv"),
        "price_coverage": read_csv(TASK1961 / "task1964_price_free_source_coverage.csv"),
        "sec_guidance": read_csv(TASK1961 / "task1965_sec_guidance_expanded_receipt_ledger.csv"),
        "price_norm": read_csv(RAW1961 / "yahoo_chart_daily_normalized.csv"),
    }


def input_manifest_rows() -> list[dict[str, object]]:
    inputs = [
        ("receipt_l4", TASK1951 / "task1957_source_receipt_hardened_l4.csv"),
        ("receipt_replay_metrics", TASK1951 / "task1958_source_receipt_top3_replay_metrics.csv"),
        ("free_source_scope", TASK1961 / "task1961_free_source_scope_manifest.csv"),
        ("alfred_fred_ledger", TASK1961 / "task1962_alfred_fred_acquisition_ledger.csv"),
        ("price_coverage", TASK1961 / "task1964_price_free_source_coverage.csv"),
        ("sec_guidance_expanded", TASK1961 / "task1965_sec_guidance_expanded_receipt_ledger.csv"),
        ("yahoo_price_normalized", RAW1961 / "yahoo_chart_daily_normalized.csv"),
    ]
    return [
        {
            "task_id": "Task1971",
            "input_id": f"FREEL0L5INPUT-1971-{idx:03d}",
            "input_name": name,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "exists": "1" if path.exists() else "0",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "authority": AUTHORITY,
        }
        for idx, (name, path) in enumerate(inputs, 1)
    ]


def fred_vintage_index(alfred_ledger: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    series_paths = {
        row["series_id"]: ROOT / row["observations_raw_path"]
        for row in alfred_ledger
        if row.get("alfred_vintage_certified") == "1" and row.get("series_id") in CERTIFIED_FRED_SERIES and row.get("observations_raw_path")
    }
    out: dict[str, list[dict[str, object]]] = {}
    for series, path in series_paths.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = []
        for item in payload.get("observations", []):
            obs_date = parse_date(item.get("date"))
            realtime_start = parse_date(item.get("realtime_start"))
            realtime_end = parse_date(item.get("realtime_end"))
            value = to_float(item.get("value"), default=float("nan"))
            if obs_date is None or realtime_start is None or realtime_end is None or value != value:
                continue
            rows.append(
                {
                    "series_id": series,
                    "observation_date": obs_date,
                    "realtime_start": realtime_start,
                    "realtime_end": realtime_end,
                    "value": value,
                }
            )
        out[series] = rows
    return out


def value_asof(index: dict[str, list[dict[str, object]]], series: str, decision_day: date) -> tuple[float | None, str]:
    rows = [
        row
        for row in index.get(series, [])
        if row["observation_date"] <= decision_day and row["realtime_start"] <= decision_day <= row["realtime_end"]
    ]
    if not rows:
        return None, ""
    row = max(rows, key=lambda item: item["observation_date"])
    return float(row["value"]), row["observation_date"].isoformat()


def macro_l1_rows(inputs: dict[str, object]) -> list[dict[str, object]]:
    fred = fred_vintage_index(inputs["alfred_ledger"])
    decisions = sorted({row["decision_asof_ts"] for row in inputs["receipt_l4"]})
    rows = []
    for idx, decision_ts in enumerate(decisions, 1):
        d = parse_date(decision_ts)
        values = {}
        dates = {}
        if d:
            for series in sorted(CERTIFIED_FRED_SERIES):
                value, obs_date = value_asof(fred, series, d)
                values[series] = value
                dates[series] = obs_date
        dgs2 = values.get("DGS2")
        dgs10 = values.get("DGS10")
        dff = values.get("DFF")
        vix = values.get("VIXCLS")
        hy = values.get("BAMLH0A0HYM2")
        certified_count = sum(1 for value in values.values() if value is not None)
        if certified_count >= 4 and ((dgs2 and dgs2 >= 4.0) or (dgs10 and dgs10 >= 4.0) or (dff and dff >= 4.0)):
            rate_state = "vintage_tight_rate_headwind"
        elif certified_count >= 4 and ((dgs2 and dgs2 < 1.5) and (dgs10 and dgs10 < 2.5)):
            rate_state = "vintage_easy_rate_tailwind"
        else:
            rate_state = "vintage_neutral_or_mixed"
        if certified_count >= 4 and ((vix and vix >= 28.0) or (hy and hy >= 5.0)):
            liquidity_state = "vintage_liquidity_stress"
        elif certified_count >= 4 and ((vix and vix < 22.0) and (hy and hy < 4.5)):
            liquidity_state = "vintage_liquidity_support"
        else:
            liquidity_state = "vintage_liquidity_neutral_or_mixed"
        rows.append(
            {
                "task_id": "Task1972",
                "macro_l1_id": f"FREEMACROL1-1972-{idx:05d}",
                "decision_asof_ts": decision_ts,
                "certified_fred_series_count": certified_count,
                "DGS2_value": values.get("DGS2", ""),
                "DGS2_observation_date": dates.get("DGS2", ""),
                "DGS10_value": values.get("DGS10", ""),
                "DGS10_observation_date": dates.get("DGS10", ""),
                "DFF_value": values.get("DFF", ""),
                "DFF_observation_date": dates.get("DFF", ""),
                "VIXCLS_value": values.get("VIXCLS", ""),
                "VIXCLS_observation_date": dates.get("VIXCLS", ""),
                "BAMLH0A0HYM2_value": values.get("BAMLH0A0HYM2", ""),
                "BAMLH0A0HYM2_observation_date": dates.get("BAMLH0A0HYM2", ""),
                "macro_rate_state": rate_state,
                "macro_liquidity_state": liquidity_state,
                "macro_assignment_permission": "active_small_adjustment_certified_fred_only" if certified_count >= 4 else "shadow_or_gap",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l0_admission_rows(inputs: dict[str, object], macro_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    price_ok = {row["symbol"]: row for row in inputs["price_coverage"] if row["download_state"] == "downloaded_json_normalized"}
    macro_by_decision = {row["decision_asof_ts"]: row for row in macro_rows}
    sec_by_spec = group_sec(inputs["sec_guidance"])
    rows = []
    for idx, l4 in enumerate(inputs["receipt_l4"], 1):
        sec_rows = sec_by_spec.get(l4["trade_spec_id"], [])
        macro = macro_by_decision.get(l4["decision_asof_ts"], {})
        state = "l0_free_source_pass" if l4["symbol"] in price_ok and macro.get("macro_assignment_permission") != "shadow_or_gap" and sec_rows else "l0_source_gap_review"
        rows.append(
            {
                "task_id": "Task1971",
                "l0_admission_id": f"FREEL0-1971-{idx:06d}",
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "price_crosscheck_available": "1" if l4["symbol"] in price_ok else "0",
                "sec_guidance_packet_count": len(sec_rows),
                "macro_certified_fred_series_count": macro.get("certified_fred_series_count", "0"),
                "l0_free_source_state": state,
                "missing_source_semantics": "gap_not_negative",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def group_sec(sec_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in sec_rows:
        grouped[row["trade_spec_id"]].append(row)
    return grouped


def price_index(price_rows: list[dict[str, str]]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in price_rows:
        d = parse_date(row.get("date"))
        adj = to_float(row.get("adjclose"))
        volume = to_float(row.get("volume"))
        if d is None or adj <= 0:
            continue
        grouped[row["symbol"].upper()].append({"date": d, "adjclose": adj, "volume": volume})
    for rows in grouped.values():
        rows.sort(key=lambda item: item["date"])
    return grouped


def price_features(index: dict[str, list[dict[str, object]]], symbol: str, decision_day: date | None) -> dict[str, object]:
    if decision_day is None:
        return {"state": "price_crosscheck_gap"}
    rows = [row for row in index.get(symbol.upper(), []) if row["date"] <= decision_day]
    if len(rows) < 64:
        return {"state": "price_crosscheck_gap"}
    last = rows[-1]
    prior21 = rows[-22] if len(rows) >= 22 else rows[0]
    prior63 = rows[-64]
    window = rows[-126:] if len(rows) >= 126 else rows
    max_close = max(to_float(row["adjclose"]) for row in window)
    drawdown = last["adjclose"] / max_close - 1.0 if max_close > 0 else 0.0
    ret21 = last["adjclose"] / prior21["adjclose"] - 1.0
    ret63 = last["adjclose"] / prior63["adjclose"] - 1.0
    avg_vol20 = sum(to_float(row["volume"]) for row in rows[-20:]) / min(20, len(rows))
    avg_vol63 = sum(to_float(row["volume"]) for row in rows[-63:]) / min(63, len(rows))
    if ret63 > 0.08 and ret21 > -0.05 and drawdown > -0.22:
        state = "raw_price_sustained_acceptance"
    elif ret63 < -0.10 or drawdown < -0.30:
        state = "raw_price_rejection_or_air_pocket"
    else:
        state = "raw_price_neutral_or_mixed"
    return {
        "state": state,
        "return_21d": round(ret21, 6),
        "return_63d": round(ret63, 6),
        "drawdown_126d": round(drawdown, 6),
        "volume_ratio_20d_63d": round(avg_vol20 / avg_vol63, 6) if avg_vol63 > 0 else "",
        "last_price_date": last["date"].isoformat(),
    }


def l2_rows(inputs: dict[str, object], macro_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    macro_by_decision = {row["decision_asof_ts"]: row for row in macro_rows}
    sec_by_spec = group_sec(inputs["sec_guidance"])
    prices = price_index(inputs["price_norm"])
    rows = []
    for idx, l4 in enumerate(inputs["receipt_l4"], 1):
        sec_rows = sec_by_spec.get(l4["trade_spec_id"], [])
        hit_rows = [row for row in sec_rows if row["guidance_receipt_state"] == "issuer_public_guidance_hit_asof"]
        families = set()
        for row in hit_rows:
            families.update([part for part in row.get("guidance_keyword_families", "").split("|") if part and part != "none"])
        if {"guidance", "outlook", "raises", "backlog"} & families:
            guidance_state = "issuer_guidance_specific_support"
        elif {"contract", "customer", "revenue", "expects"} & families:
            guidance_state = "issuer_guidance_broad_support"
        elif sec_rows:
            guidance_state = "issuer_guidance_no_hit_or_weak"
        else:
            guidance_state = "issuer_guidance_source_gap"
        price = price_features(prices, l4["symbol"], parse_date(l4["decision_asof_ts"]))
        macro = macro_by_decision.get(l4["decision_asof_ts"], {})
        rows.append(
            {
                "task_id": "Task1973",
                "l2_semantic_id": f"FREEL2-1973-{idx:06d}",
                "trade_spec_id": l4["trade_spec_id"],
                "candidate_source_id": l4["candidate_source_id"],
                "symbol": l4["symbol"],
                "decision_asof_ts": l4["decision_asof_ts"],
                "strategy_sleeve": l4["strategy_sleeve"],
                "macro_rate_state": macro.get("macro_rate_state", "macro_gap"),
                "macro_liquidity_state": macro.get("macro_liquidity_state", "macro_gap"),
                "macro_assignment_permission": macro.get("macro_assignment_permission", "shadow_or_gap"),
                "issuer_guidance_state": guidance_state,
                "issuer_guidance_hit_packet_count": len(hit_rows),
                "issuer_guidance_keyword_families": "|".join(sorted(families)) if families else "none",
                "price_crosscheck_state": price.get("state", "price_crosscheck_gap"),
                "price_return_21d": price.get("return_21d", ""),
                "price_return_63d": price.get("return_63d", ""),
                "price_drawdown_126d": price.get("drawdown_126d", ""),
                "price_volume_ratio_20d_63d": price.get("volume_ratio_20d_63d", ""),
                "last_price_date": price.get("last_price_date", ""),
                "analyst_revision_certified": "0",
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def l3_rows(l2: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    idx = 1
    for row in l2:
        primitives = []
        if row["issuer_guidance_state"] in {"issuer_guidance_specific_support", "issuer_guidance_broad_support"}:
            primitives.append(("issuer_guidance_supports_thesis", "supports", "issuer_public_sec_guidance"))
        if row["price_crosscheck_state"] == "raw_price_sustained_acceptance":
            primitives.append(("raw_price_acceptance_confirms_information", "supports", "free_public_price_crosscheck"))
        elif row["price_crosscheck_state"] == "raw_price_rejection_or_air_pocket":
            primitives.append(("raw_price_rejection_caps_payoff", "caps", "free_public_price_crosscheck"))
        if row["macro_rate_state"] == "vintage_tight_rate_headwind":
            primitives.append(("vintage_macro_tightening_offsets_duration_growth", "caps", "alfred_fred_vintage"))
        elif row["macro_rate_state"] == "vintage_easy_rate_tailwind":
            primitives.append(("vintage_macro_easing_supports_duration_growth", "supports", "alfred_fred_vintage"))
        if row["macro_liquidity_state"] == "vintage_liquidity_stress":
            primitives.append(("vintage_liquidity_stress_raises_drawdown_risk", "caps", "alfred_fred_vintage"))
        elif row["macro_liquidity_state"] == "vintage_liquidity_support":
            primitives.append(("vintage_liquidity_supports_risk_taking", "supports", "alfred_fred_vintage"))
        if not primitives:
            primitives.append(("free_source_no_new_relation", "neutral", "source_gap_or_neutral"))
        for primitive, relation, source_family in primitives:
            rows.append(
                {
                    "task_id": "Task1974",
                    "l3_edge_id": f"FREEL3-1974-{idx:07d}",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "relation_primitive": primitive,
                    "relation_direction": relation,
                    "source_family": source_family,
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def l4_rows(inputs: dict[str, object], l2: list[dict[str, object]], l3: list[dict[str, object]]) -> list[dict[str, object]]:
    l2_by_spec = {row["trade_spec_id"]: row for row in l2}
    edge_by_spec = defaultdict(list)
    for edge in l3:
        edge_by_spec[edge["trade_spec_id"]].append(edge)
    rows = []
    for idx, base in enumerate(inputs["receipt_l4"], 1):
        sem = l2_by_spec[base["trade_spec_id"]]
        score = to_float(base["source_receipt_interaction_score"])
        guidance_adj = 0.0
        # Yahoo public chart data is a diagnostic cross-check only, not an original as-of receipt.
        price_adj = 0.0
        macro_adj = 0.0
        if sem["issuer_guidance_state"] == "issuer_guidance_specific_support":
            guidance_adj = 0.08
        elif sem["issuer_guidance_state"] == "issuer_guidance_broad_support":
            guidance_adj = 0.03
        elif sem["issuer_guidance_state"] == "issuer_guidance_no_hit_or_weak":
            guidance_adj = -0.04
        if sem["price_crosscheck_state"] in {"raw_price_sustained_acceptance", "raw_price_rejection_or_air_pocket"}:
            price_adj = 0.0
        if sem["macro_assignment_permission"] == "active_small_adjustment_certified_fred_only":
            if sem["macro_rate_state"] == "vintage_tight_rate_headwind" and base["strategy_sleeve"] in {"winner_compounder", "software_ai", "semiconductor_ai"}:
                macro_adj -= 0.12
            elif sem["macro_rate_state"] == "vintage_easy_rate_tailwind" and base["strategy_sleeve"] in {"winner_compounder", "software_ai", "semiconductor_ai"}:
                macro_adj += 0.08
            if sem["macro_liquidity_state"] == "vintage_liquidity_stress":
                macro_adj -= 0.10
            elif sem["macro_liquidity_state"] == "vintage_liquidity_support":
                macro_adj += 0.05
        final_score = score + guidance_adj + price_adj + macro_adj
        if final_score >= 2.5:
            state = "free_source_high_conviction_payoff"
            mult = 1.06
        elif final_score >= 1.5:
            state = "free_source_positive_payoff"
            mult = 1.03
        elif final_score >= 0.5:
            state = "free_source_ordinary_pass"
            mult = 1.0
        elif final_score <= -1.2:
            state = "free_source_risk_cap"
            mult = 0.72
        elif final_score < 0:
            state = "free_source_watch_trim"
            mult = 0.90
        else:
            state = "free_source_neutral_watch"
            mult = 0.97
        rows.append(
            {
                "task_id": "Task1975",
                "l4_card_id": f"FREEL4-1975-{idx:06d}",
                "target_policy_variant_id": base["target_policy_variant_id"],
                "trade_spec_id": base["trade_spec_id"],
                "candidate_source_id": base["candidate_source_id"],
                "symbol": base["symbol"],
                "decision_asof_ts": base["decision_asof_ts"],
                "strategy_sleeve": base["strategy_sleeve"],
                "prior_source_receipt_score": base["source_receipt_interaction_score"],
                "free_source_guidance_adjustment": round(guidance_adj, 4),
                "free_source_price_adjustment": round(price_adj, 4),
                "price_crosscheck_score_permission": "audit_only_not_assignment",
                "free_source_macro_adjustment": round(macro_adj, 4),
                "free_source_l4_score": round(final_score, 4),
                "free_source_l5_budget_multiplier": mult,
                "free_source_thesis_state": state,
                "relation_edge_count": len(edge_by_spec[base["trade_spec_id"]]),
                "assignment_uses_future_outcome": "0",
                "outcome_used_for_assignment": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def replay_top3(inputs: dict[str, object], l4: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    l4_by_spec = {row["trade_spec_id"]: row for row in l4}
    source_trades = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in inputs["winner_trades"]}
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in inputs["budget"]:
        if row["target_policy_variant_id"] == "winner_defense_budget_top3_v1":
            grouped[row["decision_asof_ts"]].append(row)
    capital = INITIAL_CAPITAL
    trades = []
    equity = []
    trade_idx = 1
    for decision_ts in sorted(grouped):
        rows = sorted(grouped[decision_ts], key=lambda row: to_float(l4_by_spec[row["trade_spec_id"]]["free_source_l4_score"]), reverse=True)
        base_alloc = capital / 3.0
        period_pnl = 0.0
        allocated = 0
        for row in rows:
            src = source_trades.get(("winner_defense_budget_top3_v1", row["trade_spec_id"]))
            card = l4_by_spec.get(row["trade_spec_id"])
            if not src or not card:
                continue
            mult = clamp(to_float(row["sleeve_budget_multiplier"]) * to_float(card["free_source_l5_budget_multiplier"]), 0.0, 1.22)
            if mult <= 0:
                continue
            cap_alloc = base_alloc * mult
            pnl = cap_alloc * to_float(src["net_return"])
            capital += pnl
            period_pnl += pnl
            allocated += 1
            trades.append(
                {
                    "task_id": "Task1976",
                    "trade_row_id": f"FREEREPLAY-1976-{trade_idx:07d}",
                    "policy_variant_id": "free_source_l0_l5_top3_v1",
                    "source_policy_variant_id": "winner_defense_budget_top3_v1",
                    "trade_spec_id": row["trade_spec_id"],
                    "candidate_source_id": row["candidate_source_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "strategy_sleeve": row["strategy_sleeve"],
                    "free_source_thesis_state": card["free_source_thesis_state"],
                    "free_source_l4_score": card["free_source_l4_score"],
                    "free_source_l5_multiplier": card["free_source_l5_budget_multiplier"],
                    "base_sleeve_budget_multiplier": row["sleeve_budget_multiplier"],
                    "final_budget_multiplier": round(mult, 6),
                    "source_net_return": src.get("net_return", ""),
                    "capital_allocated": round(cap_alloc, 4),
                    "pnl": round(pnl, 4),
                    "net_return": src.get("net_return", ""),
                    "entry_date": src.get("entry_date", ""),
                    "actual_exit_date": src.get("actual_exit_date", ""),
                    "assignment_uses_future_outcome": "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            trade_idx += 1
        equity.append(
            {
                "task_id": "Task1976",
                "policy_variant_id": "free_source_l0_l5_top3_v1",
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_pnl": round(period_pnl, 4),
                "selected_count": len(rows),
                "allocated_count": allocated,
                "authority": AUTHORITY,
            }
        )
    return trades, equity


def metric_rows(inputs: dict[str, object], trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    sleeve = {row["policy_variant_id"]: row for row in inputs["sleeve_metrics"]}["sleeve_split_top3_v1"]
    previous = inputs["receipt_metrics"][0]
    values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in equity]
    final = values[-1]
    start = replay.parse_ts(str(equity[0]["decision_asof_ts"])).date()
    end_dates = [parse_date(row.get("actual_exit_date")) for row in trades]
    end = max([d for d in end_dates if d is not None] or [start])
    years = max((end - start).days / 365.25, 1 / 365.25)
    cagr = final ** (1 / years) / (INITIAL_CAPITAL ** (1 / years)) - 1.0
    mdd = replay.max_drawdown(values)
    return [
        {
            "task_id": "Task1976",
            "policy_variant_id": "free_source_l0_l5_top3_v1",
            "baseline_policy_variant_id": "sleeve_split_top3_v1",
            "previous_policy_variant_id": "source_receipt_hardened_top3_v1",
            "initial_capital": INITIAL_CAPITAL,
            "final_equity": round(final, 4),
            "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
            "cagr": round(cagr, 6),
            "max_drawdown": round(mdd, 6),
            "trade_count": len(trades),
            "baseline_final_equity": sleeve["final_equity"],
            "baseline_cagr": sleeve["cagr"],
            "baseline_max_drawdown": sleeve["max_drawdown"],
            "previous_final_equity": previous["final_equity"],
            "previous_cagr": previous["cagr"],
            "previous_max_drawdown": previous["max_drawdown"],
            "delta_vs_previous_final_equity": round(final - to_float(previous["final_equity"]), 4),
            "delta_vs_baseline_final_equity": round(final - to_float(sleeve["final_equity"]), 4),
            "beats_qqq": "1" if final > QQQ_BENCHMARK_FINAL else "0",
            "target_cagr_30pct_met": "1" if cagr >= 0.30 else "0",
            "target_mdd_minus30pct_met": "1" if mdd >= -0.30 else "0",
            "joint_target_met": "1" if cagr >= 0.30 and mdd >= -0.30 and final > QQQ_BENCHMARK_FINAL else "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "assignment_uses_future_outcome": "0",
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
    ]


def split_rows(equity: list[dict[str, object]]) -> list[dict[str, object]]:
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in equity:
        d = replay.parse_ts(str(row["decision_asof_ts"])).date()
        groups["IS_2021_2023" if d.year <= 2023 else "OOS_2024_2026Q1"].append(row)
    rows = []
    for idx, (window, items) in enumerate(sorted(groups.items()), 1):
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in items]
        rows.append(
            {
                "task_id": "Task1976",
                "split_id": f"FREESPLIT-1976-{idx:03d}",
                "policy_variant_id": "free_source_l0_l5_top3_v1",
                "split_window": window,
                "period_count": len(items),
                "split_final_equity": round(values[-1], 4),
                "split_total_return": round(values[-1] / INITIAL_CAPITAL - 1.0, 6),
                "split_max_drawdown": round(replay.max_drawdown(values), 6),
                "authority": AUTHORITY,
            }
        )
    return rows


def cost_rows(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    metric = metrics[0]
    rows = []
    for idx, bps in enumerate([0, 25, 50, 100], 1):
        haircut = int(metric["trade_count"]) * (bps / 10000.0) * 0.35
        stressed = to_float(metric["final_equity"]) * max(0.0, 1.0 - haircut)
        rows.append(
            {
                "task_id": "Task1976",
                "cost_stress_id": f"FREECOST-1976-{idx:03d}",
                "policy_variant_id": "free_source_l0_l5_top3_v1",
                "round_trip_cost_bps": bps,
                "approx_trade_count": metric["trade_count"],
                "stressed_final_equity": round(stressed, 4),
                "beats_qqq_after_stress": "1" if stressed > QQQ_BENCHMARK_FINAL else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def attribution_rows(l2: list[dict[str, object]], l4: list[dict[str, object]], trades: list[dict[str, object]]) -> list[dict[str, object]]:
    l2_by_spec = {row["trade_spec_id"]: row for row in l2}
    l4_by_spec = {row["trade_spec_id"]: row for row in l4}
    rows = []
    for idx, family in enumerate(["macro", "issuer_guidance", "price_crosscheck"], 1):
        pnl = 0.0
        count = 0
        adjusted = 0
        for trade in trades:
            card = l4_by_spec[trade["trade_spec_id"]]
            sem = l2_by_spec[trade["trade_spec_id"]]
            include = False
            adj = 0.0
            if family == "macro":
                adj = to_float(card["free_source_macro_adjustment"])
                include = adj != 0.0
            elif family == "issuer_guidance":
                adj = to_float(card["free_source_guidance_adjustment"])
                include = sem["issuer_guidance_state"] != "issuer_guidance_source_gap"
            elif family == "price_crosscheck":
                adj = to_float(card["free_source_price_adjustment"])
                include = sem["price_crosscheck_state"] != "price_crosscheck_gap"
            if include:
                count += 1
                pnl += to_float(trade["pnl"])
                if adj != 0:
                    adjusted += 1
        rows.append(
            {
                "task_id": "Task1977",
                "attribution_id": f"FREEATTR-1977-{idx:03d}",
                "source_family": family,
                "top3_trade_count_audit_only": count,
                "adjusted_trade_count": adjusted,
                "pnl_sum_audit_only": round(pnl, 4),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def expert_audit_rows() -> list[dict[str, object]]:
    findings = [
        ("macro_desk", "ALFRED/FRED vintage may move from shadow to small active adjustment only for downloaded FRED series.", "implemented"),
        ("equity_fundamental_desk", "SEC issuer guidance is issuer-public support, not analyst consensus surprise.", "implemented"),
        ("market_microstructure_desk", "Yahoo public chart data is cross-check only, not original broker/market receipt.", "implemented"),
        ("backtest_infra", "Replay must reuse frozen trade returns and avoid new price matching.", "implemented"),
        ("governance", "No diagnostic result can change acceptance or deployment state.", "implemented"),
        ("subagent_source_audit", "External explorer audit required Yahoo price to remain audit-only and warned against analyst surprise substitution.", "implemented"),
    ]
    return [
        {
            "task_id": "Task1978",
            "expert_audit_id": f"FREEEXPERT-1978-{idx:03d}",
            "reviewer_role": role,
            "finding": finding,
            "implementation_state": state,
            "authority": AUTHORITY,
        }
        for idx, (role, finding, state) in enumerate(findings, 1)
    ]


def closeout_rows(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    metric = metrics[0]
    gate = [
        {
            "task_id": "Task1980",
            "gate_id": "FREEL0L5GATE-1980-001",
            "policy_variant_id": metric["policy_variant_id"],
            "diagnostic_joint_target_met": metric["joint_target_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "reason": "diagnostic_free_source_l0_l5_replay_not_acceptance_contract",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1980",
            "verdict": "free_source_l0_l5_replay_complete_diagnostic_only",
            "best_policy_variant_id": metric["policy_variant_id"],
            "best_final_equity": metric["final_equity"],
            "best_cagr": metric["cagr"],
            "best_max_drawdown": metric["max_drawdown"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "next_required_action": "audit whether free-source adjustments improve source logic or only add noise before any policy promotion",
            "authority": AUTHORITY,
        }
    ]
    return gate, closeout


def write_report(metrics: list[dict[str, object]], splits: list[dict[str, object]], attribution: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    metric = metrics[0]
    lines = [
        "# Task1971-1980 Free Source L0-L5 Replay",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        f"- Policy: `{metric['policy_variant_id']}`.",
        f"- Final equity: {metric['final_equity']}.",
        f"- CAGR: {metric['cagr']}.",
        f"- MDD: {metric['max_drawdown']}.",
        f"- Delta vs Task1951-1960 source-receipt replay: {metric['delta_vs_previous_final_equity']}.",
        f"- Delta vs sleeve baseline: {metric['delta_vs_baseline_final_equity']}.",
        "- ALFRED/FRED vintage is active only as small adjustment for downloaded FRED series.",
        "- SEC issuer guidance is support-only and does not certify analyst surprise.",
        "- Yahoo price data is cross-check-only, not original as-of market receipt.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Data flow:",
        "",
        "- L0 verifies free-source availability by exact task scope symbol, SEC packet, and macro decision state.",
        "- L1 builds certified FRED vintage macro by decision timestamp.",
        "- L2 maps SEC guidance, macro, and Yahoo price cross-check into semantic primitives.",
        "- L3 creates relation edges from those primitives.",
        "- L4 applies small pre-registered source adjustments.",
        "- L5 replays the frozen top3 path using prior controlled trade returns.",
        "",
        "| Policy | Final | CAGR | MDD | Trades | Joint Target |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| `{metric['policy_variant_id']}` | {metric['final_equity']} | {metric['cagr']} | {metric['max_drawdown']} | {metric['trade_count']} | {metric['joint_target_met']} |",
        "",
        "Split/OOS metrics:",
        "",
        "| Window | Final | Return | MDD |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in splits:
        lines.append(f"| {row['split_window']} | {row['split_final_equity']} | {row['split_total_return']} | {row['split_max_drawdown']} |")
    lines.extend(["", "Attribution audit:", "", "| Source Family | Trades | Adjusted | PnL Audit |", "| --- | ---: | ---: | ---: |"])
    for row in attribution:
        lines.append(f"| `{row['source_family']}` | {row['top3_trade_count_audit_only']} | {row['adjusted_trade_count']} | {row['pnl_sum_audit_only']} |")
    lines.extend(
        [
            "",
            "Remaining blockers:",
            "",
            "- Analyst PIT consensus revision remains unavailable.",
            "- Yahoo price remains cross-check only.",
            "- Non-FRED/vendor rows in the prior free-source ledger are not macro vintage certified.",
            "- This diagnostic replay does not change acceptance.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. The new free sources were connected into L0-L5.",
            "2. The replay was run on the frozen top3 path.",
            "3. The result must be read as diagnostic only.",
            "4. The key question is whether the extra source logic improved judgment or added noise.",
            "",
            "## Artifact Manifest",
            "",
            "- `task1971_input_manifest.csv`",
            "- `task1971_l0_free_source_admission.csv`",
            "- `task1972_l1_alfred_macro_vintage_panel.csv`",
            "- `task1973_l2_free_source_semantics.csv`",
            "- `task1974_l3_free_source_relation_edges.csv`",
            "- `task1975_l4_free_source_thesis_cards.csv`",
            "- `task1976_free_source_top3_replay_trades/equity/metrics/split/cost`",
            "- `task1977_free_source_attribution.csv`",
            "- `task1978_expert_subagent_audit.csv`",
            "- `task1980_acceptance_gate.csv`",
            "- `task1980_closeout.csv/json`",
            "",
            "This task does not change strategy acceptance.",
            "This task does not change deployment readiness.",
            "This task does not permit real capital.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_registry() -> None:
    registry = ROOT / "tasks/task_registry.csv"
    rows = read_csv(registry)
    existing = {row["task_id"] for row in rows}
    report = "docs/reports/task_1971_1980_free_source_l0_l5_replay/task_1971_1980_free_source_l0_l5_replay.md"
    decision = "docs/reports/task_1971_1980_free_source_l0_l5_replay/task_1971_1980_decision.csv"
    artifacts = "data/artifacts/task_1971_1980_free_source_l0_l5_replay"
    titles = [
        ("Task1971", "Free Source L0 Admission"),
        ("Task1972", "ALFRED Macro Vintage L1"),
        ("Task1973", "Free Source L2 Semantics"),
        ("Task1974", "Free Source L3 Relations"),
        ("Task1975", "Free Source L4 Thesis Cards"),
        ("Task1976", "Free Source Top3 Replay"),
        ("Task1977", "Free Source Attribution"),
        ("Task1978", "Expert Subagent Audit"),
        ("Task1979", "Validation And Report"),
        ("Task1980", "Free Source L0-L5 Closeout"),
    ]
    for idx, (task_id, title) in enumerate(titles):
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": title,
                "owner_team": "Research Governance / Backtest & Simulation Infra",
                "status": "active",
                "canonical_state": "diagnostic-only",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "diagnostic-free-source-l0-l5-replay",
                "parent_task": "Task1970" if idx == 0 else titles[idx - 1][0],
                "key_report": report,
                "key_decision": decision,
                "key_artifacts": artifacts,
                "validation_command": "python scripts/trader_brain_1971_1980_free_source_l0_l5_replay_validate.py",
                "notes": "Connects free ALFRED/SEC/Yahoo source evidence into L0-L5 and runs a frozen top3 diagnostic replay without changing acceptance",
            }
        )
    write_csv(registry, rows)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    if "97. Task1971-Task1980" in text:
        return
    line = (
        "97. Task1971-Task1980 connected Task1961-1970 free sources into L0-L5: "
        "ALFRED/FRED vintage macro, SEC issuer guidance, and Yahoo price cross-check were converted into "
        "L0 admission, L1 macro, L2 semantics, L3 relations, L4 thesis cards, and a frozen top3 diagnostic replay; "
        f"the replay ended final {closeout['best_final_equity']} CAGR {closeout['best_cagr']} "
        f"MDD {closeout['best_max_drawdown']}; strategy remains NOT_ACCEPTED / "
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    insert = text.find("\n\nTask851-859")
    if insert == -1:
        text = text.rstrip() + "\n" + line
    else:
        text = text[:insert].rstrip() + "\n" + line + text[insert:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    manifest = input_manifest_rows()
    macro = macro_l1_rows(inputs)
    l0 = l0_admission_rows(inputs, macro)
    l2 = l2_rows(inputs, macro)
    l3 = l3_rows(l2)
    l4 = l4_rows(inputs, l2, l3)
    trades, equity = replay_top3(inputs, l4)
    metrics = metric_rows(inputs, trades, equity)
    splits = split_rows(equity)
    costs = cost_rows(metrics)
    attribution = attribution_rows(l2, l4, trades)
    audit = expert_audit_rows()
    gate, closeout = closeout_rows(metrics)

    write_csv(OUT_DIR / "task1971_input_manifest.csv", manifest)
    write_csv(OUT_DIR / "task1971_l0_free_source_admission.csv", l0)
    write_csv(OUT_DIR / "task1972_l1_alfred_macro_vintage_panel.csv", macro)
    write_csv(OUT_DIR / "task1973_l2_free_source_semantics.csv", l2)
    write_csv(OUT_DIR / "task1974_l3_free_source_relation_edges.csv", l3)
    write_csv(OUT_DIR / "task1975_l4_free_source_thesis_cards.csv", l4)
    write_csv(OUT_DIR / "task1976_free_source_top3_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1976_free_source_top3_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1976_free_source_top3_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1976_split_oos_metrics.csv", splits)
    write_csv(OUT_DIR / "task1976_cost_stress_metrics.csv", costs)
    write_csv(OUT_DIR / "task1977_free_source_attribution.csv", attribution)
    write_csv(OUT_DIR / "task1978_expert_subagent_audit.csv", audit)
    write_csv(OUT_DIR / "task1980_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1980_closeout.csv", closeout)
    write_json(OUT_DIR / "task1980_closeout.json", closeout[0])
    write_csv(DECISION, closeout)
    write_report(metrics, splits, attribution, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print(f"[TASK1971_1980] wrote {OUT_DIR}")
    print(f"[TASK1971_1980] report {REPORT}")


if __name__ == "__main__":
    main()
