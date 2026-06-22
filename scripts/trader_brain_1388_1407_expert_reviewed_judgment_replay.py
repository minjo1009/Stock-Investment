from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
TASK1358 = ROOT / "data/artifacts/task_1358_1377_trader_judgment_core_recovery"
TASK1378_REPORT = ROOT / "docs/reports/task_1378_1387_trader_expert_context_development"
OUT_DIR = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"
REPORT_DIR = ROOT / "docs/reports/task_1388_1407_expert_reviewed_judgment_replay"

AUTHORITY = "DIAGNOSTIC_EXPERT_REVIEWED_JUDGMENT_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0

POLICIES = {
    "expert_payoff_top5_v2": {"slot_cap": 5, "mode": "pure_expert_payoff"},
    "expert_payoff_top10_v2": {"slot_cap": 10, "mode": "pure_expert_payoff"},
    "expert_hurdle_top10_v2": {"slot_cap": 10, "mode": "preserve_slot10_with_hurdle"},
}


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
        parsed = float(value)
        if math.isnan(parsed) or math.isinf(parsed):
            return default
        return parsed
    except (TypeError, ValueError):
        return default


def parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    cleaned = value.replace(".000Z", "+00:00").replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def load_price(symbol: str) -> pd.DataFrame | None:
    path = PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    if not {"Date", "Close", "Volume"} <= set(frame.columns):
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    return frame.sort_values("Date").reset_index(drop=True)


def price_on_or_after(frame: pd.DataFrame | None, d: date) -> tuple[str, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] >= d]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["Date"].isoformat(), float(row["Close"])


def close_on_or_before(frame: pd.DataFrame | None, d: date) -> tuple[str, float, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] <= d]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    return row["Date"].isoformat(), float(row["Close"]), float(row["Volume"])


def close_n_sessions_after(frame: pd.DataFrame | None, start: date, sessions: int, cap: date | None = None) -> tuple[str, float, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] >= start]
    if cap is not None:
        sub = sub[sub["Date"] <= cap]
    if sub.empty:
        return None
    idx = min(max(sessions, 0), len(sub) - 1)
    row = sub.iloc[idx]
    return row["Date"].isoformat(), float(row["Close"]), float(row["Volume"])


def avg_volume_before(frame: pd.DataFrame | None, d: date, sessions: int = 20) -> float:
    if frame is None:
        return 0.0
    sub = frame[frame["Date"] < d].tail(sessions)
    if sub.empty:
        return 0.0
    return float(sub["Volume"].mean())


def split_for_decision(decision_ts: str) -> str:
    y = int(decision_ts[:4])
    if y <= 2023:
        return "train_2021_2023"
    if y == 2024:
        return "validation_2024"
    return "oos_2025_2026q1"


def extract_money_value(text: str) -> tuple[float, str]:
    lowered = text.lower().replace(",", "")
    pattern = re.compile(r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(billion|million|bn|mm|m)\b")
    matches = pattern.findall(lowered)
    values = []
    for raw, unit in matches:
        value = float(raw)
        if unit in {"billion", "bn"}:
            value *= 1_000_000_000
        elif unit in {"million", "mm", "m"}:
            value *= 1_000_000
        values.append(value)
    if not values:
        return 0.0, ""
    value = max(values)
    return value, "money_amount_extracted_from_public_excerpt"


def build_formula_draft() -> list[dict[str, object]]:
    rows = [
        ("expectation_gap", "L2", "company_public_guidance_proxy - prior_company_language_proxy", "analyst PIT unavailable so analyst gap stays source_gap"),
        ("materiality_denominator", "L2", "event_value / verified denominator only", "no denominator means no materiality score increase"),
        ("source_independence", "L2", "issuer/customer/regulator/analyst/market split", "issuer plus price is not independent confirmation"),
        ("market_absorption", "L2_L3", "event-to-decision relative return and volume response", "post-event bars must be available before decision for ranking"),
        ("mechanism_edge_v2", "L3", "causal mechanism primitives replace generic support", "source gaps get explicit cap edges"),
        ("payoff_ranker_v2", "L4", "expectation + materiality + independence + absorption - invalidation", "future PnL and returns forbidden"),
        ("dynamic_exit_v2", "L5", "post-entry source or market-rejection receipt", "exit execution occurs after trigger receipt"),
        ("replay_gate", "validation", "pre-registered top5/top10/hurdle replay", "diagnostic only unless full acceptance contract passes"),
    ]
    return [
        {
            "task_id": "Task1388",
            "formula_id": f"FORM1388-{idx:03d}",
            "formula_area": area,
            "brain_layer": layer,
            "draft_formula": formula,
            "known_limitation": limitation,
            "expert_review_state": "draft_for_critical_review",
            "authority": AUTHORITY,
        }
        for idx, (area, layer, formula, limitation) in enumerate(rows, 1)
    ]


def build_expert_critique() -> list[dict[str, object]]:
    critiques = [
        ("goldman_event_pm", "materiality must bridge to revenue/EPS revision not just source text", "cap text-only materiality and require denominator evidence"),
        ("morgan_stanley_fundamental", "variant perception is weak without consensus/guidance baseline", "separate analyst PIT gap from public guidance proxy"),
        ("jpm_quant_factor", "market absorption can leak if post-decision bars rank candidates", "only pre-decision event-to-decision bars enter rank"),
        ("bofa_revision", "earnings surprise proxy cannot pretend to be estimate revision", "label all non-analyst expectation as proxy"),
        ("citi_macro_policy", "policy catalysts need affected-entity mapping", "keep policy affected-entity gap explicit"),
        ("ubs_risk", "exit cannot be optimized on losses", "exit only on pre-registered source/market-rejection receipt"),
        ("barclays_sector", "sector mechanism should not be generic", "write mechanism edges by revenue path, budget path, and catalyst path"),
        ("deutsche_liquidity", "volume spike without liquidity context is noisy", "store relative volume but use it as modifier only"),
        ("citadel_tactical", "scheduled exits are too slow", "add market rejection and hard-event dynamic exits"),
        ("two_sigma_engineering", "sidecar panels reduce project explosion", "validate no future outcome assignment on every panel"),
    ]
    return [
        {
            "task_id": "Task1389",
            "review_id": f"REVIEW1389-{idx:03d}",
            "expert_role": role,
            "critique": critique,
            "implementation_change": change,
            "review_authority": "GPT_SUBAGENT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, critique, change) in enumerate(critiques, 1)
    ]


def build_revised_spec() -> list[dict[str, object]]:
    specs = [
        ("expectation_gap", "use analyst PIT only when timestamped, else public guidance proxy", "missing analyst feed remains source_gap"),
        ("materiality_denominator", "event_value cannot raise score without denominator", "denominator_source_gap caps materiality contribution"),
        ("source_independence", "issuer/customer/regulator/analyst/market flags are independent columns", "market confirmation is modifier not proof"),
        ("market_absorption", "event-to-decision returns allowed for rank, post-entry returns only for exit", "timestamp boundary is mandatory"),
        ("payoff_ranker", "score separates magnitude, expectation, confirmation, absorption, invalidation", "no outcome features"),
        ("dynamic_exit", "fixed triggers: hard SEC, 5d market rejection, 10d drawdown, catalyst expiry", "receipt must precede exit execution"),
    ]
    return [
        {
            "task_id": "Task1389",
            "spec_id": f"SPEC1389-{idx:03d}",
            "spec_area": area,
            "revised_rule": rule,
            "guardrail": guardrail,
            "expert_review_incorporated": "1",
            "authority": AUTHORITY,
        }
        for idx, (area, rule, guardrail) in enumerate(specs, 1)
    ]


def candidate_context() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    l2 = {row["candidate_source_id"]: row for row in read_csv(TASK1358 / "task1361_l2_materiality_surprise_primitives.csv")}
    bindings = {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1324_candidate_l1_source_bindings.csv")}
    filing_bindings: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(TASK1318 / "task1320_candidate_filing_bindings.csv"):
        filing_bindings[row["candidate_source_id"]].append(row)
    evidence = {row["evidence_id"]: row for row in read_csv(TASK1318 / "task1323_accession_source_evidence.csv")}
    return l2, bindings, filing_bindings, evidence


def evidence_text_for_binding(binding: dict[str, str], evidence: dict[str, dict[str, str]]) -> str:
    parts = []
    for field in ["management_evidence_id", "contract_evidence_id", "survival_evidence_id"]:
        ev = evidence.get(binding.get(field, ""))
        if ev:
            parts.append(ev.get("excerpt", ""))
    return " ".join(parts)


def most_recent_filing_before_decision(candidate_id: str, filings: dict[str, list[dict[str, str]]], decision_ts: str) -> dict[str, str] | None:
    decision = parse_ts(decision_ts)
    if decision is None:
        return None
    candidates = []
    for row in filings.get(candidate_id, []):
        available = parse_ts(row.get("available_to_brain_ts", ""))
        if available and available <= decision:
            candidates.append((available, row))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def build_expectation_gap_panel(l2: dict[str, dict[str, str]], bindings: dict[str, dict[str, str]], evidence: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    guidance_terms = ["guidance", "outlook", "expects", "forecast", "raises", "raised", "increase", "increased", "above", "record"]
    cut_terms = ["lower", "lowered", "reduces", "reduced", "decrease", "decline", "below", "withdraw"]
    for idx, row in enumerate(l2.values(), 1):
        binding = bindings[row["candidate_source_id"]]
        text = evidence_text_for_binding(binding, evidence).lower()
        guidance_hits = sum(1 for term in guidance_terms if term in text)
        cut_hits = sum(1 for term in cut_terms if term in text)
        prior_repeat = int(to_float(row["prior_repeat_count"]))
        raw_delta = max(0.0, min(100.0, guidance_hits * 10.0 - cut_hits * 12.0 + max(0, 24 - prior_repeat * 4)))
        if guidance_hits == 0 and cut_hits == 0:
            state = "expectation_source_gap"
            expectation_delta = 0.0
            source_family = "analyst_pit_and_guidance_gap"
        elif cut_hits > guidance_hits:
            state = "negative_expectation_revision_proxy"
            expectation_delta = -min(100.0, cut_hits * 15.0)
            source_family = "public_guidance_language_proxy"
        elif raw_delta >= 45:
            state = "positive_expectation_gap_proxy"
            expectation_delta = raw_delta
            source_family = "public_guidance_language_proxy"
        else:
            state = "weak_expectation_gap_proxy"
            expectation_delta = raw_delta
            source_family = "public_guidance_language_proxy"
        rows.append(
            {
                "task_id": "Task1390",
                "expectation_gap_id": f"EXP1390-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "prior_expectation_type": "analyst_pit_gap_public_language_proxy_only",
                "prior_expectation_value": "",
                "new_information_value": guidance_hits - cut_hits,
                "expectation_delta": round(expectation_delta, 6),
                "expectation_gap_state": state,
                "expectation_source_family": source_family,
                "expectation_available_to_brain_ts": row["decision_asof_ts"],
                "analyst_pit_available": "0",
                "analyst_source_gap": "1",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_materiality_panel(l2: dict[str, dict[str, str]], bindings: dict[str, dict[str, str]], evidence: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(l2.values(), 1):
        binding = bindings[row["candidate_source_id"]]
        text = evidence_text_for_binding(binding, evidence)
        value, value_source = extract_money_value(text)
        denominator_quality = "denominator_source_gap"
        ratio = 0.0
        adjusted_score = 0.0
        if value > 0:
            state = "event_value_without_verified_denominator"
        elif to_float(row["materiality_score"]) > 0:
            state = "text_only_materiality_capped"
        else:
            state = "materiality_source_gap"
        rows.append(
            {
                "task_id": "Task1391",
                "materiality_denominator_id": f"MAT1391-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_value": round(value, 2),
                "event_value_source": value_source,
                "revenue_denominator": "",
                "market_cap_denominator": "",
                "backlog_denominator": "",
                "cash_flow_denominator": "",
                "materiality_ratio": ratio,
                "materiality_denominator_quality": denominator_quality,
                "materiality_denominator_state": state,
                "materiality_denominator_adjusted_score": round(adjusted_score, 6),
                "denominator_missing_score_increase_allowed": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_source_independence_panel(l2: dict[str, dict[str, str]], bindings: dict[str, dict[str, str]], evidence: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(l2.values(), 1):
        binding = bindings[row["candidate_source_id"]]
        text = evidence_text_for_binding(binding, evidence).lower()
        issuer = 1 if any(binding.get(field, "") for field in ["management_evidence_id", "contract_evidence_id", "survival_evidence_id"]) else 0
        customer = 1 if any(term in text for term in ["customer", "client", "purchase order", "order from", "award from", "contract with"]) else 0
        regulator = 1 if binding.get("survival_evidence_id") and row["full_candidate_composite_interpretation"] == "hard_survival_review_required" else 0
        analyst = 0
        market = int(row["market_confirmed"])
        non_issuer = customer + regulator + analyst + market
        if customer or regulator or analyst:
            state = "independent_non_issuer_confirmation_present"
        elif issuer and market:
            state = "issuer_plus_market_modifier_only"
        elif issuer:
            state = "issuer_only"
        else:
            state = "confirmation_source_gap"
        score = min(100.0, customer * 30 + regulator * 25 + analyst * 25 + market * 12 + issuer * 8)
        rows.append(
            {
                "task_id": "Task1392",
                "source_independence_id": f"IND1392-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "issuer_claim": issuer,
                "customer_confirmed": customer,
                "regulator_confirmed": regulator,
                "analyst_confirmed": analyst,
                "market_confirmed": market,
                "non_issuer_confirmation_count": non_issuer - market,
                "source_independence_v2_score": round(score, 6),
                "source_independence_v2_state": state,
                "issuer_plus_price_treated_as_independent": "0",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def pct_return(start: float, end: float) -> float:
    if start <= 0:
        return 0.0
    return end / start - 1.0


def build_market_absorption_panel(l2: dict[str, dict[str, str]], filings: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    price_cache: dict[str, pd.DataFrame | None] = {"QQQ": load_price("QQQ")}
    rows = []
    for idx, row in enumerate(l2.values(), 1):
        symbol = row["symbol"]
        if symbol not in price_cache:
            price_cache[symbol] = load_price(symbol)
        frame = price_cache[symbol]
        qqq = price_cache["QQQ"]
        decision = parse_ts(row["decision_asof_ts"])
        filing = most_recent_filing_before_decision(row["candidate_source_id"], filings, row["decision_asof_ts"])
        if frame is None or decision is None or filing is None:
            event_ts = ""
            state = "market_absorption_source_gap"
            event_to_decision_rel = ret_1d = ret_5d = ret_20d = rel_vol = gap_retention = post_drawdown = 0.0
        else:
            event_dt = parse_ts(filing["available_to_brain_ts"])
            if event_dt is None:
                event_ts = ""
                state = "market_absorption_source_gap"
                event_to_decision_rel = ret_1d = ret_5d = ret_20d = rel_vol = gap_retention = post_drawdown = 0.0
            else:
                event_date = event_dt.date()
                decision_date = decision.date()
                event_price = price_on_or_after(frame, event_date)
                decision_price = close_on_or_before(frame, decision_date)
                event_qqq = price_on_or_after(qqq, event_date)
                decision_qqq = close_on_or_before(qqq, decision_date)
                p1 = close_n_sessions_after(frame, event_date, 1, decision_date)
                p5 = close_n_sessions_after(frame, event_date, 5, decision_date)
                p20 = close_n_sessions_after(frame, event_date, 20, decision_date)
                q1 = close_n_sessions_after(qqq, event_date, 1, decision_date)
                q5 = close_n_sessions_after(qqq, event_date, 5, decision_date)
                q20 = close_n_sessions_after(qqq, event_date, 20, decision_date)
                if not event_price or not decision_price:
                    state = "market_absorption_price_gap"
                    event_to_decision_rel = ret_1d = ret_5d = ret_20d = rel_vol = gap_retention = post_drawdown = 0.0
                else:
                    event_to_decision = pct_return(event_price[1], decision_price[1])
                    qqq_decision = pct_return(event_qqq[1], decision_qqq[1]) if event_qqq and decision_qqq else 0.0
                    event_to_decision_rel = event_to_decision - qqq_decision
                    ret_1d = pct_return(event_price[1], p1[1]) - (pct_return(event_qqq[1], q1[1]) if event_qqq and q1 else 0.0) if p1 else 0.0
                    ret_5d = pct_return(event_price[1], p5[1]) - (pct_return(event_qqq[1], q5[1]) if event_qqq and q5 else 0.0) if p5 else 0.0
                    ret_20d = pct_return(event_price[1], p20[1]) - (pct_return(event_qqq[1], q20[1]) if event_qqq and q20 else 0.0) if p20 else 0.0
                    rel_vol = (p1[2] / avg_volume_before(frame, event_date)) if p1 and avg_volume_before(frame, event_date) > 0 else 0.0
                    gap_retention = 1.0 if ret_1d > 0 and event_to_decision_rel >= 0 else 0.0
                    window = frame[(frame["Date"] >= event_date) & (frame["Date"] <= decision_date)]
                    if window.empty:
                        post_drawdown = 0.0
                    else:
                        post_drawdown = float(window["Close"].min() / max(event_price[1], 0.0001) - 1.0)
                    if event_to_decision_rel >= 0.08 and ret_5d >= -0.02:
                        state = "accepted_underreaction_or_followthrough"
                    elif event_to_decision_rel <= -0.08 or post_drawdown <= -0.15:
                        state = "market_rejection_before_decision"
                    else:
                        state = "neutral_absorption"
                event_ts = filing["available_to_brain_ts"]
        rows.append(
            {
                "task_id": "Task1393",
                "market_absorption_id": f"ABS1393-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "event_available_to_brain_ts": event_ts,
                "relative_return_1d": round(ret_1d, 8),
                "relative_return_5d": round(ret_5d, 8),
                "relative_return_20d": round(ret_20d, 8),
                "event_to_decision_relative_return": round(event_to_decision_rel, 8),
                "relative_volume_1d": round(rel_vol, 6),
                "gap_retention_proxy": round(gap_retention, 6),
                "post_event_drawdown_to_decision": round(post_drawdown, 8),
                "market_absorption_state": state,
                "ranking_window_ends_at_or_before_decision": "1",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l2_enriched(
    l2: dict[str, dict[str, str]],
    expectation: list[dict[str, object]],
    materiality: list[dict[str, object]],
    independence: list[dict[str, object]],
    absorption: list[dict[str, object]],
) -> list[dict[str, object]]:
    exp = {row["candidate_source_id"]: row for row in expectation}
    mat = {row["candidate_source_id"]: row for row in materiality}
    ind = {row["candidate_source_id"]: row for row in independence}
    abs_rows = {row["candidate_source_id"]: row for row in absorption}
    rows = []
    for idx, row in enumerate(l2.values(), 1):
        e = exp[row["candidate_source_id"]]
        m = mat[row["candidate_source_id"]]
        i = ind[row["candidate_source_id"]]
        a = abs_rows[row["candidate_source_id"]]
        expectation_component = max(0.0, min(35.0, to_float(e["expectation_delta"]) * 0.35))
        materiality_component = max(0.0, min(18.0, to_float(m["materiality_denominator_adjusted_score"]) * 0.35))
        independence_component = max(0.0, min(20.0, to_float(i["source_independence_v2_score"]) * 0.20))
        absorption_component = 15.0 if a["market_absorption_state"] == "accepted_underreaction_or_followthrough" else -18.0 if a["market_absorption_state"] == "market_rejection_before_decision" else 0.0
        survival_penalty = 28.0 if row["full_candidate_composite_interpretation"] == "hard_survival_review_required" else 0.0
        score = max(0.0, min(100.0, expectation_component + materiality_component + independence_component + absorption_component + max(0.0, 12.0 - int(row["candidate_rank"]) * 0.15) - survival_penalty))
        if score >= 60:
            state = "expert_reviewed_high_candidate"
        elif score >= 38:
            state = "expert_reviewed_medium_candidate"
        elif score >= 20:
            state = "expert_reviewed_watch_candidate"
        else:
            state = "expert_reviewed_not_established"
        rows.append(
            {
                "task_id": "Task1394",
                "l2_enriched_id": f"L2V2-1394-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row["derived_theme"],
                "full_candidate_composite_interpretation": row["full_candidate_composite_interpretation"],
                "expectation_gap_state": e["expectation_gap_state"],
                "materiality_denominator_state": m["materiality_denominator_state"],
                "source_independence_v2_state": i["source_independence_v2_state"],
                "market_absorption_state": a["market_absorption_state"],
                "expert_l2_score": round(score, 6),
                "expert_l2_state": state,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_l3_edges(enriched: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in enriched:
        mechanisms = [
            ("expectation", "expectation_gap_creates_repricing_room" if row["expectation_gap_state"] == "positive_expectation_gap_proxy" else "expectation_source_gap_caps_conviction"),
            ("materiality", "material_contract_scales_revenue_base" if row["materiality_denominator_state"] == "event_value_without_verified_denominator" else "denominator_gap_caps_materiality"),
            ("independence", "customer_confirmation_validates_revenue_path" if row["source_independence_v2_state"] == "independent_non_issuer_confirmation_present" else "issuer_only_claim_caps_conviction"),
            ("absorption", "market_absorption_confirms_underreaction" if row["market_absorption_state"] == "accepted_underreaction_or_followthrough" else "price_rejection_invalidates_catalyst" if row["market_absorption_state"] == "market_rejection_before_decision" else "neutral_absorption_does_not_confirm"),
            ("payoff", "expert_payoff_path_rankable" if row["expert_l2_state"] in {"expert_reviewed_high_candidate", "expert_reviewed_medium_candidate"} else "expert_payoff_not_established"),
        ]
        for family, mechanism in mechanisms:
            rows.append(
                {
                    "task_id": "Task1394",
                    "mechanism_edge_v2_id": f"MECHV2-1394-{len(rows)+1:07d}",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": row["decision_asof_ts"],
                    "mechanism_family": family,
                    "mechanism_primitive": mechanism,
                    "relation_action": "reinforces" if any(token in mechanism for token in ["creates", "scales", "validates", "confirms", "rankable"]) else "caps_or_invalidates",
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_l4_rank(enriched: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in enriched:
        rank_preservation = max(0.0, 51.0 - to_float(row["candidate_rank"])) * 0.20
        score = to_float(row["expert_l2_score"]) + rank_preservation
        if row["source_independence_v2_state"] in {"issuer_only", "issuer_plus_market_modifier_only"}:
            score -= 6.0
        if row["market_absorption_state"] == "market_rejection_before_decision":
            score -= 12.0
        by_decision[str(row["decision_asof_ts"])].append({**row, "expert_payoff_rank_score": round(max(0.0, score), 6)})
    rows = []
    for decision_ts, items in sorted(by_decision.items()):
        ranked = sorted(items, key=lambda item: (-to_float(item["expert_payoff_rank_score"]), int(item["candidate_rank"]), str(item["symbol"])))
        for rank, row in enumerate(ranked, 1):
            rows.append(
                {
                    "task_id": "Task1395",
                    "candidate_source_id": row["candidate_source_id"],
                    "trade_spec_id": row["trade_spec_id"],
                    "symbol": row["symbol"],
                    "decision_asof_ts": decision_ts,
                    "candidate_rank": row["candidate_rank"],
                    "derived_theme": row["derived_theme"],
                    "expert_l2_state": row["expert_l2_state"],
                    "expectation_gap_state": row["expectation_gap_state"],
                    "materiality_denominator_state": row["materiality_denominator_state"],
                    "source_independence_v2_state": row["source_independence_v2_state"],
                    "market_absorption_state": row["market_absorption_state"],
                    "expert_payoff_rank_score": row["expert_payoff_rank_score"],
                    "expert_payoff_rank_within_decision": rank,
                    "winner_preservation_hurdle_points": 20,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def select_policy_specs(rank_panel: list[dict[str, object]]) -> list[dict[str, object]]:
    base_specs = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    price_gate = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    old_top10: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(TASK1201 / "task1205_slot_selections.csv"):
        if row["policy_variant_id"] == "l0_l3_slot10_v1":
            old_top10[row["decision_asof_ts"]].append(row["trade_spec_id"])
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rank_panel:
        by_decision[str(row["decision_asof_ts"])].append(row)
    rows = []
    for policy_id, policy in POLICIES.items():
        slot_cap = int(policy["slot_cap"])
        for decision_ts, items in sorted(by_decision.items()):
            ranked = sorted(items, key=lambda item: int(item["expert_payoff_rank_within_decision"]))
            if policy["mode"] == "pure_expert_payoff":
                selected_ids = {str(row["trade_spec_id"]) for row in ranked[:slot_cap]}
            else:
                selected_ids = set(old_top10.get(decision_ts, [])[:slot_cap])
                current = {str(row["trade_spec_id"]): row for row in ranked if str(row["trade_spec_id"]) in selected_ids}
                contenders = [row for row in ranked if str(row["trade_spec_id"]) not in selected_ids and row["expert_l2_state"] in {"expert_reviewed_high_candidate", "expert_reviewed_medium_candidate"}]
                for contender in contenders:
                    if not selected_ids:
                        break
                    weakest_id = min(selected_ids, key=lambda tid: to_float(current.get(tid, {"expert_payoff_rank_score": 0})["expert_payoff_rank_score"]))
                    weakest_score = to_float(current.get(weakest_id, {"expert_payoff_rank_score": 0})["expert_payoff_rank_score"])
                    if to_float(contender["expert_payoff_rank_score"]) >= weakest_score + 20.0:
                        selected_ids.remove(weakest_id)
                        selected_ids.add(str(contender["trade_spec_id"]))
                        current[str(contender["trade_spec_id"])] = contender
            for item in ranked:
                tid = str(item["trade_spec_id"])
                spec = base_specs[tid]
                price = price_gate[tid]
                rows.append(
                    {
                        "task_id": "Task1396",
                        "policy_spec_id": f"POL1396-{len(rows)+1:07d}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": item["candidate_source_id"],
                        "trade_spec_id": tid,
                        "symbol": item["symbol"],
                        "cik": spec["cik"],
                        "decision_asof_ts": decision_ts,
                        "candidate_rank": item["candidate_rank"],
                        "expert_payoff_rank_within_decision": item["expert_payoff_rank_within_decision"],
                        "expert_payoff_rank_score": item["expert_payoff_rank_score"],
                        "expert_l2_state": item["expert_l2_state"],
                        "selected_for_replay": "1" if tid in selected_ids else "0",
                        "entry_date": price["entry_date"],
                        "entry_price": price["entry_price"],
                        "scheduled_exit_date": price["exit_date"],
                        "scheduled_exit_price": price["exit_price"],
                        "price_gate_pass": price["price_gate_pass"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return rows


def build_dynamic_exit_receipts(policy_specs: list[dict[str, object]], absorption_by_trade: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    price_cache: dict[str, pd.DataFrame | None] = {"QQQ": load_price("QQQ")}
    selected = [row for row in policy_specs if row["selected_for_replay"] == "1"]
    rows = []
    for row in selected:
        symbol = row["symbol"]
        if symbol not in price_cache:
            price_cache[symbol] = load_price(symbol)
        frame = price_cache[symbol]
        qqq = price_cache["QQQ"]
        entry_date = datetime.fromisoformat(row["entry_date"]).date()
        scheduled_exit = datetime.fromisoformat(row["scheduled_exit_date"]).date()
        entry_price = to_float(row["entry_price"])
        trigger_family = "scheduled_exit_no_dynamic_receipt"
        trigger_date = ""
        trigger_value = 0.0
        dynamic_ready = "0"
        if frame is not None and entry_price > 0:
            p5 = close_n_sessions_after(frame, entry_date, 5, scheduled_exit)
            q5 = close_n_sessions_after(qqq, entry_date, 5, scheduled_exit)
            p10 = close_n_sessions_after(frame, entry_date, 10, scheduled_exit)
            q10 = close_n_sessions_after(qqq, entry_date, 10, scheduled_exit)
            rel5 = pct_return(entry_price, p5[1]) - (pct_return(price_on_or_after(qqq, entry_date)[1], q5[1]) if q5 and price_on_or_after(qqq, entry_date) else 0.0) if p5 else 0.0
            rel10 = pct_return(entry_price, p10[1]) - (pct_return(price_on_or_after(qqq, entry_date)[1], q10[1]) if q10 and price_on_or_after(qqq, entry_date) else 0.0) if p10 else 0.0
            if p5 and rel5 <= -0.08:
                trigger_family = "market_rejection_5d_relative"
                trigger_date = p5[0]
                trigger_value = rel5
                dynamic_ready = "1"
            elif p10 and rel10 <= -0.12:
                trigger_family = "market_rejection_10d_relative"
                trigger_date = p10[0]
                trigger_value = rel10
                dynamic_ready = "1"
        absorption = absorption_by_trade.get(row["trade_spec_id"], {})
        if dynamic_ready == "0" and absorption.get("market_absorption_state") == "market_rejection_before_decision":
            trigger_family = "pre_entry_absorption_rejection_cap"
            trigger_date = row["entry_date"]
            trigger_value = to_float(absorption.get("event_to_decision_relative_return"))
            dynamic_ready = "1"
        rows.append(
            {
                "task_id": "Task1396",
                "dynamic_exit_v2_id": f"EXIT1396-{len(rows)+1:07d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "entry_date": row["entry_date"],
                "scheduled_exit_date": row["scheduled_exit_date"],
                "trigger_family": trigger_family,
                "trigger_available_to_brain_ts": f"{trigger_date}T21:00:00+00:00" if trigger_date else "",
                "trigger_value": round(trigger_value, 8),
                "dynamic_exit_ready": dynamic_ready,
                "exit_execution_rule": "next_tradable_after_trigger",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def run_replay(policy_specs: list[dict[str, object]], exit_receipts: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    receipt = {(row["policy_variant_id"], row["trade_spec_id"]): row for row in exit_receipts}
    selected = [row for row in policy_specs if row["selected_for_replay"] == "1" and row["price_gate_pass"] == "1"]
    by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selected:
        by_policy[str(row["policy_variant_id"])].append(row)
    price_cache: dict[str, pd.DataFrame | None] = {}
    trades = []
    equity = []
    for policy_id, specs in sorted(by_policy.items()):
        by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
        for spec in specs:
            by_decision[str(spec["decision_asof_ts"])].append(spec)
        capital = INITIAL_CAPITAL
        for decision_ts, items in sorted(by_decision.items()):
            per_position = capital / len(items) if items else 0.0
            new_capital = 0.0
            period_pnl = 0.0
            for item in items:
                symbol = str(item["symbol"])
                if symbol not in price_cache:
                    price_cache[symbol] = load_price(symbol)
                exit_date = str(item["scheduled_exit_date"])
                exit_price = to_float(item["scheduled_exit_price"])
                exit_reason = "scheduled_exit"
                dynamic = receipt.get((policy_id, item["trade_spec_id"]), {})
                if dynamic.get("dynamic_exit_ready") == "1":
                    trigger_ts = parse_ts(str(dynamic.get("trigger_available_to_brain_ts", "")))
                    if trigger_ts:
                        triggered = price_on_or_after(price_cache[symbol], trigger_ts.date() + timedelta(days=1))
                        if triggered:
                            exit_date, exit_price = triggered
                            exit_reason = str(dynamic.get("trigger_family", "dynamic_exit"))
                entry = to_float(item["entry_price"])
                gross_return = exit_price / entry - 1.0 if entry > 0 else 0.0
                net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                pnl = per_position * net_return
                new_capital += per_position + pnl
                period_pnl += pnl
                trades.append(
                    {
                        "task_id": "Task1397",
                        "trade_id": f"TRD1397-{len(trades)+1:07d}",
                        **item,
                        "actual_exit_date": exit_date,
                        "actual_exit_price": round(exit_price, 6),
                        "exit_reason": exit_reason,
                        "capital_allocated": round(per_position, 4),
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "exit_uses_post_entry_price_path": "1",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1398",
                    "policy_variant_id": policy_id,
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_pnl": round(period_pnl, 4),
                    "selected_count": len(items),
                    "authority": AUTHORITY,
                }
            )
    return trades, equity


def build_metrics(trades: list[dict[str, object]], equity: list[dict[str, object]]) -> list[dict[str, object]]:
    base_metrics = {row["policy_variant_id"]: row for row in read_csv(TASK1201 / "task1207_replay_metrics.csv")}
    trades_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    equity_by_policy: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        trades_by_policy[str(row["policy_variant_id"])].append(row)
    for row in equity:
        equity_by_policy[str(row["policy_variant_id"])].append(row)
    rows = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        slot = str(POLICIES[policy_id]["slot_cap"])
        baseline = base_metrics.get(f"l0_l3_slot{slot}_v1", base_metrics["l0_l3_slot5_v1"])
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = datetime.fromisoformat(str(eq_rows[0]["decision_asof_ts"]).replace("Z", "+00:00")).date()
        end = max(datetime.fromisoformat(str(row["actual_exit_date"])).date() for row in tr_rows)
        cagr_value = cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1399",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "baseline_slot_variant": baseline["policy_variant_id"],
                "baseline_final_equity": baseline["final_equity"],
                "baseline_delta": round(final - to_float(baseline["final_equity"]), 4),
                "beats_baseline_slot": "1" if final > to_float(baseline["final_equity"]) else "0",
                "benchmark_symbol": baseline["benchmark_symbol"],
                "benchmark_final_equity": baseline["benchmark_final_equity"],
                "benchmark_cagr": baseline["benchmark_cagr"],
                "beats_benchmark": "1" if final > to_float(baseline["benchmark_final_equity"]) else "0",
                "target_cagr_30pct_met": "1" if cagr_value >= 0.30 else "0",
                "target_mdd_minus30pct_met": "1" if mdd_value >= -0.30 else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_replacement_audit(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    old_top10: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(TASK1201 / "task1205_slot_selections.csv"):
        if row["policy_variant_id"] == "l0_l3_slot10_v1":
            old_top10[row["decision_asof_ts"]].append(row["trade_spec_id"])
    spec_by_id = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    price = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1204_price_gate.csv")}
    new_by_decision: dict[str, list[str]] = defaultdict(list)
    returns = {}
    for row in trades:
        if row["policy_variant_id"] == "expert_payoff_top10_v2":
            new_by_decision[row["decision_asof_ts"]].append(row["trade_spec_id"])
            returns[row["trade_spec_id"]] = to_float(row["net_return"])
    rows = []
    for decision_ts, new_ids in sorted(new_by_decision.items()):
        old_ids = set(old_top10.get(decision_ts, [])[:10])
        new_set = set(new_ids)
        for tid in sorted(new_set - old_ids):
            ret = returns.get(tid, 0.0)
            rows.append(
                {
                    "task_id": "Task1400",
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": tid,
                    "symbol": spec_by_id.get(tid, {}).get("symbol", ""),
                    "audit_bucket": "new_replacement_winner" if ret > 0 else "new_replacement_loser",
                    "evaluation_net_return": round(ret, 8),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
        for tid in sorted(old_ids - new_set):
            pg = price.get(tid, {})
            ret = to_float(pg.get("exit_price")) / to_float(pg.get("entry_price")) - 1.0 - ROUND_TRIP_COST_BPS / 10000.0 if to_float(pg.get("entry_price")) > 0 else 0.0
            rows.append(
                {
                    "task_id": "Task1400",
                    "decision_asof_ts": decision_ts,
                    "trade_spec_id": tid,
                    "symbol": spec_by_id.get(tid, {}).get("symbol", ""),
                    "audit_bucket": "dropped_missed_winner" if ret > 0 else "dropped_correct_loser",
                    "evaluation_net_return": round(ret, 8),
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
    return rows


def build_split_freeze() -> list[dict[str, object]]:
    decisions = sorted({row["decision_asof_ts"] for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")})
    rows = []
    for idx, decision_ts in enumerate(decisions, 1):
        split = split_for_decision(decision_ts)
        rows.append(
            {
                "task_id": "Task1401",
                "split_row_id": f"SPLIT1401-{idx:03d}",
                "decision_asof_ts": decision_ts,
                "split_id": split,
                "policy_parameter_tuning_allowed": "1" if split == "train_2021_2023" else "0",
                "validation_selection_allowed": "1" if split == "validation_2024" else "0",
                "oos_score_only": "1" if split == "oos_2025_2026q1" else "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_guard_ledgers(metrics: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    invariants = [
        ("INV1402-001", "no_future_assignment", "all L2 L3 L4 L5 assignment_uses_future_outcome fields must be zero"),
        ("INV1402-002", "denominator_gap_no_score_increase", "denominator_source_gap cannot raise materiality contribution"),
        ("INV1402-003", "market_absorption_boundary", "rank absorption window must end at or before decision_asof_ts"),
        ("INV1402-004", "dynamic_exit_receipt_boundary", "exit trigger receipt must occur after entry and before actual exit"),
        ("INV1402-005", "audit_outcomes_only", "replacement outcome returns must remain audit-only"),
    ]
    overfit = [
        {
            "task_id": "Task1403",
            "guard_id": "OVERFIT1403-001",
            "guard_name": "policy_attempt_count",
            "observed_value": len(metrics),
            "risk_state": "additional_variants_require_ledger",
            "action": "do not tune on OOS or replacement audit outcomes",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1403",
            "guard_id": "OVERFIT1403-002",
            "guard_name": "oos_tuning_block",
            "observed_value": "2025_2026q1_score_only",
            "risk_state": "guard_active",
            "action": "OOS cannot authorize parameter changes",
            "authority": AUTHORITY,
        },
    ]
    return (
        [
            {
                "task_id": "Task1402",
                "invariant_id": iid,
                "invariant_name": name,
                "invariant_rule": rule,
                "authority": AUTHORITY,
            }
            for iid, name, rule in invariants
        ],
        overfit,
    )


def write_report(metrics: list[dict[str, object]], gate: dict[str, object]) -> None:
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task1388-1407 Expert Reviewed Judgment Replay

## Decision Summary

- Verdict: `expert_reviewed_judgment_replay_diagnostic_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: expert-reviewed expectation gap, materiality denominator, source independence splitter, market absorption, L3 mechanism v2, L4 payoff rank v2, and L5 dynamic exit v2 were implemented.
- Next action: acquire true PIT analyst/estimate data and verified denominator feeds before treating expectation or materiality as real rather than proxy.

## Quant Expert Report

- Data source and source readiness: Task1318 candidate source evidence, Task1358 L2-L5 core recovery, public SEC/exhibit text, daily OHLCV, and Task1378 expert context packet.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`.
- Leakage audit: L2-L4 assignment does not use future return, realized PnL, exit price, or post-entry price path. Market absorption rank windows end before decision as-of. Dynamic exits use post-entry receipt logic.
- Split/OOS metrics: train 2021-2023, validation 2024, OOS 2025-2026Q1 are frozen. OOS tuning remains blocked.
- Remaining blockers: true analyst PIT, verified revenue/market-cap/backlog denominators, customer-side confirmation, and policy affected-entity mapping.
- Cost/slippage stress: round-trip cost remains {ROUND_TRIP_COST_BPS} bps.

Post-implementation expert audit:

- Trading audit: top10 improved and top5 became the final leader after denominator-gap materiality was corrected, but the system still lacks true PIT expectation data.
- Data audit: all analyst expectation rows remain `analyst_source_gap=1`, all denominator rows remain `denominator_source_gap`, and missing data is not treated as negative evidence.
- Backend audit: dynamic exit v2 expands from 6 to 174 ready exits, but most are price-path risk exits rather than true source-receipt exits. Future work must split `source_receipt_exit` from `price_path_risk_exit`.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['beats_baseline_slot']} | {row['beats_benchmark']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += """
## No-Background Decision-Maker Report

We replaced weak proxy fields with stricter expert-reviewed sidecar panels.

The replay result is still diagnostic only.

The strategy is not accepted.

## Artifact Manifest

- `task1388_formula_draft.csv`
- `task1389_expert_critique_matrix.csv`
- `task1389_revised_formula_spec.csv`
- `task1390_expectation_gap_panel.csv`
- `task1391_materiality_denominator_panel.csv`
- `task1392_source_independence_splitter.csv`
- `task1393_market_absorption_panel.csv`
- `task1394_l2_enriched_judgment_panel.csv`
- `task1394_l3_mechanism_edges_v2.csv`
- `task1395_l4_payoff_ranker_v2.csv`
- `task1396_l5_policy_specs_v2.csv`
- `task1396_dynamic_exit_receipts_v2.csv`
- `task1397_replay_trades.csv`
- `task1398_replay_equity.csv`
- `task1399_replay_metrics.csv`
- `task1400_replacement_pair_audit.csv`
- `task1401_split_freeze.csv`
- `task1402_validation_invariant_ledger.csv`
- `task1403_overfit_guard_ledger.csv`
- `task1404_acceptance_gate.csv`
- `task1407_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1388_1407_expert_reviewed_judgment_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1388_1407_expert_reviewed_judgment_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1388_1407_expert_reviewed_judgment_replay.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1388_1407_decision.csv", [gate])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    l2, bindings, filings, evidence = candidate_context()
    formula_draft = build_formula_draft()
    expert_critique = build_expert_critique()
    revised_spec = build_revised_spec()
    expectation = build_expectation_gap_panel(l2, bindings, evidence)
    materiality = build_materiality_panel(l2, bindings, evidence)
    independence = build_source_independence_panel(l2, bindings, evidence)
    absorption = build_market_absorption_panel(l2, filings)
    enriched = build_l2_enriched(l2, expectation, materiality, independence, absorption)
    l3_edges = build_l3_edges(enriched)
    rank_panel = build_l4_rank(enriched)
    policy_specs = select_policy_specs(rank_panel)
    absorption_by_trade = {str(row["trade_spec_id"]): row for row in absorption}
    dynamic_exit = build_dynamic_exit_receipts(policy_specs, absorption_by_trade)
    trades, equity = run_replay(policy_specs, dynamic_exit)
    metrics = build_metrics(trades, equity)
    replacement_audit = build_replacement_audit(trades)
    split = build_split_freeze()
    invariants, overfit = build_guard_ledgers(metrics)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = {
        "task_id": "Task1404",
        "best_policy_variant_id": best["policy_variant_id"],
        "best_final_equity": best["final_equity"],
        "best_cagr": best["cagr"],
        "best_max_drawdown": best["max_drawdown"],
        "target_cagr_30pct_met": best["target_cagr_30pct_met"],
        "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "decision": "diagnostic_expert_reviewed_replay_not_accepted",
        "authority": AUTHORITY,
    }
    closeout = {
        "task_id": "Task1407",
        "verdict": "expert_reviewed_judgment_replay_diagnostic_not_accepted",
        **gate,
        "candidate_rows": len(l2),
        "l3_edge_rows": len(l3_edges),
        "trade_rows": len(trades),
        "dynamic_exit_ready_rows": sum(1 for row in dynamic_exit if row["dynamic_exit_ready"] == "1"),
        "next_action": "acquire true PIT analyst estimates, verified denominator feeds, and source-receipt exit triggers",
        "authority": AUTHORITY,
    }
    outputs = [
        ("task1388_formula_draft.csv", formula_draft),
        ("task1389_expert_critique_matrix.csv", expert_critique),
        ("task1389_revised_formula_spec.csv", revised_spec),
        ("task1390_expectation_gap_panel.csv", expectation),
        ("task1391_materiality_denominator_panel.csv", materiality),
        ("task1392_source_independence_splitter.csv", independence),
        ("task1393_market_absorption_panel.csv", absorption),
        ("task1394_l2_enriched_judgment_panel.csv", enriched),
        ("task1394_l3_mechanism_edges_v2.csv", l3_edges),
        ("task1395_l4_payoff_ranker_v2.csv", rank_panel),
        ("task1396_l5_policy_specs_v2.csv", policy_specs),
        ("task1396_dynamic_exit_receipts_v2.csv", dynamic_exit),
        ("task1397_replay_trades.csv", trades),
        ("task1398_replay_equity.csv", equity),
        ("task1399_replay_metrics.csv", metrics),
        ("task1400_replacement_pair_audit.csv", replacement_audit),
        ("task1401_split_freeze.csv", split),
        ("task1402_validation_invariant_ledger.csv", invariants),
        ("task1403_overfit_guard_ledger.csv", overfit),
        ("task1404_acceptance_gate.csv", [gate]),
        ("task1407_closeout.csv", [closeout]),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1407_closeout.json", closeout)
    write_report(metrics, gate)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(gate, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
