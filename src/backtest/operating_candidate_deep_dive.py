from __future__ import annotations

import html
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class CandidateDeepDive:
    event_id: str
    lifecycle_id: str
    symbol: str
    theme_id: str
    entry_ts: str
    split_name: str
    prior_permission_state: str
    prior_rule_id: str
    refined_context_family: str
    refined_permission_state: str
    refined_rule_id: str
    refined_relation_type: str
    operating_connection_candidate_after_review_flag: int
    operating_connection_supported_after_review_flag: int
    false_positive_flag: int
    required_next_evidence: str
    source_text_window: str
    used_for_trading_flag: int
    backtest_eligible_flag: int
    outcome_used_for_assignment_flag: int


def review_operating_candidate(row: pd.Series, *, root: Path = ROOT) -> dict[str, object]:
    text = source_text(row, root=root)
    lower = text.lower()
    span = clean_missing(row.get("content_interpretation_evidence_span"))

    if is_mna(lower):
        family = "strategic_mna_context"
        permission = "connection_candidate"
        rule = "MNA_REQUIRES_OPERATING_TRANSMISSION"
        relation = "prerequisite"
        candidate = 1
        supported = 0
        false_positive = 0
        evidence = "acquired business description, revenue contribution, customer relationships, backlog, guidance, synergy, or integration details"
    elif is_severance_or_proxy(lower):
        family = "governance_compensation_context"
        permission = "not_applicable"
        rule = "SEVERANCE_POLICY_NON_OPERATING"
        relation = "non_operating"
        candidate = 0
        supported = 0
        false_positive = 1
        evidence = "none; severance or proxy schedule is governance/compensation context"
    elif is_director_governance(lower):
        family = "governance_board_context"
        permission = "not_applicable"
        rule = "DIRECTOR_APPOINTMENT_GOVERNANCE_ONLY"
        relation = "non_operating"
        candidate = 0
        supported = 0
        false_positive = 1
        evidence = "none; board or committee change is governance context"
    elif is_compensation(lower):
        family = "compensation_context"
        permission = "not_applicable"
        rule = "COMPENSATION_PLAN_NON_OPERATING"
        relation = "non_operating"
        candidate = 0
        supported = 0
        false_positive = 1
        evidence = "none; compensation plan belongs to compensation/governance context"
    elif is_investment_transaction(lower):
        family = "strategic_transaction_context"
        permission = "review_required"
        rule = "INVESTMENT_AGREEMENT_NOT_OPERATING_BY_DEFAULT"
        relation = "strategic_transaction_review"
        candidate = 0
        supported = 0
        false_positive = 1
        evidence = "business-unit economics, strategic fit, revenue impact, margin impact, or capital allocation rationale"
    elif has_operating_path(lower):
        family = "operating_context"
        permission = "connection_candidate"
        rule = "OPERATING_LANGUAGE_NEEDS_ECONOMIC_PATH"
        relation = "candidate_edge_review_only"
        candidate = 1
        supported = 0
        false_positive = 0
        evidence = "contract economics, customer, duration, backlog, guidance, margin, and denominator"
    else:
        family = "unclassified_generic_8k_context"
        permission = "review_required"
        rule = "UNCLASSIFIED_8K_REVIEW_REQUIRED_AFTER_DEEP_DIVE"
        relation = "prerequisite_review_required"
        candidate = 0
        supported = 0
        false_positive = 1
        evidence = "item type and economic transmission evidence"

    return asdict(
        CandidateDeepDive(
            event_id=str(row.get("event_id", "")),
            lifecycle_id=str(row.get("lifecycle_id", "")),
            symbol=str(row.get("symbol", "")),
            theme_id=str(row.get("theme_id", "")),
            entry_ts=str(row.get("entry_ts", "")),
            split_name=str(row.get("split_name", "")),
            prior_permission_state=str(row.get("permission_state", "")),
            prior_rule_id=str(row.get("rule_id", "")),
            refined_context_family=family,
            refined_permission_state=permission,
            refined_rule_id=rule,
            refined_relation_type=relation,
            operating_connection_candidate_after_review_flag=candidate,
            operating_connection_supported_after_review_flag=supported,
            false_positive_flag=false_positive,
            required_next_evidence=evidence,
            source_text_window=window(text, span),
            used_for_trading_flag=0,
            backtest_eligible_flag=0,
            outcome_used_for_assignment_flag=0,
        )
    )


def is_compensation(lower: str) -> bool:
    return any(token in lower for token in ["restricted stock unit", "stock option grant", "performance stock unit", "compensatory plan", "equity incentive", "long-term incentive"])


def is_director_governance(lower: str) -> bool:
    if "director" not in lower:
        return False
    return bool(
        re.search(r"appointed[^.]{0,120}director", lower)
        or re.search(r"director[^.]{0,120}appointed", lower)
        or "fill a vacancy" in lower
        or "class iii director" in lower
    )


def is_severance_or_proxy(lower: str) -> bool:
    return any(token in lower for token in ["severance benefits policy", "change in control severance"])


def is_investment_transaction(lower: str) -> bool:
    return "investment agreement" in lower or ("shares" in lower and "investment" in lower and "divestiture" in lower)


def is_mna(lower: str) -> bool:
    return any(token in lower for token in ["agreement to acquire", "acquire geost", "merger", "purchase agreement"]) and any(token in lower for token in ["acquire", "transaction"])


def has_operating_path(lower: str) -> bool:
    return any(token in lower for token in ["customer", "contract award", "backlog", "guidance", "revenue contribution", "margin", "supply agreement", "production capacity"])


def source_text(row: pd.Series, *, root: Path = ROOT) -> str:
    raw_path = clean_missing(row.get("raw_text_path"))
    if raw_path:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return normalize(path.read_text(encoding="utf-8", errors="ignore")[:50000])
    span = clean_missing(row.get("content_interpretation_evidence_span"))
    return normalize(span)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", TAG_RE.sub(" ", html.unescape(text))).strip()


def window(text: str, span: str, limit: int = 1400) -> str:
    if not text:
        return ""
    idx = text.find(span[:80]) if span else -1
    if idx < 0:
        match = re.search(
            r"restricted stock|compensatory|investment agreement|director|severance|purchase agreement|acquire|material definitive agreement",
            text,
            re.IGNORECASE,
        )
        idx = match.start() if match else 0
    start = max(0, idx - 350)
    return text[start : start + limit]


def clean_missing(value: object) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "nat"} else text
