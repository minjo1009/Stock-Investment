from __future__ import annotations

import html
import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
COMPANYFACTS_DIR = ROOT / "data/raw/fundamental/sec_companyfacts/companyfacts"

MONEY_RE = re.compile(
    r"(?P<prefix>\$|USD\s*)\s?(?P<number>\d+(?:,\d{3})*(?:\.\d+)?)\s?(?P<scale>billion|million|thousand|bn|mm|m|k)?",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"(?P<number>\d+(?:\.\d+)?)\s?(?P<unit>year|years|yr|yrs|month|months)", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")

REVENUE_TAGS = [
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
]
CASH_TAGS = [
    "CashAndCashEquivalentsAtCarryingValue",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
]
DEBT_TAGS = [
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "DebtCurrent",
    "DebtNoncurrent",
    "ShortTermBorrowings",
    "ConvertibleNotesPayable",
]
BACKLOG_PROXY_TAGS = [
    "ContractWithCustomerLiabilityCurrent",
    "ContractWithCustomerLiabilityNoncurrent",
    "ContractWithCustomerLiability",
]
PUBLIC_FLOAT_TAGS = ["EntityPublicFloat"]


@dataclass(frozen=True)
class PrimitiveFacts:
    stated_amount_usd: float | None
    stated_amount_count: int
    max_amount_span: str
    duration_months: float | None
    named_counterparty_flag: int
    funded_status: str
    guidance_direction_state: str
    margin_language_state: str
    financing_terms_state: str
    use_of_proceeds_state: str
    raw_operational_span: str


@dataclass(frozen=True)
class DenominatorSnapshot:
    revenue_run_rate_usd: float | None
    revenue_filed_date: str
    cash_usd: float | None
    cash_filed_date: str
    debt_usd: float | None
    debt_filed_date: str
    backlog_proxy_usd: float | None
    backlog_proxy_filed_date: str
    public_float_usd: float | None
    public_float_filed_date: str
    denominator_available_count: int
    denominator_source_status: str


@dataclass(frozen=True)
class EconomicRealityPacket:
    evidence_viability_state: str
    primitive_fact_state: str
    denominator_state: str
    expectation_state: str
    economic_meaning_state: str
    task729_injection_state: str
    primitive_fact_gate_pass_flag: int
    source_denominator_gate_pass_flag: int
    backtest_eligible_flag: int


def build_event_reality_packet(row: pd.Series, *, root: Path = ROOT) -> dict[str, object]:
    raw_text = read_raw_text(row.get("raw_text_path"), root=root)
    evidence_span = clean_missing(row.get("content_interpretation_evidence_span"))
    clean_text = normalize_text(evidence_span or raw_text)
    allow_extraction = source_allows_primitive_extraction(row)
    facts = extract_primitive_facts(row, clean_text, allow_extraction=allow_extraction)
    denominators = denominator_snapshot(str(row.get("symbol", "")), str(row.get("entry_ts", "")))
    reality = classify_reality_packet(row, facts, denominators)
    ratios = compute_ratios(facts, denominators)
    return {
        **key_fields(row),
        "event_id": row.get("event_id", ""),
        "source_form_family": row.get("source_form_family", ""),
        "interpretation_blocker": row.get("interpretation_blocker", ""),
        "source_text_certified_flag": int_safe(row.get("source_text_certified_flag")),
        "economic_evidence_certified_flag": int_safe(row.get("economic_evidence_certified_flag")),
        **asdict(facts),
        **asdict(denominators),
        **ratios,
        **asdict(reality),
        "raw_text_available_flag": int(bool(raw_text)),
        "outcome_used_for_assignment_flag": 0,
    }


def extract_primitive_facts(row: pd.Series, text: str, *, allow_extraction: bool = True) -> PrimitiveFacts:
    if not allow_extraction:
        return PrimitiveFacts(
            stated_amount_usd=None,
            stated_amount_count=0,
            max_amount_span="",
            duration_months=None,
            named_counterparty_flag=0,
            funded_status="source_non_operational_not_extracted",
            guidance_direction_state="source_non_operational_not_extracted",
            margin_language_state="source_non_operational_not_extracted",
            financing_terms_state="source_non_operational_not_extracted",
            use_of_proceeds_state="source_non_operational_not_extracted",
            raw_operational_span=short_span(text),
        )
    amounts = [(money_to_usd(m), m.group(0)) for m in MONEY_RE.finditer(text)]
    amounts = [(value, span) for value, span in amounts if value is not None]
    max_amount = max(amounts, key=lambda item: item[0]) if amounts else (None, "")
    duration = extract_duration_months(text)
    return PrimitiveFacts(
        stated_amount_usd=max_amount[0],
        stated_amount_count=len(amounts),
        max_amount_span=max_amount[1],
        duration_months=duration,
        named_counterparty_flag=int_safe(row.get("content_named_customer_or_counterparty")),
        funded_status=classify_funded_status(text),
        guidance_direction_state=classify_guidance(row, text),
        margin_language_state=classify_margin(text),
        financing_terms_state=classify_financing_terms(text),
        use_of_proceeds_state=classify_use_of_proceeds(text),
        raw_operational_span=short_span(text),
    )


def classify_reality_packet(
    row: pd.Series,
    facts: PrimitiveFacts,
    denominators: DenominatorSnapshot,
) -> EconomicRealityPacket:
    source_family = str(row.get("source_form_family", ""))
    blocker = clean_missing(row.get("interpretation_blocker"))
    economic_certified = int_safe(row.get("economic_evidence_certified_flag"))
    source_certified = int_safe(row.get("source_text_certified_flag"))
    blocked_family = source_family in {"form4_insider", "schedule_13d_13g", "form_13f", "ownership_or_institutional_filing"}

    if not source_certified:
        evidence_state = "source_text_missing"
    elif blocker == "financing_context_requires_separate_review":
        evidence_state = "source_certified_financing_context_review_required"
    elif blocked_family or blocker:
        evidence_state = "blocked_or_non_operational_source"
    elif economic_certified:
        evidence_state = "source_certified_operational_economic"
    else:
        evidence_state = "source_certified_needs_semantic_review"

    primitive_count = sum(
        [
            int(facts.stated_amount_usd is not None),
            int(facts.duration_months is not None),
            facts.named_counterparty_flag,
            int(facts.guidance_direction_state not in {"guidance_unknown", "source_non_operational_not_extracted"}),
            int(facts.margin_language_state not in {"margin_unknown", "source_non_operational_not_extracted"}),
            int(facts.financing_terms_state not in {"financing_terms_none", "source_non_operational_not_extracted"}),
            int(facts.use_of_proceeds_state not in {"use_of_proceeds_unknown", "source_non_operational_not_extracted"}),
        ]
    )
    primitive_state = "primitive_fact_missing" if primitive_count == 0 else "primitive_fact_partial"
    if primitive_count >= 3 and evidence_state == "source_certified_operational_economic":
        primitive_state = "primitive_fact_operational_packet"

    denominator_state = (
        "denominator_missing"
        if denominators.denominator_available_count == 0
        else "denominator_partial_available"
    )
    if denominators.revenue_run_rate_usd and facts.stated_amount_usd:
        denominator_state = "amount_revenue_denominator_available"

    expectation_state = classify_expectation_state(facts)
    economic_meaning = classify_economic_meaning(facts, denominators, evidence_state, primitive_state)
    primitive_pass = int(primitive_state == "primitive_fact_operational_packet")
    denominator_pass = int(denominator_state == "amount_revenue_denominator_available")
    injection_state = classify_injection_state(evidence_state, primitive_state, denominator_state, economic_meaning)

    return EconomicRealityPacket(
        evidence_viability_state=evidence_state,
        primitive_fact_state=primitive_state,
        denominator_state=denominator_state,
        expectation_state=expectation_state,
        economic_meaning_state=economic_meaning,
        task729_injection_state=injection_state,
        primitive_fact_gate_pass_flag=primitive_pass,
        source_denominator_gate_pass_flag=int(primitive_pass and denominator_pass),
        backtest_eligible_flag=0,
    )


def classify_injection_state(evidence_state: str, primitive_state: str, denominator_state: str, economic_meaning: str) -> str:
    if evidence_state in {"source_text_missing", "blocked_or_non_operational_source"}:
        return "task729_source_blocker_unchanged"
    if primitive_state == "primitive_fact_missing":
        return "task729_needs_primitive_fact"
    if denominator_state == "denominator_missing":
        return "task729_needs_denominator"
    if "material" in economic_meaning:
        return "task729_economic_reality_review_candidate"
    return "task729_reality_packet_review_only"


def classify_economic_meaning(
    facts: PrimitiveFacts,
    denominators: DenominatorSnapshot,
    evidence_state: str,
    primitive_state: str,
) -> str:
    if evidence_state in {"source_text_missing", "blocked_or_non_operational_source"}:
        return "economic_meaning_not_evaluated_non_operational_source"
    if primitive_state == "primitive_fact_missing":
        return "economic_meaning_not_interpretable"
    if facts.stated_amount_usd and denominators.revenue_run_rate_usd:
        ratio = safe_ratio(facts.stated_amount_usd, denominators.revenue_run_rate_usd)
        if ratio is not None and ratio >= 0.10:
            return "material_amount_vs_revenue_needs_full_context"
        return "amount_vs_revenue_small_or_uncertain"
    if facts.financing_terms_state != "financing_terms_none":
        return "financing_reality_packet_needs_use_of_proceeds_and_dilution"
    return "economic_meaning_partial_needs_denominator"


def source_allows_primitive_extraction(row: pd.Series) -> bool:
    source_family = str(row.get("source_form_family", ""))
    blocker = clean_missing(row.get("interpretation_blocker"))
    non_operational_families = {
        "form4_insider",
        "schedule_13d_13g",
        "form_13f",
        "ownership_or_institutional_filing",
        "macro_policy_or_geopolitical_source",
    }
    hard_blockers = {
        "ownership_or_insider_filing_blocker",
        "generic_sec_boilerplate_weak_keyword_blocker",
        "governance_or_compensation_filing_blocker",
    }
    if blocker == "financing_context_requires_separate_review":
        return True
    if source_family in non_operational_families:
        return False
    return blocker not in hard_blockers


@lru_cache(maxsize=4096)
def denominator_snapshot(symbol: str, entry_ts: str) -> DenominatorSnapshot:
    facts = load_companyfacts(symbol)
    asof = pd.to_datetime(entry_ts, utc=True, errors="coerce")
    revenue = latest_fact_value(facts, REVENUE_TAGS, asof, prefer_duration=True)
    cash = latest_fact_value(facts, CASH_TAGS, asof)
    debt_values = [latest_fact_value(facts, [tag], asof) for tag in DEBT_TAGS]
    debt_present = [item for item in debt_values if item[0] is not None]
    debt_val = sum(float(item[0]) for item in debt_present) if debt_present else None
    debt_date = max((item[1] for item in debt_present if item[1]), default="")
    backlog = latest_fact_value(facts, BACKLOG_PROXY_TAGS, asof)
    public_float = latest_fact_value(facts, PUBLIC_FLOAT_TAGS, asof)
    available = sum(
        int(x is not None)
        for x in [revenue[0], cash[0], debt_val, backlog[0], public_float[0]]
    )
    return DenominatorSnapshot(
        revenue_run_rate_usd=revenue[0],
        revenue_filed_date=revenue[1],
        cash_usd=cash[0],
        cash_filed_date=cash[1],
        debt_usd=debt_val,
        debt_filed_date=debt_date,
        backlog_proxy_usd=backlog[0],
        backlog_proxy_filed_date=backlog[1],
        public_float_usd=public_float[0],
        public_float_filed_date=public_float[1],
        denominator_available_count=available,
        denominator_source_status="sec_companyfacts_asof" if available else "denominator_missing_or_symbol_not_found",
    )


@lru_cache(maxsize=256)
def load_companyfacts(symbol: str) -> dict[str, Any]:
    if not symbol:
        return {}
    matches = sorted(COMPANYFACTS_DIR.glob(f"{symbol}_*.json"))
    if not matches:
        return {}
    with matches[0].open("r", encoding="utf-8") as f:
        return json.load(f)


def latest_fact_value(
    facts: dict[str, Any],
    tags: list[str],
    asof: pd.Timestamp,
    *,
    prefer_duration: bool = False,
) -> tuple[float | None, str]:
    if not facts or pd.isna(asof):
        return None, ""
    candidates: list[dict[str, Any]] = []
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    dei = facts.get("facts", {}).get("dei", {})
    for tag in tags:
        item = us_gaap.get(tag) or dei.get(tag) or {}
        for unit_items in item.get("units", {}).values():
            for point in unit_items:
                filed = pd.to_datetime(point.get("filed"), utc=True, errors="coerce")
                if pd.isna(filed) or filed > asof:
                    continue
                if prefer_duration and "start" not in point:
                    continue
                if point.get("val") is None:
                    continue
                candidates.append(point)
    if not candidates:
        return None, ""
    candidates.sort(key=lambda p: (str(p.get("filed", "")), str(p.get("end", ""))))
    chosen = candidates[-1]
    value = float(chosen["val"])
    if prefer_duration:
        start = pd.to_datetime(chosen.get("start"), utc=True, errors="coerce")
        end = pd.to_datetime(chosen.get("end"), utc=True, errors="coerce")
        if not pd.isna(start) and not pd.isna(end):
            days = max((end - start).days, 1)
            if days < 330:
                value = value * (365.0 / days)
    return value, str(chosen.get("filed", ""))


def compute_ratios(facts: PrimitiveFacts, denominators: DenominatorSnapshot) -> dict[str, float | None]:
    amount = facts.stated_amount_usd
    return {
        "amount_to_revenue_run_rate": safe_ratio(amount, denominators.revenue_run_rate_usd),
        "amount_to_cash": safe_ratio(amount, denominators.cash_usd),
        "amount_to_debt": safe_ratio(amount, denominators.debt_usd),
        "amount_to_backlog_proxy": safe_ratio(amount, denominators.backlog_proxy_usd),
        "amount_to_public_float": safe_ratio(amount, denominators.public_float_usd),
    }


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(float(numerator) / float(denominator), 6)


def read_raw_text(path_value: object, *, root: Path = ROOT) -> str:
    if not isinstance(path_value, str) or not path_value:
        return ""
    path = Path(path_value)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def clean_missing(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = TAG_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def money_to_usd(match: re.Match[str]) -> float | None:
    number = float(match.group("number").replace(",", ""))
    scale = (match.group("scale") or "").lower()
    if scale in {"billion", "bn"}:
        number *= 1_000_000_000
    elif scale in {"million", "mm", "m"}:
        number *= 1_000_000
    elif scale in {"thousand", "k"}:
        number *= 1_000
    return number


def extract_duration_months(text: str) -> float | None:
    match = YEAR_RE.search(text)
    if not match:
        return None
    value = float(match.group("number"))
    unit = match.group("unit").lower()
    return value * 12.0 if unit.startswith(("year", "yr")) else value


def classify_funded_status(text: str) -> str:
    lower = text.lower()
    if "unfunded" in lower:
        return "unfunded"
    if "funded" in lower:
        return "funded"
    if "framework" in lower or "indefinite delivery" in lower or "idiq" in lower:
        return "framework_or_indefinite"
    return "funded_status_unknown"


def classify_guidance(row: pd.Series, text: str) -> str:
    existing = str(row.get("guidance_direction_state", ""))
    lower = text.lower()
    if "reaffirm" in lower or "reaffirmed" in lower or existing == "guidance_reaffirm":
        return "guidance_reaffirm"
    if "raise" in lower or "raised" in lower or "increase" in lower or existing == "guidance_raise":
        return "guidance_raise_or_increase"
    if "cut" in lower or "lower" in lower or "reduced" in lower:
        return "guidance_cut_or_lower"
    if "guidance" in lower or "outlook" in lower or "forecast" in lower:
        return "guidance_mentioned_direction_unknown"
    return "guidance_unknown"


def classify_margin(text: str) -> str:
    lower = text.lower()
    if "margin" not in lower and "gross profit" not in lower:
        return "margin_unknown"
    if "accretive" in lower or "expansion" in lower or "improve" in lower:
        return "margin_positive_language"
    if "dilutive" in lower or "pressure" in lower or "decline" in lower:
        return "margin_negative_language"
    return "margin_mentioned_direction_unknown"


def classify_financing_terms(text: str) -> str:
    lower = text.lower()
    if "convertible" in lower or "conversion" in lower:
        return "convertible_or_conversion_terms"
    if "warrant" in lower:
        return "warrant_terms"
    if "atm" in lower or "at-the-market" in lower or "offering" in lower:
        return "equity_offering_or_atm"
    if "credit agreement" in lower or "note purchase" in lower or "securities purchase" in lower:
        return "credit_or_note_purchase_terms"
    return "financing_terms_none"


def classify_use_of_proceeds(text: str) -> str:
    lower = text.lower()
    if "use of proceeds" not in lower and "net proceeds" not in lower:
        return "use_of_proceeds_unknown"
    if "working capital" in lower or "general corporate" in lower:
        return "general_corporate_or_working_capital"
    if "growth" in lower or "capacity" in lower or "capital expenditures" in lower or "manufacturing" in lower:
        return "growth_or_capacity_funding"
    if "repay" in lower or "refinance" in lower or "debt" in lower:
        return "debt_repayment_or_refinancing"
    return "use_of_proceeds_mentioned_unknown"


def classify_expectation_state(facts: PrimitiveFacts) -> str:
    if facts.guidance_direction_state == "guidance_raise_or_increase":
        return "possible_positive_expectation_revision"
    if facts.guidance_direction_state == "guidance_reaffirm":
        return "reaffirmation_not_new_positive_surprise"
    if facts.guidance_direction_state == "guidance_cut_or_lower":
        return "negative_expectation_revision"
    return "expectation_delta_unknown"


def short_span(text: str, limit: int = 500) -> str:
    return text[:limit]


def key_fields(row: pd.Series) -> dict[str, object]:
    return {
        "lifecycle_id": row.get("lifecycle_id", ""),
        "symbol": row.get("symbol", ""),
        "theme_id": row.get("theme_id", ""),
        "entry_ts": row.get("entry_ts", ""),
        "split_name": row.get("split_name", ""),
    }


def int_safe(value: object) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0
