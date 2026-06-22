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
TASK1201 = ROOT / "data/artifacts/task_1201_1210_l0_l3_controlled_replay"
TASK1318 = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"
TASK1388 = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"
PRICE_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy/daily"
COMPANYFACTS_DIR = ROOT / "data/raw/fundamental/sec_companyfacts/companyfacts"
OUT_DIR = ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay"
REPORT_DIR = ROOT / "docs/reports/task_1408_1427_ruler_acquisition_replay"

AUTHORITY = "DIAGNOSTIC_RULER_ACQUISITION_REPLAY_ONLY"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0

POLICIES = {
    "ruler_top3_v1": 3,
    "ruler_top5_v1": 5,
    "ruler_top10_v1": 10,
}

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]
CASH_TAGS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    "CashAndCashEquivalentsAndShortTermInvestments",
]
OCF_TAGS = [
    "NetCashProvidedByUsedInOperatingActivities",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
]
SHARE_TAGS = ["EntityCommonStockSharesOutstanding"]
FLOAT_TAGS = ["EntityPublicFloat"]


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


def parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except ValueError:
        return None


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


def load_price(symbol: str, cache: dict[str, pd.DataFrame | None]) -> pd.DataFrame | None:
    if symbol in cache:
        return cache[symbol]
    path = PRICE_DIR / symbol / f"{symbol}_daily.csv"
    if not path.exists():
        cache[symbol] = None
        return None
    frame = pd.read_csv(path)
    if not {"Date", "Close", "Volume"} <= set(frame.columns):
        cache[symbol] = None
        return None
    frame["Date"] = pd.to_datetime(frame["Date"]).dt.date
    cache[symbol] = frame.sort_values("Date").reset_index(drop=True)
    return cache[symbol]


def price_on_or_after(frame: pd.DataFrame | None, d: date) -> tuple[date, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] >= d]
    if sub.empty:
        return None
    row = sub.iloc[0]
    return row["Date"], float(row["Close"])


def close_on_or_before(frame: pd.DataFrame | None, d: date) -> tuple[date, float, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] <= d]
    if sub.empty:
        return None
    row = sub.iloc[-1]
    return row["Date"], float(row["Close"]), float(row["Volume"])


def close_n_sessions_after(frame: pd.DataFrame | None, start: date, sessions: int, cap: date | None = None) -> tuple[date, float, float] | None:
    if frame is None:
        return None
    sub = frame[frame["Date"] >= start]
    if cap is not None:
        sub = sub[sub["Date"] <= cap]
    if sub.empty:
        return None
    idx = min(max(sessions, 0), len(sub) - 1)
    row = sub.iloc[idx]
    return row["Date"], float(row["Close"]), float(row["Volume"])


def avg_volume_before(frame: pd.DataFrame | None, d: date, sessions: int = 20) -> float:
    if frame is None:
        return 0.0
    sub = frame[frame["Date"] < d].tail(sessions)
    if sub.empty:
        return 0.0
    return float(sub["Volume"].mean())


def pct_return(start_price: float, end_price: float) -> float:
    if start_price <= 0:
        return 0.0
    return end_price / start_price - 1.0


def split_for_decision(decision_ts: str) -> str:
    y = int(decision_ts[:4])
    if y <= 2023:
        return "train_2021_2023"
    if y == 2024:
        return "validation_2024"
    return "oos_2025_2026q1"


def load_inputs() -> tuple[list[dict[str, str]], dict[str, dict[str, str]], dict[str, dict[str, str]], dict[str, list[dict[str, str]]], dict[str, dict[str, str]]]:
    enriched = read_csv(TASK1388 / "task1394_l2_enriched_judgment_panel.csv")
    specs = {row["trade_spec_id"]: row for row in read_csv(TASK1201 / "task1203_l5_trade_specs.csv")}
    bindings = {row["candidate_source_id"]: row for row in read_csv(TASK1318 / "task1324_candidate_l1_source_bindings.csv")}
    filing_bindings: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(TASK1318 / "task1320_candidate_filing_bindings.csv"):
        filing_bindings[row["candidate_source_id"]].append(row)
    evidence = {row["evidence_id"]: row for row in read_csv(TASK1318 / "task1323_accession_source_evidence.csv")}
    return enriched, specs, bindings, filing_bindings, evidence


def build_expert_review_packet() -> list[dict[str, object]]:
    rows = [
        ("goldman_event_driven_pm", "materiality ruler needs denominator-backed magnitude, not source count", "event_value divided by verified revenue, market cap, backlog, cash"),
        ("morgan_stanley_semis", "contract and AI capex stories need revenue scale and customer confirmation", "issuer-only evidence stays capped unless independent family appears"),
        ("jpm_quant_research", "market acceptance should be pre-decision absorption and post-entry exit separately", "absorption ruler and exit ruler are split"),
        ("bofa_revisions", "expectation needs prior guidance or analyst PIT, otherwise it is only a public proxy", "analyst PIT remains explicit unavailable gap"),
        ("citi_macro_policy", "policy/news catalysts require affected entity mapping before broad boosts", "policy source gap remains no-score unless symbol mapped"),
        ("ubs_risk", "sell rules must distinguish source receipt exits from price-path stops", "source_receipt_exit and price_path_risk_exit are separate panels"),
        ("barclays_space_ai", "high upside names require volatility tolerance but terminal risk evidence must cut", "leverage/high beta are not auto-blocked; hard source receipt can exit"),
        ("deutsche_engineering", "missing denominators cannot be imputed from symbol/date proximity", "missing denominator contributes zero materiality points"),
        ("two_sigma_backtest", "replacement policies must be frozen before replay and OOS cannot tune", "top3/top5/top10 policies are fixed upfront"),
        ("backend_quality_lead", "every panel needs audit columns and artifact manifest", "validator enforces row counts, no-future fields, and status footer"),
    ]
    return [
        {
            "task_id": "Task1408",
            "review_id": f"RULERREVIEW1408-{idx:03d}",
            "expert_role": role,
            "critical_feedback": feedback,
            "implementation_change": change,
            "review_authority": "GPT_SUBAGENT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, feedback, change) in enumerate(rows, 1)
    ]


def build_ruler_schema() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    scale_rows = [
        ("event_value_usd", "public excerpt money amount attached to contract/order/backlog/cash context", "source_excerpt"),
        ("ttm_revenue_usd", "latest SEC companyfacts annual or trailing revenue filed by decision time", "sec_companyfacts_asof"),
        ("market_cap_proxy_usd", "shares outstanding filed by decision time times close on/before decision", "sec_companyfacts_plus_price_asof"),
        ("cash_usd", "latest SEC companyfacts cash filed by decision time", "sec_companyfacts_asof"),
        ("backlog_usd", "public excerpt backlog amount when explicitly found", "source_excerpt"),
    ]
    expectation_rows = [
        ("public_guidance_direction", "raised/lowered/maintained/unknown based on source excerpt text", "source_excerpt"),
        ("analyst_pit_available", "licensed analyst estimate feed availability flag", "vendor_gap_today"),
        ("expectation_ruler_state", "positive/negative/weak/source_gap", "computed_no_future"),
    ]
    exit_rows = [
        ("source_receipt_exit", "post-entry as-of source receipt with hard survival, dilution, guidance cut, or material invalidation", "source_timestamp_after_entry"),
        ("price_path_risk_exit", "pre-registered post-entry price rejection/risk stop", "post_entry_price_path_diagnostic"),
        ("hold_extend_receipt", "positive post-entry source or market acceptance that supports scheduled holding", "source_or_price_receipt_after_entry"),
    ]
    def pack(task: str, rows: list[tuple[str, str, str]]) -> list[dict[str, object]]:
        return [
            {
                "task_id": task,
                "field_name": name,
                "definition": definition,
                "source_contract": contract,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
            for name, definition, contract in rows
        ]
    return pack("Task1409", scale_rows), pack("Task1414", expectation_rows), pack("Task1420", exit_rows)


def fact_units(facts: dict, taxonomy: str, tag: str) -> list[dict]:
    item = facts.get(taxonomy, {}).get(tag, {})
    units = item.get("units", {})
    rows: list[dict] = []
    for unit_rows in units.values():
        if isinstance(unit_rows, list):
            rows.extend([row for row in unit_rows if isinstance(row, dict)])
    return rows


def latest_fact_before(facts: dict, tags: list[str], decision: date, *, taxonomy: str = "us-gaap", annual_only: bool = False) -> tuple[float, str, str, str]:
    candidates: list[tuple[date, date, float, str, str, str]] = []
    for tag in tags:
        for row in fact_units(facts, taxonomy, tag):
            filed = parse_date(str(row.get("filed", "")))
            end = parse_date(str(row.get("end", "")))
            if filed is None or end is None or filed > decision or end > decision:
                continue
            if annual_only and str(row.get("fp", "")).upper() not in {"FY", "CY"}:
                continue
            value = to_float(row.get("val"))
            if value == 0.0:
                continue
            candidates.append((filed, end, value, tag, str(row.get("form", "")), str(row.get("fp", ""))))
    if not candidates:
        return 0.0, "", "", ""
    filed, end, value, tag, form, fp = max(candidates, key=lambda item: (item[0], item[1]))
    return value, tag, filed.isoformat(), f"{form}:{fp}:{end.isoformat()}"


def load_companyfacts_index() -> tuple[dict[str, Path], dict[str, Path]]:
    by_symbol: dict[str, Path] = {}
    by_cik: dict[str, Path] = {}
    if not COMPANYFACTS_DIR.exists():
        return by_symbol, by_cik
    for path in COMPANYFACTS_DIR.glob("*.json"):
        stem = path.stem
        parts = stem.split("_")
        if parts:
            by_symbol[parts[0].upper()] = path
        if len(parts) >= 2:
            by_cik[parts[-1].lstrip("0")] = path
    return by_symbol, by_cik


def companyfacts_for(symbol: str, cik: str, by_symbol: dict[str, Path], by_cik: dict[str, Path], cache: dict[Path, dict]) -> dict | None:
    path = by_symbol.get(symbol.upper()) or by_cik.get(cik.lstrip("0"))
    if path is None:
        return None
    if path not in cache:
        try:
            cache[path] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache[path] = {}
    return cache[path] or None


def build_companyfacts_denominators(
    enriched: list[dict[str, str]],
    specs: dict[str, dict[str, str]],
    price_cache: dict[str, pd.DataFrame | None],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    by_symbol, by_cik = load_companyfacts_index()
    fact_cache: dict[Path, dict] = {}
    denom_rows: list[dict[str, object]] = []
    market_rows: list[dict[str, object]] = []
    for idx, row in enumerate(enriched, 1):
        spec = specs[row["trade_spec_id"]]
        symbol = row["symbol"]
        cik = spec.get("cik", "")
        decision = parse_ts(row["decision_asof_ts"])
        decision_date = decision.date() if decision else parse_date(row["decision_asof_ts"][:10]) or date(1970, 1, 1)
        facts = companyfacts_for(symbol, cik, by_symbol, by_cik, fact_cache)
        revenue = cash = ocf = shares = public_float = 0.0
        rev_tag = cash_tag = ocf_tag = share_tag = float_tag = ""
        rev_filed = cash_filed = ocf_filed = share_filed = float_filed = ""
        rev_meta = cash_meta = ocf_meta = share_meta = float_meta = ""
        source_gap = "1"
        if facts:
            revenue, rev_tag, rev_filed, rev_meta = latest_fact_before(facts.get("facts", {}), REVENUE_TAGS, decision_date, annual_only=True)
            if revenue == 0.0:
                revenue, rev_tag, rev_filed, rev_meta = latest_fact_before(facts.get("facts", {}), REVENUE_TAGS, decision_date)
            cash, cash_tag, cash_filed, cash_meta = latest_fact_before(facts.get("facts", {}), CASH_TAGS, decision_date)
            ocf, ocf_tag, ocf_filed, ocf_meta = latest_fact_before(facts.get("facts", {}), OCF_TAGS, decision_date, annual_only=True)
            shares, share_tag, share_filed, share_meta = latest_fact_before(facts.get("facts", {}), SHARE_TAGS, decision_date, taxonomy="dei")
            public_float, float_tag, float_filed, float_meta = latest_fact_before(facts.get("facts", {}), FLOAT_TAGS, decision_date, taxonomy="dei")
            if any(value > 0 for value in [revenue, cash, ocf, shares, public_float]):
                source_gap = "0"
        frame = load_price(symbol, price_cache)
        close = close_on_or_before(frame, decision_date)
        decision_close = close[1] if close else 0.0
        market_cap = shares * decision_close if shares > 0 and decision_close > 0 else 0.0
        market_cap_gap = "0" if market_cap > 0 else "1"
        denom_rows.append(
            {
                "task_id": "Task1410",
                "denominator_row_id": f"DENOM1410-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "cik": cik,
                "decision_asof_ts": row["decision_asof_ts"],
                "companyfacts_available": "1" if facts else "0",
                "ttm_revenue_usd": round(revenue, 4),
                "ttm_revenue_tag": rev_tag,
                "ttm_revenue_filed_date": rev_filed,
                "ttm_revenue_meta": rev_meta,
                "cash_usd": round(cash, 4),
                "cash_tag": cash_tag,
                "cash_filed_date": cash_filed,
                "cash_meta": cash_meta,
                "operating_cash_flow_usd": round(ocf, 4),
                "operating_cash_flow_tag": ocf_tag,
                "operating_cash_flow_filed_date": ocf_filed,
                "operating_cash_flow_meta": ocf_meta,
                "shares_outstanding": round(shares, 4),
                "shares_tag": share_tag,
                "shares_filed_date": share_filed,
                "shares_meta": share_meta,
                "public_float_usd": round(public_float, 4),
                "public_float_tag": float_tag,
                "public_float_filed_date": float_filed,
                "public_float_meta": float_meta,
                "denominator_source_gap": source_gap,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        market_rows.append(
            {
                "task_id": "Task1411",
                "market_cap_row_id": f"MKTCAP1411-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": symbol,
                "decision_asof_ts": row["decision_asof_ts"],
                "shares_outstanding": round(shares, 4),
                "shares_filed_date": share_filed,
                "decision_close_date": close[0].isoformat() if close else "",
                "decision_close_price": round(decision_close, 6),
                "market_cap_proxy_usd": round(market_cap, 4),
                "market_cap_proxy_gap": market_cap_gap,
                "public_float_usd": round(public_float, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return denom_rows, market_rows


def extract_money_context(text: str) -> tuple[float, str, str]:
    lowered = text.lower().replace(",", "")
    pattern = re.compile(r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(billion|million|bn|mm|m)\b")
    matches = list(pattern.finditer(lowered))
    if not matches:
        return 0.0, "", ""
    best_value = 0.0
    best_ctx = ""
    for match in matches:
        value = float(match.group(1))
        unit = match.group(2)
        if unit in {"billion", "bn"}:
            value *= 1_000_000_000
        else:
            value *= 1_000_000
        start = max(0, match.start() - 90)
        end = min(len(lowered), match.end() + 90)
        context = lowered[start:end]
        if value > best_value:
            best_value = value
            best_ctx = context
    if "backlog" in best_ctx:
        amount_type = "backlog_value"
    elif any(token in best_ctx for token in ["contract", "award", "order", "customer", "purchase", "booking"]):
        amount_type = "contract_or_order_value"
    elif any(token in best_ctx for token in ["cash", "liquidity", "financing", "credit"]):
        amount_type = "cash_or_financing_value"
    else:
        amount_type = "public_money_amount"
    return best_value, amount_type, best_ctx[:180]


def source_excerpt(row: dict[str, str], bindings: dict[str, dict[str, str]], evidence: dict[str, dict[str, str]]) -> str:
    binding = bindings.get(row["candidate_source_id"], {})
    ids = [
        binding.get("management_evidence_id", ""),
        binding.get("contract_evidence_id", ""),
        binding.get("survival_evidence_id", ""),
    ]
    return " ".join(evidence.get(eid, {}).get("excerpt", "") for eid in ids if eid)


def build_event_value_panel(
    enriched: list[dict[str, str]],
    bindings: dict[str, dict[str, str]],
    evidence: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(enriched, 1):
        excerpt = source_excerpt(row, bindings, evidence)
        value, value_type, context = extract_money_context(excerpt)
        rows.append(
            {
                "task_id": "Task1412",
                "event_value_row_id": f"EVENTVAL1412-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_value_usd": round(value, 4),
                "event_value_type": value_type if value > 0 else "event_value_not_found",
                "backlog_value_usd": round(value, 4) if value_type == "backlog_value" else 0.0,
                "value_extraction_state": "money_value_found" if value > 0 else "source_gap_or_no_money_amount",
                "value_context_excerpt": context,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def ratio(value: float, denom: float) -> float:
    if value <= 0 or denom <= 0:
        return 0.0
    return value / denom


def build_materiality_ruler(
    enriched: list[dict[str, str]],
    denom: list[dict[str, object]],
    market_cap: list[dict[str, object]],
    event_values: list[dict[str, object]],
) -> list[dict[str, object]]:
    denom_by_id = {str(row["candidate_source_id"]): row for row in denom}
    market_by_id = {str(row["candidate_source_id"]): row for row in market_cap}
    event_by_id = {str(row["candidate_source_id"]): row for row in event_values}
    rows: list[dict[str, object]] = []
    for idx, row in enumerate(enriched, 1):
        cid = row["candidate_source_id"]
        d = denom_by_id[cid]
        m = market_by_id[cid]
        e = event_by_id[cid]
        event = to_float(e["event_value_usd"])
        revenue_ratio = ratio(event, to_float(d["ttm_revenue_usd"]))
        market_ratio = ratio(event, to_float(m["market_cap_proxy_usd"]))
        cash_ratio = ratio(event, to_float(d["cash_usd"]))
        # Backlog mentioned in the same excerpt is evidence context, not a verified denominator by itself.
        backlog_ratio = 0.0
        source_gap = "1" if event <= 0 or (revenue_ratio == market_ratio == cash_ratio == 0.0) else "0"
        score = 0.0
        state = "materiality_source_gap"
        if source_gap == "0":
            if revenue_ratio >= 0.10 or market_ratio >= 0.05 or cash_ratio >= 0.25 or backlog_ratio >= 0.10:
                score = 30.0
                state = "high_verified_materiality"
            elif revenue_ratio >= 0.03 or market_ratio >= 0.015 or cash_ratio >= 0.10:
                score = 15.0
                state = "medium_verified_materiality"
            else:
                score = 5.0
                state = "low_verified_materiality"
        rows.append(
            {
                "task_id": "Task1413",
                "materiality_ruler_row_id": f"MATRULER1413-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "event_value_usd": round(event, 4),
                "event_to_revenue_ratio": round(revenue_ratio, 8),
                "event_to_market_cap_ratio": round(market_ratio, 8),
                "event_to_cash_ratio": round(cash_ratio, 8),
                "event_to_backlog_ratio": round(backlog_ratio, 8),
                "materiality_ruler_state": state,
                "materiality_ruler_score": round(score, 4),
                "materiality_source_gap": source_gap,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_guidance_and_expectation(
    enriched: list[dict[str, str]],
    bindings: dict[str, dict[str, str]],
    evidence: dict[str, dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    guidance_rows: list[dict[str, object]] = []
    analyst_rows: list[dict[str, object]] = []
    expectation_rows: list[dict[str, object]] = []
    positive = ["raise", "raised", "raises", "increase", "increased", "higher", "above", "record", "strong", "accelerat"]
    negative = ["lower", "lowered", "reduce", "reduced", "below", "withdraw", "delay", "weak", "declin", "miss"]
    for idx, row in enumerate(enriched, 1):
        excerpt = source_excerpt(row, bindings, evidence).lower()
        pos_hits = sum(1 for token in positive if token in excerpt)
        neg_hits = sum(1 for token in negative if token in excerpt)
        if pos_hits > neg_hits and pos_hits > 0:
            direction = "positive_public_guidance_revision_proxy"
            score = 18.0
        elif neg_hits > pos_hits and neg_hits > 0:
            direction = "negative_public_guidance_revision_proxy"
            score = -20.0
        elif pos_hits or neg_hits:
            direction = "mixed_public_guidance_proxy"
            score = 4.0
        else:
            direction = "guidance_revision_not_detected"
            score = 0.0
        guidance_rows.append(
            {
                "task_id": "Task1415",
                "guidance_row_id": f"GUIDE1415-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "public_guidance_direction": direction,
                "positive_term_hits": pos_hits,
                "negative_term_hits": neg_hits,
                "guidance_proxy_score": round(score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        analyst_rows.append(
            {
                "task_id": "Task1416",
                "analyst_audit_row_id": f"ANALYST1416-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "analyst_pit_available": "0",
                "analyst_pit_source_gap": "1",
                "reason": "licensed_pit_estimate_revision_feed_not_available_in_local_repo",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        state = direction
        if direction == "guidance_revision_not_detected":
            state = "expectation_ruler_source_gap"
        expectation_rows.append(
            {
                "task_id": "Task1417",
                "expectation_ruler_row_id": f"EXPRULER1417-{idx:07d}",
                "candidate_source_id": row["candidate_source_id"],
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "expectation_ruler_state": state,
                "public_guidance_score": round(score, 4),
                "analyst_revision_score": 0.0,
                "analyst_pit_source_gap": "1",
                "expectation_ruler_score": round(score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return guidance_rows, analyst_rows, expectation_rows


def earliest_event_date(candidate_id: str, filings: dict[str, list[dict[str, str]]]) -> date | None:
    dates = []
    for row in filings.get(candidate_id, []):
        ts = parse_ts(row.get("available_to_brain_ts", ""))
        if ts:
            dates.append(ts.date())
    return min(dates) if dates else None


def build_absorption_panels(
    enriched: list[dict[str, str]],
    filings: dict[str, list[dict[str, str]]],
    price_cache: dict[str, pd.DataFrame | None],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    qqq = load_price("QQQ", price_cache)
    enhanced: list[dict[str, object]] = []
    ruler: list[dict[str, object]] = []
    for idx, row in enumerate(enriched, 1):
        decision_dt = parse_ts(row["decision_asof_ts"])
        decision_date = decision_dt.date() if decision_dt else parse_date(row["decision_asof_ts"][:10]) or date(1970, 1, 1)
        event_date = earliest_event_date(row["candidate_source_id"], filings)
        frame = load_price(row["symbol"], price_cache)
        symbol_event = close_on_or_before(frame, event_date) if event_date else None
        symbol_decision = close_on_or_before(frame, decision_date)
        qqq_event = close_on_or_before(qqq, event_date) if event_date else None
        qqq_decision = close_on_or_before(qqq, decision_date)
        rel_return = 0.0
        abs_return = 0.0
        rel_volume = 0.0
        window_pass = "0"
        if symbol_event and symbol_decision and qqq_event and qqq_decision:
            abs_return = pct_return(symbol_event[1], symbol_decision[1])
            qqq_return = pct_return(qqq_event[1], qqq_decision[1])
            rel_return = abs_return - qqq_return
            avg_vol = avg_volume_before(frame, decision_date)
            rel_volume = symbol_decision[2] / avg_vol if avg_vol > 0 else 0.0
            window_pass = "1" if event_date <= decision_date else "0"
        if window_pass == "1" and rel_return > 0.05:
            state = "accepted_underreaction_or_followthrough"
            score = 18.0
        elif window_pass == "1" and rel_return < -0.08:
            state = "market_rejection_before_decision"
            score = -22.0
        elif window_pass == "1":
            state = "neutral_absorption"
            score = 4.0
        else:
            state = "absorption_source_gap"
            score = 0.0
        base = {
            "candidate_source_id": row["candidate_source_id"],
            "trade_spec_id": row["trade_spec_id"],
            "symbol": row["symbol"],
            "decision_asof_ts": row["decision_asof_ts"],
            "event_date": event_date.isoformat() if event_date else "",
            "window_end_date": decision_date.isoformat(),
            "event_to_decision_return": round(abs_return, 8),
            "event_to_decision_relative_return": round(rel_return, 8),
            "decision_relative_volume": round(rel_volume, 6),
            "absorption_window_pass": window_pass,
            "assignment_uses_future_outcome": "0",
            "authority": AUTHORITY,
        }
        enhanced.append({"task_id": "Task1418", "absorption_row_id": f"ABSORB1418-{idx:07d}", **base})
        ruler.append(
            {
                "task_id": "Task1419",
                "absorption_ruler_row_id": f"ABSRULER1419-{idx:07d}",
                **base,
                "absorption_ruler_state": state,
                "absorption_ruler_score": round(score, 4),
            }
        )
    return enhanced, ruler


def build_filing_indexes(
    filing_bindings: dict[str, list[dict[str, str]]],
    evidence: dict[str, dict[str, str]],
) -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    by_symbol: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    accession_text: dict[str, list[str]] = defaultdict(list)
    for ev in evidence.values():
        accession = ev.get("accession", "")
        if accession:
            accession_text[accession].append((ev.get("source_state", "") + " " + ev.get("reason", "") + " " + ev.get("matched_pattern", "") + " " + ev.get("excerpt", "")).lower())
    for rows in filing_bindings.values():
        for row in rows:
            symbol = row.get("symbol", "")
            accession = row.get("accession", "")
            if not symbol or not accession:
                continue
            if accession not in by_symbol[symbol]:
                by_symbol[symbol][accession] = row
    packed = {symbol: sorted(rows.values(), key=lambda r: r.get("available_to_brain_ts", "")) for symbol, rows in by_symbol.items()}
    return packed, {acc: " ".join(parts) for acc, parts in accession_text.items()}


def build_policy_specs(rank_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rank_rows:
        by_decision[str(row["decision_asof_ts"])].append(row)
    selected: list[dict[str, object]] = []
    for policy_id, slot_cap in POLICIES.items():
        for decision_ts, rows in by_decision.items():
            ordered = sorted(rows, key=lambda item: (to_float(item["ruler_payoff_rank_within_decision"]), int(to_float(item["candidate_rank"], 9999))))[:slot_cap]
            for row in ordered:
                selected.append(
                    {
                        "task_id": "Task1426",
                        "policy_spec_id": f"{policy_id}:{row['trade_spec_id']}",
                        "policy_variant_id": policy_id,
                        "slot_cap": slot_cap,
                        "candidate_source_id": row["candidate_source_id"],
                        "trade_spec_id": row["trade_spec_id"],
                        "symbol": row["symbol"],
                        "decision_asof_ts": decision_ts,
                        "ruler_payoff_rank_score": row["ruler_payoff_rank_score"],
                        "ruler_payoff_rank_within_decision": row["ruler_payoff_rank_within_decision"],
                        "assignment_uses_future_outcome": "0",
                        "authority": AUTHORITY,
                    }
                )
    return selected


def build_integrated_and_rank(
    enriched: list[dict[str, str]],
    materiality: list[dict[str, object]],
    expectation: list[dict[str, object]],
    absorption: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    mat = {str(row["candidate_source_id"]): row for row in materiality}
    exp = {str(row["candidate_source_id"]): row for row in expectation}
    absb = {str(row["candidate_source_id"]): row for row in absorption}
    integrated: list[dict[str, object]] = []
    for idx, row in enumerate(enriched, 1):
        cid = row["candidate_source_id"]
        candidate_rank = int(to_float(row.get("candidate_rank"), 9999))
        base_quality = max(0.0, 20.0 - candidate_rank * 0.12)
        materiality_score = to_float(mat[cid]["materiality_ruler_score"])
        expectation_score = to_float(exp[cid]["expectation_ruler_score"])
        absorption_score = to_float(absb[cid]["absorption_ruler_score"])
        prior_expert_score = min(18.0, max(0.0, to_float(row.get("expert_l2_score")) * 0.18))
        if row.get("source_independence_v2_state") == "independent_non_issuer_confirmation_present":
            independence_score = 14.0
        elif row.get("source_independence_v2_state") == "issuer_plus_market_modifier_only":
            independence_score = 5.0
        else:
            independence_score = 0.0
        invalidation_penalty = -25.0 if "hard" in row.get("full_candidate_composite_interpretation", "").lower() else 0.0
        score = base_quality + prior_expert_score + materiality_score + expectation_score + absorption_score + independence_score + invalidation_penalty
        if mat[cid]["materiality_ruler_state"] == "materiality_source_gap":
            score -= 4.0
        if exp[cid]["expectation_ruler_state"] == "expectation_ruler_source_gap":
            score -= 3.0
        integrated.append(
            {
                "task_id": "Task1424",
                "integrated_ruler_row_id": f"INTRULER1424-{idx:07d}",
                "candidate_source_id": cid,
                "trade_spec_id": row["trade_spec_id"],
                "symbol": row["symbol"],
                "decision_asof_ts": row["decision_asof_ts"],
                "candidate_rank": row["candidate_rank"],
                "derived_theme": row.get("derived_theme", ""),
                "materiality_ruler_state": mat[cid]["materiality_ruler_state"],
                "materiality_ruler_score": round(materiality_score, 4),
                "expectation_ruler_state": exp[cid]["expectation_ruler_state"],
                "expectation_ruler_score": round(expectation_score, 4),
                "absorption_ruler_state": absb[cid]["absorption_ruler_state"],
                "absorption_ruler_score": round(absorption_score, 4),
                "source_independence_v2_state": row.get("source_independence_v2_state", ""),
                "source_independence_score": round(independence_score, 4),
                "prior_expert_score_component": round(prior_expert_score, 4),
                "invalidation_penalty": round(invalidation_penalty, 4),
                "integrated_ruler_score": round(score, 4),
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    by_decision: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in integrated:
        by_decision[str(row["decision_asof_ts"])].append(row)
    rank_rows: list[dict[str, object]] = []
    for decision_ts, rows in by_decision.items():
        ordered = sorted(rows, key=lambda item: (-to_float(item["integrated_ruler_score"]), int(to_float(item["candidate_rank"], 9999))))
        for rank, row in enumerate(ordered, 1):
            rank_rows.append(
                {
                    "task_id": "Task1425",
                    "rank_row_id": f"PAYOFFV3-1425-{len(rank_rows)+1:07d}",
                    **{key: row[key] for key in row if key not in {"task_id", "integrated_ruler_row_id"}},
                    "ruler_payoff_rank_score": row["integrated_ruler_score"],
                    "ruler_payoff_rank_within_decision": rank,
                    "assignment_uses_future_outcome": "0",
                    "authority": AUTHORITY,
                }
            )
    return integrated, rank_rows


def build_exit_panels(
    selected_specs: list[dict[str, object]],
    specs: dict[str, dict[str, str]],
    symbol_filings: dict[str, list[dict[str, str]]],
    accession_text: dict[str, str],
    price_cache: dict[str, pd.DataFrame | None],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    source_rows: list[dict[str, object]] = []
    price_rows: list[dict[str, object]] = []
    hold_rows: list[dict[str, object]] = []
    hard_tokens = ["going concern", "dilution", "delist", "bankrupt", "material weakness", "lowered", "withdraw", "terminate"]
    positive_tokens = ["raise", "record", "award", "contract", "customer", "backlog", "strong"]
    for idx, selected in enumerate(selected_specs, 1):
        spec = specs[str(selected["trade_spec_id"])]
        symbol = str(selected["symbol"])
        entry_after = parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
        scheduled_exit = parse_date(spec["exit_on_or_before_date"]) or entry_after
        entry = price_on_or_after(load_price(symbol, price_cache), entry_after)
        entry_date = entry[0] if entry else entry_after
        source_trigger = ""
        source_ts = ""
        hold_trigger = ""
        hold_ts = ""
        for filing in symbol_filings.get(symbol, []):
            ts = parse_ts(filing.get("available_to_brain_ts", ""))
            if ts is None or ts.date() <= entry_date or ts.date() > scheduled_exit:
                continue
            text = accession_text.get(filing.get("accession", ""), "")
            if not source_trigger and any(token in text for token in hard_tokens):
                source_trigger = "hard_source_invalidation_receipt"
                source_ts = ts.isoformat()
            if not hold_trigger and any(token in text for token in positive_tokens):
                hold_trigger = "positive_source_hold_receipt"
                hold_ts = ts.isoformat()
            if source_trigger and hold_trigger:
                break
        frame = load_price(symbol, price_cache)
        day5 = close_n_sessions_after(frame, entry_date, 5, scheduled_exit)
        day10 = close_n_sessions_after(frame, entry_date, 10, scheduled_exit)
        risk_trigger = ""
        risk_date = ""
        risk_price = 0.0
        if entry and day5 and pct_return(entry[1], day5[1]) <= -0.10:
            risk_trigger = "price_path_5d_market_rejection"
            risk_date = day5[0].isoformat()
            risk_price = day5[1]
        elif entry and day10 and pct_return(entry[1], day10[1]) <= -0.16:
            risk_trigger = "price_path_10d_drawdown_risk"
            risk_date = day10[0].isoformat()
            risk_price = day10[1]
        source_rows.append(
            {
                "task_id": "Task1421",
                "source_exit_row_id": f"SRCEXIT1421-{idx:07d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "symbol": symbol,
                "entry_date": entry_date.isoformat(),
                "scheduled_exit_date": scheduled_exit.isoformat(),
                "source_receipt_exit_ready": "1" if source_trigger else "0",
                "source_receipt_exit_type": source_trigger,
                "source_receipt_ts": source_ts,
                "exit_family": "source_receipt_exit",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        price_rows.append(
            {
                "task_id": "Task1422",
                "price_exit_row_id": f"PRICEEXIT1422-{idx:07d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "symbol": symbol,
                "entry_date": entry_date.isoformat(),
                "scheduled_exit_date": scheduled_exit.isoformat(),
                "price_path_risk_exit_ready": "1" if risk_trigger else "0",
                "price_path_risk_exit_type": risk_trigger,
                "price_path_risk_exit_date": risk_date,
                "price_path_risk_exit_price": round(risk_price, 6),
                "exit_family": "price_path_risk_exit",
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
        hold_rows.append(
            {
                "task_id": "Task1423",
                "hold_receipt_row_id": f"HOLD1423-{idx:07d}",
                "policy_variant_id": selected["policy_variant_id"],
                "trade_spec_id": selected["trade_spec_id"],
                "symbol": symbol,
                "entry_date": entry_date.isoformat(),
                "scheduled_exit_date": scheduled_exit.isoformat(),
                "hold_extend_receipt_ready": "1" if hold_trigger else "0",
                "hold_extend_receipt_type": hold_trigger,
                "hold_extend_receipt_ts": hold_ts,
                "assignment_uses_future_outcome": "0",
                "authority": AUTHORITY,
            }
        )
    return source_rows, price_rows, hold_rows


def run_replay(
    selected_specs: list[dict[str, object]],
    specs: dict[str, dict[str, str]],
    source_exits: list[dict[str, object]],
    price_exits: list[dict[str, object]],
    price_cache: dict[str, pd.DataFrame | None],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    source_by_key = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in source_exits}
    price_by_key = {(str(row["policy_variant_id"]), str(row["trade_spec_id"])): row for row in price_exits}
    by_policy_decision: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in selected_specs:
        by_policy_decision[(str(row["policy_variant_id"]), str(row["decision_asof_ts"]))].append(row)
    trades: list[dict[str, object]] = []
    equity: list[dict[str, object]] = []
    for policy_id in POLICIES:
        capital = INITIAL_CAPITAL
        for decision_ts in sorted({key[1] for key in by_policy_decision if key[0] == policy_id}):
            items = by_policy_decision[(policy_id, decision_ts)]
            if not items:
                continue
            per_position = capital / len(items)
            new_capital = capital
            period_pnl = 0.0
            for selected in items:
                spec = specs[str(selected["trade_spec_id"])]
                symbol = str(selected["symbol"])
                frame = load_price(symbol, price_cache)
                entry_after = parse_date(spec["entry_after_date"]) or date(1970, 1, 1)
                scheduled_exit = parse_date(spec["exit_on_or_before_date"]) or entry_after
                entry = price_on_or_after(frame, entry_after)
                if not entry:
                    continue
                entry_date, entry_price = entry
                exit_date = scheduled_exit
                exit_price = 0.0
                exit_reason = "scheduled_exit"
                src = source_by_key.get((policy_id, str(selected["trade_spec_id"])), {})
                px = price_by_key.get((policy_id, str(selected["trade_spec_id"])), {})
                src_ts = parse_ts(str(src.get("source_receipt_ts", "")))
                if str(src.get("source_receipt_exit_ready", "")) == "1" and src_ts:
                    exit_date = src_ts.date()
                    exit_reason = str(src.get("source_receipt_exit_type"))
                elif str(px.get("price_path_risk_exit_ready", "")) == "1":
                    parsed = parse_date(str(px.get("price_path_risk_exit_date", "")))
                    if parsed:
                        exit_date = parsed
                        exit_reason = str(px.get("price_path_risk_exit_type"))
                close = close_on_or_before(frame, exit_date)
                if close:
                    exit_date, exit_price = close[0], close[1]
                else:
                    fallback = close_n_sessions_after(frame, entry_date, 1, scheduled_exit)
                    if not fallback:
                        continue
                    exit_date, exit_price = fallback[0], fallback[1]
                    exit_reason = "fallback_next_available_exit"
                gross_return = pct_return(entry_price, exit_price)
                net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
                pnl = per_position * net_return
                new_capital += pnl
                period_pnl += pnl
                trades.append(
                    {
                        "task_id": "Task1426",
                        "policy_variant_id": policy_id,
                        "trade_spec_id": selected["trade_spec_id"],
                        "candidate_source_id": selected["candidate_source_id"],
                        "symbol": symbol,
                        "decision_asof_ts": decision_ts,
                        "entry_date": entry_date.isoformat(),
                        "entry_price": round(entry_price, 6),
                        "scheduled_exit_date": scheduled_exit.isoformat(),
                        "actual_exit_date": exit_date.isoformat(),
                        "actual_exit_price": round(exit_price, 6),
                        "exit_reason": exit_reason,
                        "capital_allocated": round(per_position, 4),
                        "gross_return": round(gross_return, 8),
                        "net_return": round(net_return, 8),
                        "pnl": round(pnl, 4),
                        "exit_uses_post_entry_price_path": "1" if "price_path" in exit_reason else "0",
                        "source_receipt_exit_used": "1" if "source" in exit_reason else "0",
                        "authority": AUTHORITY,
                    }
                )
            capital = max(new_capital, 0.01)
            equity.append(
                {
                    "task_id": "Task1426",
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
    rows: list[dict[str, object]] = []
    for policy_id, eq_rows in sorted(equity_by_policy.items()):
        tr_rows = trades_by_policy[policy_id]
        slot = POLICIES[policy_id]
        baseline = base_metrics.get(f"l0_l3_slot{slot}_v1", base_metrics["l0_l3_slot5_v1"])
        values = [INITIAL_CAPITAL] + [to_float(row["equity"]) for row in eq_rows]
        final = values[-1]
        start = parse_ts(str(eq_rows[0]["decision_asof_ts"])).date()
        end = max(parse_date(str(row["actual_exit_date"])) or start for row in tr_rows)
        cagr_value = cagr(INITIAL_CAPITAL, final, start, end)
        mdd_value = max_drawdown(values)
        rows.append(
            {
                "task_id": "Task1426",
                "policy_variant_id": policy_id,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr_value, 6),
                "max_drawdown": round(mdd_value, 6),
                "trade_count": len(tr_rows),
                "source_receipt_exit_count": sum(1 for row in tr_rows if row.get("source_receipt_exit_used") == "1"),
                "price_path_exit_count": sum(1 for row in tr_rows if row.get("exit_uses_post_entry_price_path") == "1"),
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


def build_audits(
    metrics: list[dict[str, object]],
    denom: list[dict[str, object]],
    source_exits: list[dict[str, object]],
    price_exits: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    denom_coverage = sum(1 for row in denom if row["denominator_source_gap"] == "0")
    source_exit_ready = sum(1 for row in source_exits if row["source_receipt_exit_ready"] == "1")
    price_exit_ready = sum(1 for row in price_exits if row["price_path_risk_exit_ready"] == "1")
    expert = [
        ("data_audit", f"verified denominator coverage {denom_coverage}/{len(denom)}", "partial_coverage_explicit_gap_not_filled"),
        ("expectation_audit", "analyst PIT remains unavailable", "public guidance proxy only"),
        ("exit_audit", f"source receipt exits {source_exit_ready}; price path risk exits {price_exit_ready}", "exit families separated"),
        ("trading_audit", "top3/top5/top10 replay is diagnostic and frozen before results", "no OOS tuning authorization"),
    ]
    expert_rows = [
        {
            "task_id": "Task1427",
            "audit_id": f"EXPERT1427-{idx:03d}",
            "audit_area": area,
            "finding": finding,
            "decision": decision,
            "authority": AUTHORITY,
        }
        for idx, (area, finding, decision) in enumerate(expert, 1)
    ]
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    gate = [
        {
            "task_id": "Task1427",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "target_cagr_30pct_met": best["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": best["target_mdd_minus30pct_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "diagnostic_ruler_replay_not_accepted",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1427",
            "verdict": "ruler_acquisition_replay_diagnostic_not_accepted",
            "best_policy_variant_id": best["policy_variant_id"],
            "best_final_equity": best["final_equity"],
            "best_cagr": best["cagr"],
            "best_max_drawdown": best["max_drawdown"],
            "denominator_coverage_rows": denom_coverage,
            "source_receipt_exit_ready_rows": source_exit_ready,
            "price_path_risk_exit_ready_rows": price_exit_ready,
            "next_action": "acquire broader verified denominators, true analyst PIT estimates, and non-SEC source receipts",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return expert_rows, gate, closeout


def write_report(metrics: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    best = max(metrics, key=lambda row: to_float(row["final_equity"]))
    report = f"""# Task1408-1427 Ruler Acquisition Replay

## Decision Summary

- Verdict: `ruler_acquisition_replay_diagnostic_not_accepted`.
- Best policy: `{best['policy_variant_id']}`.
- Best final equity: {best['final_equity']}.
- Best CAGR: {best['cagr']}.
- Best MDD: {best['max_drawdown']}.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: scale, expectation, absorption, and exit rulers were split into explicit panels; SEC companyfacts denominators were used only when filed by the decision date; source-receipt exits and price-path exits were separated.
- Next action: broaden verified denominator coverage, acquire true PIT analyst estimates, and attach non-SEC historical source receipts.

## Quant Expert Report

- Data source and source readiness: Task1201 candidates/trade specs, Task1318 full candidate SEC/exhibit sources, Task1388 enriched judgment panels, SEC companyfacts raw files, and daily OHLCV.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`.
- Leakage audit: denominator facts require filed date at or before decision. L2-L4 assignment does not use future PnL, exit price, or post-entry price path. Price-path exits are labeled as L5 diagnostic execution logic, not L2-L4 assignment evidence.
- Expert audit result: GPT/subagent roles are review-only; source-of-truth remains local artifacts and source timestamps.
- Cost/slippage stress: round-trip cost remains {ROUND_TRIP_COST_BPS} bps.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
"""
    for row in sorted(metrics, key=lambda item: str(item["policy_variant_id"])):
        report += (
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | "
            f"{row['trade_count']} | {row['source_receipt_exit_count']} | {row['price_path_exit_count']} | "
            f"{row['beats_baseline_slot']} | {row['beats_benchmark']} | {row['target_cagr_30pct_met']} | {row['target_mdd_minus30pct_met']} |\n"
        )
    report += f"""
## No-Background Decision-Maker Report

눈금자는 일부 확보됐다.

하지만 아직 완성은 아니다.

좋은 점수의 근거가 더 구체화됐고, 매도 사유도 source exit과 price exit으로 갈라졌다.

그래도 전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1408_ruler_expert_review_packet.csv`
- `task1409_scale_ruler_schema.csv`
- `task1410_companyfacts_denominator_panel.csv`
- `task1411_market_cap_proxy_panel.csv`
- `task1412_event_value_panel.csv`
- `task1413_materiality_ruler_panel.csv`
- `task1414_expectation_ruler_schema.csv`
- `task1415_public_guidance_revision_panel.csv`
- `task1416_analyst_pit_audit.csv`
- `task1417_expectation_ruler_panel.csv`
- `task1418_market_absorption_enhanced_panel.csv`
- `task1419_absorption_ruler_panel.csv`
- `task1420_exit_ruler_schema.csv`
- `task1421_source_receipt_exit_panel.csv`
- `task1422_price_path_risk_exit_panel.csv`
- `task1423_hold_extend_receipt_panel.csv`
- `task1424_integrated_ruler_panel.csv`
- `task1425_payoff_ranker_v3.csv`
- `task1426_policy_specs.csv`
- `task1426_replay_trades.csv`
- `task1426_replay_equity.csv`
- `task1426_replay_metrics.csv`
- `task1427_expert_post_audit.csv`
- `task1427_acceptance_gate.csv`
- `task1427_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1408_1427_ruler_acquisition_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1408_1427_ruler_acquisition_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
"""
    (REPORT_DIR / "task_1408_1427_ruler_acquisition_replay.md").write_text(report, encoding="utf-8")
    write_csv(REPORT_DIR / "task_1408_1427_decision.csv", [closeout])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    price_cache: dict[str, pd.DataFrame | None] = {}
    enriched, specs, bindings, filing_bindings, evidence = load_inputs()
    expert_packet = build_expert_review_packet()
    scale_schema, expectation_schema, exit_schema = build_ruler_schema()
    denom, market_cap = build_companyfacts_denominators(enriched, specs, price_cache)
    event_values = build_event_value_panel(enriched, bindings, evidence)
    materiality = build_materiality_ruler(enriched, denom, market_cap, event_values)
    guidance, analyst, expectation = build_guidance_and_expectation(enriched, bindings, evidence)
    absorption_enhanced, absorption_ruler = build_absorption_panels(enriched, filing_bindings, price_cache)
    integrated, rank_rows = build_integrated_and_rank(enriched, materiality, expectation, absorption_ruler)
    selected_specs = build_policy_specs(rank_rows)
    symbol_filings, accession_text = build_filing_indexes(filing_bindings, evidence)
    source_exits, price_exits, hold_receipts = build_exit_panels(selected_specs, specs, symbol_filings, accession_text, price_cache)
    trades, equity = run_replay(selected_specs, specs, source_exits, price_exits, price_cache)
    metrics = build_metrics(trades, equity)
    expert_audit, gate, closeout = build_audits(metrics, denom, source_exits, price_exits)
    outputs = [
        ("task1408_ruler_expert_review_packet.csv", expert_packet),
        ("task1409_scale_ruler_schema.csv", scale_schema),
        ("task1410_companyfacts_denominator_panel.csv", denom),
        ("task1411_market_cap_proxy_panel.csv", market_cap),
        ("task1412_event_value_panel.csv", event_values),
        ("task1413_materiality_ruler_panel.csv", materiality),
        ("task1414_expectation_ruler_schema.csv", expectation_schema),
        ("task1415_public_guidance_revision_panel.csv", guidance),
        ("task1416_analyst_pit_audit.csv", analyst),
        ("task1417_expectation_ruler_panel.csv", expectation),
        ("task1418_market_absorption_enhanced_panel.csv", absorption_enhanced),
        ("task1419_absorption_ruler_panel.csv", absorption_ruler),
        ("task1420_exit_ruler_schema.csv", exit_schema),
        ("task1421_source_receipt_exit_panel.csv", source_exits),
        ("task1422_price_path_risk_exit_panel.csv", price_exits),
        ("task1423_hold_extend_receipt_panel.csv", hold_receipts),
        ("task1424_integrated_ruler_panel.csv", integrated),
        ("task1425_payoff_ranker_v3.csv", rank_rows),
        ("task1426_policy_specs.csv", selected_specs),
        ("task1426_replay_trades.csv", trades),
        ("task1426_replay_equity.csv", equity),
        ("task1426_replay_metrics.csv", metrics),
        ("task1427_expert_post_audit.csv", expert_audit),
        ("task1427_acceptance_gate.csv", gate),
        ("task1427_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_json(OUT_DIR / "task1427_closeout.json", closeout[0])
    write_report(metrics, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
