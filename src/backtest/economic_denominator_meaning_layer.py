from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
COMPANYFACTS_DIR = ROOT / "data/raw/fundamental/sec_companyfacts/companyfacts"
DAILY_DIRS = [ROOT / "data/raw/us_daily_breadth_top500", ROOT / "data/raw/us_daily"]


@dataclass(frozen=True)
class EconomicMeaningPacket:
    lifecycle_id: str
    source_event_id: str
    symbol: str
    event_date: str
    tradable_after_dt: str
    source_form_family: str
    source_circuit: str
    requirement_family: str
    primitive_state: str
    resolver_state: str
    source_availability_json: str
    attached_denominators_json: str
    attached_comparators_json: str
    timing_asof_checks_json: str
    meaning_state: str
    missing_blocker_states: str
    allowed_layer_effects: str
    forbidden_layer_effects: str
    evidence_trace_json: str
    trade_output_flag: int
    score_output_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int
    rule_id: str


@dataclass(frozen=True)
class EconomicMissingSourceBlocker:
    lifecycle_id: str
    source_event_id: str
    symbol: str
    source_circuit: str
    requirement_family: str
    blocker_state: str
    blocker_reason: str
    required_source: str
    research_only_flag: int
    backtest_eligible_flag: int
    rule_id: str


def build_economic_meaning_packets(
    primitives: pd.DataFrame,
    resolvers: pd.DataFrame,
    event_detail: pd.DataFrame,
    *,
    root: Path = ROOT,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    event_map = {str(row["event_id"]): row for _, row in event_detail.iterrows()}
    primitive_map = {str(row["source_event_id"]): row for _, row in primitives.iterrows()}
    fact_cache: dict[str, dict[str, Any]] = {}
    price_cache: dict[str, pd.DataFrame] = {}
    packet_rows = []
    blocker_rows = []
    for _, resolver in resolvers.iterrows():
        event = event_map.get(str(resolver["source_event_id"]), pd.Series(dtype=object))
        primitive_row = primitive_map.get(str(resolver["source_event_id"]), pd.Series(dtype=object))
        packet, blockers = build_packet_for_row(resolver, primitive_row, event, fact_cache, price_cache, root=root)
        packet_rows.append(asdict(packet))
        blocker_rows.extend(asdict(blocker) for blocker in blockers)
    return pd.DataFrame(packet_rows), pd.DataFrame(blocker_rows)


def build_packet_for_row(
    resolver: pd.Series,
    primitive_row: pd.Series,
    event: pd.Series,
    fact_cache: dict[str, dict[str, Any]],
    price_cache: dict[str, pd.DataFrame],
    *,
    root: Path = ROOT,
) -> tuple[EconomicMeaningPacket, list[EconomicMissingSourceBlocker]]:
    symbol = text(resolver.get("symbol"))
    event_date = first_nonempty(text(event.get("event_date")), date_from_source_event_id(text(resolver.get("source_event_id"))))
    tradable_after = text(event.get("tradable_after_dt"))
    event_dt = parse_dt(event_date)
    tradable_dt = parse_dt(tradable_after) or event_dt
    primitive = parse_json(primitive_row.get("primitive_fields_json"))
    companyfacts = companyfacts_snapshot(symbol, event_dt, fact_cache)
    price = price_snapshot(symbol, tradable_dt, price_cache, root=root)
    denominators = attach_denominators(symbol, companyfacts, price)
    comparators = attach_comparators(resolver, primitive, companyfacts, price)
    availability = source_availability(event, primitive_row, companyfacts, price, denominators, comparators)
    timing = timing_checks(event_dt, tradable_dt, companyfacts, price)
    meaning_state, missing = resolve_meaning_state(resolver, primitive, denominators, comparators, availability)
    packet = EconomicMeaningPacket(
        lifecycle_id=text(resolver.get("lifecycle_id")),
        source_event_id=text(resolver.get("source_event_id")),
        symbol=symbol,
        event_date=event_date,
        tradable_after_dt=tradable_after,
        source_form_family=text(event.get("source_form_family")),
        source_circuit=text(resolver.get("source_circuit")),
        requirement_family=text(resolver.get("requirement_family")),
        primitive_state=text(primitive_row.get("extractor_state")),
        resolver_state=text(resolver.get("resolver_state")),
        source_availability_json=json.dumps(availability, ensure_ascii=False, sort_keys=True),
        attached_denominators_json=json.dumps(denominators, ensure_ascii=False, sort_keys=True),
        attached_comparators_json=json.dumps(comparators, ensure_ascii=False, sort_keys=True),
        timing_asof_checks_json=json.dumps(timing, ensure_ascii=False, sort_keys=True),
        meaning_state=meaning_state,
        missing_blocker_states="|".join(missing),
        allowed_layer_effects=text(resolver.get("allowed_layer_effects")),
        forbidden_layer_effects="buy_sell|score_rank|trade_ready|backtest_ready|outcome_label",
        evidence_trace_json=json.dumps(
            {
                "task740_primitive_rule_id": text(primitive_row.get("rule_id")),
                "task740_resolver_rule_id": text(resolver.get("rule_id")),
                "companyfacts_path": companyfacts.get("path", ""),
                "daily_price_path": price.get("path", ""),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        trade_output_flag=0,
        score_output_flag=0,
        backtest_eligible_flag=0,
        outcome_used_for_assignment_flag=0,
        rule_id="TASK741_ECONOMIC_DENOMINATOR_MEANING_PACKET_REVIEW_ONLY",
    )
    blockers = [
        EconomicMissingSourceBlocker(
            lifecycle_id=text(resolver.get("lifecycle_id")),
            source_event_id=text(resolver.get("source_event_id")),
            symbol=symbol,
            source_circuit=text(resolver.get("source_circuit")),
            requirement_family=text(resolver.get("requirement_family")),
            blocker_state=blocker,
            blocker_reason=blocker_reason(blocker),
            required_source=required_source(blocker),
            research_only_flag=1,
            backtest_eligible_flag=0,
            rule_id="TASK741_ECONOMIC_MISSING_SOURCE_BLOCKER",
        )
        for blocker in missing
        if blocker.endswith("_missing") or blocker.endswith("_blocked") or blocker.endswith("_needed")
    ]
    return packet, blockers


def resolve_meaning_state(
    resolver: pd.Series,
    primitive: dict[str, Any],
    denominators: dict[str, Any],
    comparators: dict[str, Any],
    availability: dict[str, Any],
) -> tuple[str, list[str]]:
    circuit = text(resolver.get("source_circuit"))
    state = text(resolver.get("resolver_state"))
    missing: list[str] = []
    if circuit == "form4_insider_behavior":
        pct_holdings = safe_ratio(primitive.get("shares_changed"), primitive.get("ownership_after"))
        pct_outstanding = safe_ratio(primitive.get("shares_changed"), denominators.get("shares_outstanding"))
        if pct_holdings is not None or pct_outstanding is not None or denominators.get("estimated_transaction_value"):
            meaning = "insider_transaction_size_attached_source_only"
        else:
            meaning = "insider_context_denominator_blocked"
        if denominators.get("market_cap_proxy"):
            meaning = "insider_transaction_size_market_cap_context"
        if "automatic_plan" in state:
            meaning = "insider_plan_pattern_context"
        missing.extend(["exact_person_history_missing", "insider_total_holdings_missing"])
        if primitive.get("ownership_after") in {None, "", 0}:
            missing.append("ownership_after_missing")
        return meaning, missing
    if circuit in {"ownership_float_structure", "activist_control"}:
        if primitive.get("ownership_percent_present_flag"):
            meaning = "ownership_percent_source_attached"
        elif state in {"passive_ownership_context"}:
            meaning = "passive_ownership_context_attached"
        elif state in {"active_control_intent_review", "control_intent_unknown"}:
            meaning = "active_control_context_attached"
        elif denominators.get("market_cap_proxy"):
            meaning = "ownership_market_cap_context_attached"
        else:
            meaning = "ownership_float_denominator_blocked"
        if not availability["has_free_float"]:
            missing.append("free_float_missing")
        missing.append("prior_holder_percent_missing")
        if not primitive.get("ownership_percent_present_flag"):
            missing.append("ownership_percent_missing")
        return meaning, missing
    if circuit == "credit_financing":
        if primitive.get("principal_amount") and denominators.get("market_cap_proxy"):
            meaning = "financing_principal_market_cap_context"
        elif denominators.get("cash") is not None or denominators.get("debt") is not None:
            meaning = "financing_cash_debt_context"
        elif "growth" in state:
            meaning = "growth_funding_review_context"
        elif "dilution" in state:
            meaning = "dilution_overhang_review_context"
        elif "liquidity" in state:
            meaning = "liquidity_review_context"
        else:
            meaning = "financing_denominator_blocked"
        if not primitive.get("principal_amount"):
            missing.append("principal_amount_missing")
        if denominators.get("cash") is None:
            missing.append("cash_fact_missing")
        if denominators.get("debt") is None:
            missing.append("debt_fact_missing")
        if not denominators.get("market_cap_proxy"):
            missing.append("market_cap_proxy_missing")
        if primitive.get("instrument_convertible_flag") or primitive.get("instrument_warrant_flag"):
            missing.append("dilution_terms_incomplete")
        return meaning, missing
    if circuit == "financial_results_guidance":
        if denominators.get("revenue") is not None:
            meaning = "revenue_baseline_attached"
        elif denominators.get("cash") is not None or denominators.get("debt") is not None:
            meaning = "cash_debt_context_attached"
        elif primitive.get("guidance_language_flag"):
            meaning = "guidance_language_context_only"
        else:
            meaning = "financial_result_source_only_context"
        missing.extend(["consensus_estimates_missing", "prior_guidance_database_missing"])
        if primitive.get("margin_language_flag"):
            missing.append("margin_bridge_missing")
        return meaning, missing
    if circuit == "generic_8k_classifier":
        if state == "financing_route_required":
            return "generic_8k_financing_route_context", ["explicit_operating_transmission_missing"]
        if state == "mna_route_required":
            return "generic_8k_mna_route_context", ["explicit_operating_transmission_missing"]
        if state in {"governance_context_only", "compensation_context_only"}:
            return "generic_8k_governance_route_context", []
        if state == "operating_transmission_needed":
            return "generic_8k_operating_transmission_blocked", ["explicit_operating_transmission_missing", "item_101_only_not_sufficient"]
        return "generic_8k_non_operating_route_confirmed", []
    return "economic_meaning_context_only", ["economic_resolver_missing"]


def attach_denominators(symbol: str, companyfacts: dict[str, Any], price: dict[str, Any]) -> dict[str, Any]:
    shares = companyfacts.get("shares_outstanding")
    close_price = price.get("close")
    market_cap = close_price * shares if close_price is not None and shares is not None else None
    return {
        "shares_outstanding": shares,
        "public_float_usd": companyfacts.get("public_float_usd"),
        "cash": companyfacts.get("cash"),
        "debt": companyfacts.get("debt"),
        "revenue": companyfacts.get("revenue"),
        "close_price": close_price,
        "market_cap_proxy": market_cap,
        "companyfacts_asof": companyfacts.get("asof", ""),
        "companyfacts_filed": companyfacts.get("filed", ""),
        "price_asof": price.get("asof", ""),
    }


def attach_comparators(resolver: pd.Series, primitive: dict[str, Any], companyfacts: dict[str, Any], price: dict[str, Any]) -> dict[str, Any]:
    shares_changed = primitive.get("shares_changed")
    ownership_after = primitive.get("ownership_after")
    principal = primitive.get("principal_amount")
    shares = companyfacts.get("shares_outstanding")
    market_cap = price.get("close") * shares if price.get("close") is not None and shares is not None else None
    return {
        "shares_changed_pct_of_ownership_after": safe_ratio(shares_changed, ownership_after),
        "shares_changed_pct_of_shares_outstanding": safe_ratio(shares_changed, shares),
        "principal_pct_of_market_cap": safe_ratio(principal, market_cap),
        "principal_pct_of_cash": safe_ratio(principal, companyfacts.get("cash")),
        "principal_pct_of_debt": safe_ratio(principal, companyfacts.get("debt")),
        "ownership_percent_source": primitive.get("ownership_percent"),
        "has_prior_guidance_comparator": False,
        "has_consensus_comparator": False,
        "has_exact_insider_history": False,
        "has_prior_holder_percent": False,
    }


def source_availability(event: pd.Series, primitive_row: pd.Series, companyfacts: dict[str, Any], price: dict[str, Any], denominators: dict[str, Any], comparators: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_task740_primitive": not primitive_row.empty,
        "has_task722_event_detail": not event.empty,
        "has_raw_text_path": bool(text(event.get("raw_text_path"))),
        "has_event_date": bool(text(event.get("event_date"))),
        "has_tradable_after_dt": bool(text(event.get("tradable_after_dt"))),
        "has_sec_companyfacts": bool(companyfacts.get("path")),
        "has_shares_outstanding_fact": denominators.get("shares_outstanding") is not None,
        "has_public_float_fact": denominators.get("public_float_usd") is not None,
        "has_revenue_fact": denominators.get("revenue") is not None,
        "has_cash_fact": denominators.get("cash") is not None,
        "has_debt_fact": denominators.get("debt") is not None,
        "has_daily_price": price.get("close") is not None,
        "has_market_cap_proxy": denominators.get("market_cap_proxy") is not None,
        "has_free_float": False,
        "has_consensus_estimates": False,
        "has_prior_guidance_database": False,
        "has_exact_insider_history": False,
    }


def timing_checks(event_dt: datetime | None, tradable_dt: datetime | None, companyfacts: dict[str, Any], price: dict[str, Any]) -> dict[str, Any]:
    fact_end = parse_dt(companyfacts.get("asof"))
    fact_filed = parse_dt(companyfacts.get("filed"))
    price_asof = parse_dt(price.get("asof"))
    return {
        "event_date_present": event_dt is not None,
        "tradable_after_dt_present": tradable_dt is not None,
        "denominator_asof_lte_event": bool(fact_end and event_dt and fact_end <= event_dt),
        "companyfacts_filed_lte_event": bool(fact_filed and event_dt and fact_filed <= event_dt),
        "price_asof_lte_tradable_after": bool(price_asof and tradable_dt and price_asof <= tradable_dt),
        "sec_fact_period_end_lte_event": bool(fact_end and event_dt and fact_end <= event_dt),
        "no_future_data_used": no_future_data_used(event_dt, tradable_dt, fact_end, fact_filed, price_asof),
    }


def no_future_data_used(
    event_dt: datetime | None,
    tradable_dt: datetime | None,
    fact_end: datetime | None,
    fact_filed: datetime | None,
    price_asof: datetime | None,
) -> bool:
    if fact_end and event_dt and fact_end > event_dt:
        return False
    if fact_filed and event_dt and fact_filed > event_dt:
        return False
    if price_asof and tradable_dt and price_asof > tradable_dt:
        return False
    return True


def companyfacts_snapshot(symbol: str, event_dt: datetime | None, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    key = f"{symbol}|{event_dt.date().isoformat() if event_dt else 'none'}"
    if key in cache:
        return cache[key]
    path = next(iter(COMPANYFACTS_DIR.glob(f"{symbol}_*.json")), None)
    if not path:
        cache[key] = {}
        return cache[key]
    obj = json.loads(path.read_text(encoding="utf-8"))
    facts = obj.get("facts", {})
    snapshot = {
        "path": str(path.relative_to(ROOT)),
        "shares_outstanding": latest_fact(facts, "EntityCommonStockSharesOutstanding", "shares", event_dt),
        "public_float_usd": latest_fact(facts, "EntityPublicFloat", "USD", event_dt),
        "cash": first_latest_fact(facts, ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"], "USD", event_dt),
        "debt": sum_latest_facts(facts, ["LongTermDebt", "LongTermDebtCurrent", "ShortTermBorrowings"], "USD", event_dt),
        "revenue": first_latest_fact(facts, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"], "USD", event_dt),
    }
    latest_meta = latest_meta_any(facts, event_dt)
    snapshot.update(latest_meta)
    cache[key] = snapshot
    return snapshot


def latest_fact(facts: dict[str, Any], concept: str, unit: str, event_dt: datetime | None) -> float | None:
    for namespace in facts.values():
        if concept not in namespace:
            continue
        arr = namespace[concept].get("units", {}).get(unit, [])
        record = latest_record(arr, event_dt)
        if record:
            return float(record.get("val"))
    return None


def first_latest_fact(facts: dict[str, Any], concepts: list[str], unit: str, event_dt: datetime | None) -> float | None:
    for concept in concepts:
        value = latest_fact(facts, concept, unit, event_dt)
        if value is not None:
            return value
    return None


def sum_latest_facts(facts: dict[str, Any], concepts: list[str], unit: str, event_dt: datetime | None) -> float | None:
    values = [latest_fact(facts, concept, unit, event_dt) for concept in concepts]
    values = [value for value in values if value is not None]
    return sum(values) if values else None


def latest_meta_any(facts: dict[str, Any], event_dt: datetime | None) -> dict[str, str]:
    records = []
    for namespace in facts.values():
        for concept in namespace.values():
            for arr in concept.get("units", {}).values():
                for record in arr:
                    parsed = parse_dt(record.get("end"))
                    filed = parse_dt(record.get("filed"))
                    if parsed and event_dt and parsed <= event_dt and (not filed or filed <= event_dt):
                        records.append(record)
    if not records:
        return {"asof": "", "filed": ""}
    records.sort(key=lambda r: (str(r.get("end", "")), str(r.get("filed", ""))))
    return {"asof": str(records[-1].get("end", "")), "filed": str(records[-1].get("filed", ""))}


def latest_record(arr: list[dict[str, Any]], event_dt: datetime | None) -> dict[str, Any] | None:
    candidates = []
    for record in arr:
        end = parse_dt(record.get("end"))
        filed = parse_dt(record.get("filed"))
        if not event_dt:
            continue
        if end and end <= event_dt and (not filed or filed <= event_dt):
            candidates.append(record)
    if not candidates:
        return None
    candidates.sort(key=lambda r: (str(r.get("end", "")), str(r.get("filed", ""))))
    return candidates[-1]


def price_snapshot(symbol: str, tradable_dt: datetime | None, cache: dict[str, pd.DataFrame], *, root: Path = ROOT) -> dict[str, Any]:
    if symbol not in cache:
        path = None
        for directory in DAILY_DIRS:
            candidate = directory / f"{symbol}.csv"
            if candidate.exists():
                path = candidate
                break
        if not path:
            cache[symbol] = pd.DataFrame()
        else:
            frame = pd.read_csv(path)
            frame["parsed_ts"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
            frame["source_path"] = str(path.relative_to(root))
            cache[symbol] = frame
    frame = cache[symbol]
    if frame.empty or tradable_dt is None:
        return {}
    eligible = frame[frame["parsed_ts"] <= pd.Timestamp(tradable_dt)]
    if eligible.empty:
        return {}
    row = eligible.sort_values("parsed_ts").iloc[-1]
    return {"close": float(row["close"]), "asof": row["parsed_ts"].date().isoformat(), "path": str(row["source_path"])}


def parse_json(value: object) -> dict[str, Any]:
    if value is None or pd.isna(value):
        return {}
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def safe_ratio(numerator: object, denominator: object) -> float | None:
    try:
        n = float(numerator)
        d = float(denominator)
    except (TypeError, ValueError):
        return None
    if d == 0:
        return None
    return n / d


def date_from_source_event_id(event_id: str) -> str:
    parts = event_id.split("|")
    return parts[2] if len(parts) >= 3 else ""


def first_nonempty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def parse_dt(value: object) -> datetime | None:
    text_value = text(value)
    if not text_value:
        return None
    try:
        return pd.Timestamp(text_value).to_pydatetime().astimezone(timezone.utc)
    except Exception:
        return None


def text(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def blocker_reason(blocker: str) -> str:
    return {
        "insider_total_holdings_missing": "Exact insider total holdings and role history are not available as a reliable joined source.",
        "exact_person_history_missing": "Prior exact-person insider behavior history is not joined yet.",
        "ownership_after_missing": "Form4 ownership-after primitive is missing or not parseable.",
        "free_float_missing": "Free float share denominator is not available; SEC public float USD is not the same as free float shares.",
        "prior_holder_percent_missing": "Prior holder percent database is not joined.",
        "ownership_percent_missing": "Ownership percent is not present in parsed source text.",
        "principal_amount_missing": "Financing principal amount was not extracted from source text.",
        "cash_fact_missing": "SEC companyfacts cash denominator is missing as-of event date.",
        "debt_fact_missing": "SEC companyfacts debt denominator is missing as-of event date.",
        "market_cap_proxy_missing": "Market cap proxy cannot be computed from as-of price and shares outstanding.",
        "dilution_terms_incomplete": "Convertible or warrant economics need conversion, warrant, hedge, and share issuance details.",
        "consensus_estimates_missing": "Consensus estimates are not available in local raw sources.",
        "prior_guidance_database_missing": "Prior guidance baseline database is not available.",
        "margin_bridge_missing": "Margin bridge needs segment mix and one-off adjustments.",
        "explicit_operating_transmission_missing": "8-K route lacks explicit operating transmission evidence.",
        "item_101_only_not_sufficient": "Item 1.01 alone cannot support operating transmission.",
    }.get(blocker, "Required economic source is missing.")


def required_source(blocker: str) -> str:
    if "consensus" in blocker:
        return "licensed_or_verified_consensus_estimates"
    if "guidance" in blocker:
        return "prior_guidance_database"
    if "float" in blocker:
        return "free_float_shares_source"
    if "insider" in blocker or "person_history" in blocker:
        return "exact_insider_history_store"
    if "market_cap" in blocker:
        return "daily_price_and_shares_outstanding_asof"
    if "cash" in blocker or "debt" in blocker:
        return "sec_companyfacts_asof"
    return "source_or_denominator_join"
