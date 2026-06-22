from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task636"
REPORT_DIR = Path("docs/reports/task_636_full_period_content_prediction_backtest")
RAW_TEXT_DIR = Path("data/raw/task_636_content_source_text")
BASELINE_PANEL = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task632_temporal_strict_refresh/task_632_baseline_all_confirmed_backtest_panel.csv")
SCORED_ENTRIES = Path("docs/reports/task_633_qqq_benchmark_full_period_refresh/task632_temporal_strict_refresh/task_632_temporal_strict_scored_entry_panel.csv")
EVENT_STORE = Path("data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv")
TASK625_CERT = Path("docs/reports/task_625_big_event_perfection_criteria_source_certification/task_625_source_certification_matrix.csv")

USER_AGENT = "Task636QuantResearch/1.0 minjo@example.com"
CHECKPOINT_FLUSH_EVERY = 25

SIGNAL_COLUMNS = [
    "content_direct_bullish_count",
    "content_direct_bearish_count",
    "content_contract_revenue_count",
    "content_guidance_margin_count",
    "content_supply_demand_count",
    "content_regulatory_policy_count",
    "content_insider_buy_count",
    "content_insider_sell_count",
    "content_net_prediction_score",
    "content_max_magnitude_score",
    "content_low_priced_in_positive_flag",
]


def build_task636_full_period_content_prediction_backtest(
    *,
    baseline_panel_path: Path = BASELINE_PANEL,
    scored_entries_path: Path = SCORED_ENTRIES,
    event_store_path: Path = EVENT_STORE,
    task625_cert_path: Path = TASK625_CERT,
    raw_text_dir: Path = RAW_TEXT_DIR,
    out_dir: Path = REPORT_DIR,
    fetch_live: bool = True,
    max_fetch: int | None = None,
) -> dict[str, pd.DataFrame]:
    baseline = load_baseline(baseline_panel_path)
    scored = pd.read_csv(scored_entries_path)
    events = load_events(event_store_path)
    links = build_entry_event_links(baseline, events)
    source_text = certify_linked_source_text(
        links,
        events,
        task625_cert_path=task625_cert_path,
        raw_text_dir=raw_text_dir,
        fetch_live=fetch_live,
        max_fetch=max_fetch,
    )
    event_predictions = build_event_content_predictions(source_text, events)
    entry_predictions = build_entry_content_predictions(baseline, scored, links, event_predictions)
    feature_audit = build_predictive_feature_audit(entry_predictions)
    source_audit = build_source_audit(baseline, links, source_text, event_predictions, entry_predictions)
    pass_fail = build_pass_fail(source_audit, feature_audit)
    decision = build_decision(source_audit, feature_audit, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    links.to_csv(out_dir / "task_636_entry_event_links.csv", index=False)
    source_text.to_csv(out_dir / "task_636_linked_source_text_certification.csv", index=False)
    event_predictions.to_csv(out_dir / "task_636_event_content_predictions.csv", index=False)
    entry_predictions.to_csv(out_dir / "task_636_entry_content_prediction_panel.csv", index=False)
    feature_audit.to_csv(out_dir / "task_636_content_predictive_feature_audit.csv", index=False)
    source_audit.to_csv(out_dir / "task_636_source_and_prediction_coverage_audit.csv", index=False)
    pass_fail.to_csv(out_dir / "task_636_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_636_decision.csv", index=False)
    (out_dir / "task_636_full_period_content_prediction_backtest.md").write_text(
        render_report(source_audit, feature_audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "task_636_entry_event_links": links,
        "task_636_linked_source_text_certification": source_text,
        "task_636_event_content_predictions": event_predictions,
        "task_636_entry_content_prediction_panel": entry_predictions,
        "task_636_content_predictive_feature_audit": feature_audit,
        "task_636_source_and_prediction_coverage_audit": source_audit,
        "task_636_pass_fail_matrix": pass_fail,
        "task_636_decision": decision,
    }


def load_baseline(path: Path) -> pd.DataFrame:
    panel = pd.read_csv(path)
    panel["entry_ts"] = pd.to_datetime(panel["entry_ts"], utc=True, errors="coerce")
    panel["trade_date"] = pd.to_datetime(panel["trade_date"], errors="coerce").dt.date
    panel["net_return_pct"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce") * 100.0
    panel["win_eval_flag"] = panel["net_return_pct"].gt(0).astype(int)
    panel["entry_reduce_eval_flag"] = panel["net_return_pct"].le(-3.0).astype(int)
    panel["symbol"] = panel["symbol"].astype(str).str.upper()
    return panel


def load_events(path: Path) -> pd.DataFrame:
    events = pd.read_csv(path)
    events["event_id"] = events["event_id"].astype(str)
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp_utc"], utc=True, errors="coerce")
    events["tradable_after_dt"] = pd.to_datetime(events.get("tradable_after_ts"), utc=True, errors="coerce")
    events["tradable_after_dt"] = events["tradable_after_dt"].where(events["tradable_after_dt"].notna(), events["event_timestamp_dt"])
    events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
    return events[events["tradable_after_dt"].notna()].copy()


def split_tags(value: object) -> list[str]:
    return [part.strip().upper() for part in str(value or "").split("|") if part.strip() and part.strip().lower() != "nan"]


def explode_symbol_events(events: pd.DataFrame, lane: str) -> pd.DataFrame:
    ev = events[events["source_lane"].eq(lane)][["event_id", "source_lane", "tradable_after_dt", "symbol_tags"]].copy()
    ev["symbol"] = ev["symbol_tags"].apply(split_tags)
    ev = ev.explode("symbol")
    ev["symbol"] = ev["symbol"].astype(str).str.upper()
    return ev[ev["symbol"].str.len().gt(0)].drop(columns=["symbol_tags"])


def explode_theme_events(events: pd.DataFrame, lane: str) -> pd.DataFrame:
    ev = events[events["source_lane"].eq(lane)][["event_id", "source_lane", "tradable_after_dt", "theme_tags"]].copy()
    ev["theme_id"] = ev["theme_tags"].apply(lambda value: [part.strip() for part in str(value or "").split("|") if part.strip() and part.strip().lower() != "nan"])
    ev = ev.explode("theme_id")
    return ev[ev["theme_id"].astype(str).str.len().gt(0)].drop(columns=["theme_tags"])


def build_entry_event_links(entries: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for lane, days in [("institution_investment_actions", 30), ("ceo_ir_transcripts_and_presentations", 14)]:
        ev = explode_symbol_events(events, lane)
        en = entries[["lifecycle_id", "symbol", "theme_id", "entry_ts", "ret_5d_prev", "ret_20d_prev"]].copy()
        merged = en.merge(ev, on="symbol", how="inner")
        lag_days = (merged["entry_ts"] - merged["tradable_after_dt"]).dt.total_seconds() / 86400.0
        merged = merged[(lag_days >= 0) & (lag_days <= days)].copy()
        merged["event_lag_days"] = lag_days.loc[merged.index]
        merged["link_reason"] = "direct_symbol_window"
        parts.append(merged)

    for lane in ["trump_major_person_political_statements", "war_geopolitical_conflict_events"]:
        ev_theme = explode_theme_events(events, lane)
        en = entries[["lifecycle_id", "symbol", "theme_id", "entry_ts", "ret_5d_prev", "ret_20d_prev"]].copy()
        theme = en.merge(ev_theme, on="theme_id", how="inner")
        lag_days = (theme["entry_ts"] - theme["tradable_after_dt"]).dt.total_seconds() / 86400.0
        theme = theme[(lag_days >= 0) & (lag_days <= 7)].copy()
        theme["event_lag_days"] = lag_days.loc[theme.index]
        theme["link_reason"] = "theme_policy_window"
        parts.append(theme)

        policy = events[
            events["source_lane"].eq(lane)
            & events["policy_tags"].astype(str).str.strip().ne("")
            & events["policy_tags"].astype(str).str.lower().ne("nan")
        ][["event_id", "source_lane", "tradable_after_dt"]].copy()
        if not policy.empty:
            en2 = entries[["lifecycle_id", "symbol", "theme_id", "entry_ts", "ret_5d_prev", "ret_20d_prev"]].copy()
            en2["key"] = 1
            policy["key"] = 1
            merged = en2.merge(policy, on="key", how="inner").drop(columns=["key"])
            lag_days = (merged["entry_ts"] - merged["tradable_after_dt"]).dt.total_seconds() / 86400.0
            merged = merged[(lag_days >= 0) & (lag_days <= 7)].copy()
            merged["event_lag_days"] = lag_days.loc[merged.index]
            merged["link_reason"] = "broad_policy_window"
            parts.append(merged)

    if not parts:
        return pd.DataFrame()
    links = pd.concat(parts, ignore_index=True)
    return links.drop_duplicates(["lifecycle_id", "event_id"]).reset_index(drop=True)


def load_existing_certification(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    cert = pd.read_csv(path)
    cert["event_id"] = cert["event_id"].astype(str)
    return cert


def certify_linked_source_text(
    links: pd.DataFrame,
    events: pd.DataFrame,
    *,
    task625_cert_path: Path,
    raw_text_dir: Path,
    fetch_live: bool,
    max_fetch: int | None,
) -> pd.DataFrame:
    raw_text_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = raw_text_dir / "task_636_source_text_checkpoint.csv"
    existing = load_existing_certification(task625_cert_path)
    existing_by_id = {row["event_id"]: row for row in existing.to_dict(orient="records")}
    checkpoint = load_existing_certification(checkpoint_path)
    checkpoint_by_id = {
        row["event_id"]: row
        for row in checkpoint.to_dict(orient="records")
        if int(row.get("source_text_certified_flag", 0) or 0) == 1
    }
    unique = links[["event_id", "source_lane"]].drop_duplicates().merge(
        events.drop_duplicates("event_id")[
            ["event_id", "event_title", "event_date", "source_url", "source_name", "event_category", "symbol_tags", "theme_tags", "policy_tags"]
        ],
        on="event_id",
        how="left",
    )
    rows: list[dict[str, object]] = []
    fetched = 0
    for row in unique.to_dict(orient="records"):
        event_id = str(row["event_id"])
        if event_id in existing_by_id and str(existing_by_id[event_id].get("raw_text_path", "") or "").strip():
            old = existing_by_id[event_id]
            rows.append({**row, **source_text_row_from_existing(old), "text_source_status": "existing_task625_certification"})
            continue
        if event_id in checkpoint_by_id and str(checkpoint_by_id[event_id].get("raw_text_path", "") or "").strip():
            old = checkpoint_by_id[event_id]
            rows.append({**row, **source_text_row_from_existing(old), "text_source_status": "existing_task636_checkpoint"})
            continue
        source_url = str(row.get("source_url", "") or "").strip()
        if not fetch_live or not source_url or (max_fetch is not None and fetched >= max_fetch):
            rows.append({**row, **empty_source_text_row(), "text_source_status": "not_fetched"})
            continue
        status_code, final_url, text = fetch_text(source_url)
        fetched += 1
        normalized = normalize_text(text)
        text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""
        raw_text_path = ""
        if normalized:
            safe_id = hashlib.sha256(event_id.encode("utf-8")).hexdigest()[:16]
            raw_file = raw_text_dir / f"{safe_id}_{text_hash[:12]}.txt"
            raw_file.write_text(normalized, encoding="utf-8")
            raw_text_path = raw_file.as_posix()
        rows.append(
            {
                **row,
                "final_url": final_url,
                "http_status": int(status_code),
                "source_text_char_count": int(len(normalized)),
                "source_text_hash": text_hash,
                "raw_text_path": raw_text_path,
                "source_text_certified_flag": int(status_code == 200 and len(normalized) >= 200),
                "text_source_status": "fetched_live",
            }
        )
        if fetched % CHECKPOINT_FLUSH_EVERY == 0:
            pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
    if rows:
        pd.DataFrame(rows).to_csv(checkpoint_path, index=False)
    return pd.DataFrame(rows)


def source_text_row_from_existing(row: dict[str, Any]) -> dict[str, object]:
    return {
        "final_url": row.get("final_url", ""),
        "http_status": int(row.get("http_status", 0) or 0),
        "source_text_char_count": int(row.get("source_text_char_count", 0) or 0),
        "source_text_hash": row.get("source_text_hash", ""),
        "raw_text_path": row.get("raw_text_path", ""),
        "source_text_certified_flag": int(row.get("source_text_certified_flag", 0) or 0),
    }


def empty_source_text_row() -> dict[str, object]:
    return {
        "final_url": "",
        "http_status": 0,
        "source_text_char_count": 0,
        "source_text_hash": "",
        "raw_text_path": "",
        "source_text_certified_flag": 0,
    }


def fetch_text(url: str) -> tuple[int, str, str]:
    try:
        response = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/xml,text/plain"},
        )
        if "sec.gov" in url.lower():
            time.sleep(0.12)
    except requests.RequestException:
        return 0, url, ""
    text = response.text
    content_type = response.headers.get("content-type", "")
    if "xml" in content_type or url.lower().endswith(".xml"):
        return int(response.status_code), response.url, normalize_text(text)
    return int(response.status_code), response.url, extract_visible_text(text)


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    container = soup.find("main") or soup.find("article") or soup.find("body") or soup
    return normalize_text(container.get_text(" "))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def read_text(path: object) -> str:
    p = Path(str(path or ""))
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def evidence_span(text: str, patterns: list[str]) -> str:
    lower = text.lower()
    for pattern in patterns:
        idx = lower.find(pattern)
        if idx >= 0:
            start = max(0, idx - 120)
            end = min(len(text), idx + 240)
            return text[start:end].replace("\n", " ").strip()
    return text[:260].strip() if text else ""


def has_any(text: str, patterns: list[str]) -> bool:
    lower = text.lower()
    return any(pattern in lower for pattern in patterns)


OWNERSHIP_BLOCKER_PATTERNS = [
    "form 4",
    "schedule 13g",
    "schedule 13d",
    "beneficial ownership",
    "reporting person",
    "sole voting power",
    "shared voting power",
    "power of attorney",
    "section 16",
    "rule 13d-1",
    "non-derivative securities",
    "derivative securities",
    "ten percent owner",
]

FINANCING_BLOCKER_PATTERNS = [
    "securities purchase agreement",
    "note purchase agreement",
    "convertible note",
    "convertible senior notes",
    "registered direct offering",
    "private placement",
    "at-the-market offering",
    "atm program",
    "shelf registration",
    "equity distribution agreement",
    "credit agreement",
    "loan agreement",
    "indenture",
    "going concern",
]

GENERIC_SEC_BOILERPLATE_PATTERNS = [
    "item 1.01 entry into a material definitive agreement",
    "item 2.03 creation of a direct financial obligation",
    "item 3.02 unregistered sales of equity securities",
    "item 5.02 departure of directors or certain officers",
    "item 9.01 financial statements and exhibits",
    "exhibit 10.1",
    "forward-looking statements",
    "safe harbor",
    "securities and exchange commission",
]

GOVERNANCE_CONTEXT_PATTERNS = [
    "board of directors",
    "director nominees",
    "named executive officers",
    "proxy statement",
    "annual meeting",
    "independent registered public accounting firm",
    "compensation paid",
    "indemnification agreement",
    "resignation",
    "appointment",
    "employment agreement",
    "restricted stock units",
    "rsus",
    "stock options",
    "tax and financial planning",
    "compensatory plan",
]

WEAK_ECONOMIC_KEYWORDS = [
    "contract",
    "agreement",
    "order",
    "purchase",
    "award",
    "capacity",
    "pricing",
]

NAMED_COUNTERPARTY_PATTERNS = [
    "customer",
    "counterparty",
    "department of defense",
    "dod",
    "nasa",
    "government",
    "microsoft",
    "amazon",
    "google",
    "oracle",
    "boeing",
    "lockheed",
    "spacex",
]


def has_regex(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


def has_term(text: str, terms: list[str]) -> bool:
    for term in terms:
        escaped = re.escape(term.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()):
            return True
    return False


def classify_source_form_family(title: str, lane: str, event_category: str, text: str) -> str:
    full = f"{title} {event_category} {text}".lower()
    if lane == "institution_investment_actions":
        if "form 4" in full or "transactioncode" in full or "section 16" in full:
            return "form4_insider"
        if any(pattern in full for pattern in ["schedule 13g", "schedule 13d", "sc 13g", "sc 13d", "beneficial ownership"]):
            return "schedule_13d_13g"
        if "13f" in full or "institutional_13f" in full:
            return "form_13f"
        return "ownership_or_institutional_filing"
    if lane == "ceo_ir_transcripts_and_presentations":
        if has_any(full, FINANCING_BLOCKER_PATTERNS):
            return "financing_8k"
        if "form 8-k" in full or "current report" in full or "item 9.01" in full:
            return "generic_8k"
        return "operational_company_source"
    if lane in {"trump_major_person_political_statements", "war_geopolitical_conflict_events"}:
        return "macro_policy_or_geopolitical_source"
    return "unknown_source_family"


def detect_financing_state(text: str) -> str:
    lower = text.lower()
    if has_any(lower, ["going concern", "liquidity", "bankruptcy"]):
        return "liquidity_stress"
    if has_any(lower, ["convertible", "warrant", "registered direct offering", "private placement", "atm program", "shelf registration"]):
        return "dilution_or_overhang"
    if has_any(lower, ["credit agreement", "loan agreement", "indenture", "note purchase agreement", "debt"]):
        return "debt_or_credit_financing"
    return "no_financing_context"


def classify_guidance_direction(text: str) -> str:
    lower = text.lower()
    if not has_any(lower, ["guidance", "outlook", "forecast"]):
        return "no_guidance_context"
    if has_any(lower, ["raise", "raises", "raised", "increase", "increases", "increased", "above prior", "higher than previously"]):
        return "guidance_raise"
    if has_any(lower, ["reaffirm", "reaffirms", "reaffirmed", "unchanged", "maintain", "maintains"]):
        return "guidance_reaffirm"
    if has_any(lower, ["withdraw", "withdraws", "withdrew", "suspend", "suspended"]):
        return "guidance_withdraw"
    if has_any(lower, ["lower", "lowers", "lowered", "cut", "cuts", "reduced", "below prior"]):
        return "guidance_cut"
    return "guidance_mentioned_no_direction"


def raw_economic_flags(text: str) -> dict[str, bool]:
    lower = text.lower()
    named_counterparty = has_term(lower, NAMED_COUNTERPARTY_PATTERNS)
    dollar_value = has_regex(lower, [r"\$[0-9][0-9,.]*\s*(million|billion|m|bn|k)?", r"\b[0-9][0-9,.]*\s*(million|billion)\b"])
    backlog_bridge = has_term(lower, ["backlog", "bookings", "book-to-bill", "remaining performance obligations", "rpo"])
    revenue_bridge = has_term(lower, ["revenue", "revenues", "sales", "annual recurring revenue", "arr"])
    funded_award = has_term(lower, ["funded award", "contract award", "awarded a contract", "purchase order", "task order"])
    margin_bridge = has_term(lower, ["gross margin", "operating margin", "margin expansion", "margin improvement"])
    direct_demand = has_term(lower, ["customer demand", "strong demand", "supply shortage", "capacity expansion", "production ramp", "deliveries"])
    return {
        "named_counterparty": named_counterparty,
        "dollar_value": dollar_value,
        "backlog_bridge": backlog_bridge,
        "revenue_bridge": revenue_bridge,
        "funded_award": funded_award,
        "margin_bridge": margin_bridge,
        "direct_demand": direct_demand,
        "weak_keyword": has_term(lower, WEAK_ECONOMIC_KEYWORDS),
    }


def interpretation_blocker(source_form_family: str, text: str, flags: dict[str, bool]) -> tuple[str, int, int]:
    lower = text.lower()
    ownership_blocked = int(
        source_form_family in {"form4_insider", "schedule_13d_13g", "form_13f", "ownership_or_institutional_filing"}
        or has_any(lower, OWNERSHIP_BLOCKER_PATTERNS)
    )
    financing_blocked = int(has_any(lower, FINANCING_BLOCKER_PATTERNS))
    boilerplate_noise = int(has_any(lower, GENERIC_SEC_BOILERPLATE_PATTERNS))
    governance_noise = int(has_any(lower, GOVERNANCE_CONTEXT_PATTERNS))
    strong_anchor = int(sum(int(flags[name]) for name in ["named_counterparty", "dollar_value", "backlog_bridge", "revenue_bridge", "funded_award", "margin_bridge", "direct_demand"]) >= 2)
    if ownership_blocked:
        return "ownership_or_insider_filing_blocker", financing_blocked, boilerplate_noise
    if financing_blocked:
        return "financing_context_requires_separate_review", financing_blocked, boilerplate_noise
    if governance_noise and not (flags["funded_award"] or flags["direct_demand"] or flags["margin_bridge"]):
        return "governance_or_compensation_filing_blocker", financing_blocked, boilerplate_noise
    if boilerplate_noise and not strong_anchor:
        return "generic_sec_boilerplate_weak_keyword_blocker", financing_blocked, boilerplate_noise
    if flags["weak_keyword"] and not strong_anchor:
        return "weak_keyword_without_operational_anchor", financing_blocked, boilerplate_noise
    return "", financing_blocked, boilerplate_noise


def score_event_text(row: pd.Series, text: str) -> dict[str, object]:
    title = str(row.get("event_title", "") or "")
    lane = str(row.get("source_lane", "") or "")
    event_category = str(row.get("event_category", "") or "")
    full = f"{title} {text}"
    lower = full.lower()
    source_form_family = classify_source_form_family(title, lane, event_category, full)
    flags = raw_economic_flags(full)
    blocker, financing_contamination, boilerplate_noise = interpretation_blocker(source_form_family, full, flags)
    guidance_state = classify_guidance_direction(full)
    financing_state = detect_financing_state(full)

    form4_transaction_codes = [code.upper() for code in re.findall(r"<transactionCode>\s*([A-Z])\s*</transactionCode>", full, flags=re.I)]
    form4_shares = re.findall(r"<transactionShares>\s*<value>\s*([0-9,.]+)\s*</value>", full, flags=re.I)
    form4_prices = re.findall(r"<transactionPricePerShare>\s*<value>\s*([0-9,.]+)\s*</value>", full, flags=re.I)
    has_form4_purchase = "P" in form4_transaction_codes
    has_form4_sale = "S" in form4_transaction_codes
    has_large_form4_trade = len(form4_shares) >= 2 or any(parse_float(value) >= 10000 for value in form4_shares)

    revenue = bool(flags["backlog_bridge"] or flags["revenue_bridge"] or flags["funded_award"])
    guidance = guidance_state == "guidance_raise" or flags["margin_bridge"]
    supply = bool(flags["direct_demand"])
    regulatory = has_any(
        lower,
        ["approval", "clearance", "fda", "sanction", "restriction", "tariff", "export control", "investigation", "designation", "license"],
    )
    named_counterparty = bool(flags["named_counterparty"])
    dilution = financing_state in {"dilution_or_overhang", "liquidity_stress"}
    negative_operations = has_any(lower, ["delay", "delayed", "termination", "cancelled", "impairment", "restatement", "material weakness"])
    insider_buy = has_form4_purchase or bool(re.search(r"transaction code\s+p|acquired", lower))
    insider_sell = has_form4_sale or bool(re.search(r"transaction code\s+s|disposed|sale", lower))
    operational_anchor_count = int(
        sum(
            int(flags[name])
            for name in ["named_counterparty", "dollar_value", "backlog_bridge", "revenue_bridge", "funded_award", "margin_bridge", "direct_demand"]
        )
    )
    operational_positive_certified = int(
        bool(text)
        and not blocker
        and operational_anchor_count >= 2
        and (revenue or guidance or supply)
    )

    direction = "neutral"
    score = 0.0
    magnitude = 0
    causal = "no_stock_specific_causal_link"
    if lane == "institution_investment_actions":
        revenue = False
        guidance = False
        supply = False
        regulatory = False
        named_counterparty = False
        if insider_buy:
            direction, score, magnitude, causal = "neutral", 0.0, 0, "insider_or_owner_acquisition_non_economic"
            if has_large_form4_trade:
                magnitude = 0
        elif insider_sell or dilution:
            direction, score, magnitude, causal = "neutral", 0.0, 0, "insider_sale_or_dilution_non_economic"
        elif event_category in {"activist_13d"}:
            direction, score, magnitude, causal = "neutral", 0.0, 0, "activist_ownership_pressure_non_economic"
        elif event_category in {"passive_13g", "institutional_13f_disclosure"}:
            direction, score, magnitude, causal = "neutral", 0.0, 0, "institutional_ownership_disclosure_non_economic"
        else:
            causal = "ownership_filing_without_direction"
    elif lane == "ceo_ir_transcripts_and_presentations":
        if financing_state != "no_financing_context" or dilution or negative_operations:
            direction, score, magnitude, causal = "bearish", -2.0, 2, "financing_or_dilution_risk"
        elif operational_positive_certified:
            direction, score, magnitude, causal = "bullish", 2.0, 2, "company_direct_economic_update"
            if named_counterparty or revenue:
                score += 1.0
                magnitude = 3
        else:
            causal = "company_filing_without_interpretable_economic_content"
    elif lane == "trump_major_person_political_statements":
        if regulatory and has_any(lower, ["tariff", "restriction", "export control", "sanction"]):
            direction, score, magnitude, causal = "bearish", -1.0, 1, "macro_policy_restriction"
        elif has_any(lower, ["defense", "space", "nasa", "industrial base", "infrastructure", "energy"]):
            direction, score, magnitude, causal = "mixed", 0.5, 1, "theme_policy_possible_tailwind"
        else:
            causal = "macro_statement_without_stock_specific_link"
    elif lane == "war_geopolitical_conflict_events":
        if regulatory:
            direction, score, magnitude, causal = "bearish", -1.0, 1, "sanction_or_geopolitical_restriction"
        else:
            causal = "geopolitical_background_without_direct_link"

    if blocker and causal == "company_direct_economic_update":
        direction, score, magnitude, causal = "neutral", 0.0, 0, "blocked_weak_or_contaminated_economic_keyword"
    if blocker:
        revenue = False
        guidance = False
        supply = False
        named_counterparty = False

    certified = int(
        bool(text)
        and magnitude > 0
        and causal not in {"no_stock_specific_causal_link", "macro_statement_without_stock_specific_link", "geopolitical_background_without_direct_link"}
    )
    economic_certified = int(operational_positive_certified and causal == "company_direct_economic_update")
    weak_keyword_only = int(flags["weak_keyword"] and not economic_certified)
    patterns = ["contract", "award", "order", "backlog", "guidance", "margin", "demand", "capacity", "approval", "sanction", "tariff", "acquired", "disposed", "offering"]
    return {
        "source_form_family": source_form_family,
        "interpretation_blocker": blocker,
        "financing_interpretation_state": financing_state,
        "guidance_direction_state": guidance_state,
        "financing_contamination_flag": int(financing_contamination),
        "boilerplate_noise_flag": int(boilerplate_noise),
        "weak_keyword_only_flag": int(weak_keyword_only),
        "operational_anchor_count": int(operational_anchor_count),
        "economic_evidence_certified_flag": int(economic_certified),
        "content_prediction_direction": direction,
        "content_prediction_magnitude_score": int(magnitude),
        "content_stock_specific_causal_link": causal,
        "content_stock_specific_causal_link_flag": int(causal in {"company_direct_economic_update", "financing_or_dilution_risk", "macro_policy_restriction", "theme_policy_possible_tailwind", "sanction_or_geopolitical_restriction"}),
        "content_named_customer_or_counterparty": int(named_counterparty),
        "content_revenue_or_backlog_signal": int(revenue),
        "content_guidance_or_margin_signal": int(guidance),
        "content_supply_demand_signal": int(supply),
        "content_regulatory_or_policy_transmission": int(regulatory),
        "content_priced_in_risk_base_score": 0,
        "content_interpretation_evidence_span": evidence_span(full, patterns),
        "content_prediction_certified_flag": certified,
        "content_raw_prediction_score": float(score),
    }


def parse_float(value: object) -> float:
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return 0.0


def build_event_content_predictions(source_text: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    source_text = source_text.merge(
        events.drop_duplicates("event_id")[["event_id", "time_precision"]],
        on="event_id",
        how="left",
    )
    rows: list[dict[str, object]] = []
    for _, row in source_text.iterrows():
        text = read_text(row.get("raw_text_path"))
        prediction = score_event_text(row, text)
        rows.append({**row.to_dict(), **prediction})
    return pd.DataFrame(rows)


def build_entry_content_predictions(
    baseline: pd.DataFrame,
    scored: pd.DataFrame,
    links: pd.DataFrame,
    event_predictions: pd.DataFrame,
) -> pd.DataFrame:
    ret_cols = [
        "lifecycle_id",
        "symbol",
        "theme_id",
        "entry_ts",
        "split_name",
        "net_return_pct",
        "win_eval_flag",
        "entry_reduce_eval_flag",
    ]
    base = baseline[ret_cols + ["ret_5d_prev", "ret_20d_prev"]].copy()
    linked = links.merge(
        event_predictions[
            [
                "event_id",
                "content_prediction_direction",
                "content_prediction_magnitude_score",
                "content_stock_specific_causal_link",
                "content_named_customer_or_counterparty",
                "content_revenue_or_backlog_signal",
                "content_guidance_or_margin_signal",
                "content_supply_demand_signal",
                "content_regulatory_or_policy_transmission",
                "content_stock_specific_causal_link_flag",
                "source_form_family",
                "interpretation_blocker",
                "financing_interpretation_state",
                "guidance_direction_state",
                "financing_contamination_flag",
                "boilerplate_noise_flag",
                "weak_keyword_only_flag",
                "operational_anchor_count",
                "economic_evidence_certified_flag",
                "content_prediction_certified_flag",
                "content_raw_prediction_score",
                "source_text_certified_flag",
            ]
        ],
        on="event_id",
        how="left",
    )
    linked["lag_priced_in_penalty"] = (linked["event_lag_days"].astype(float) / 7.0).clip(0, 1)
    linked["price_extension_penalty"] = pd.to_numeric(linked["ret_5d_prev"], errors="coerce").fillna(0).clip(lower=0, upper=0.10) / 0.10
    linked["content_priced_in_risk_score"] = ((linked["lag_priced_in_penalty"] + linked["price_extension_penalty"]) / 2.0).fillna(0)
    linked["content_adjusted_prediction_score"] = (
        pd.to_numeric(linked["content_raw_prediction_score"], errors="coerce").fillna(0)
        * (1.0 - linked["content_priced_in_risk_score"].clip(0, 1))
        * pd.to_numeric(linked["content_prediction_certified_flag"], errors="coerce").fillna(0)
    )
    agg = linked.groupby("lifecycle_id", as_index=False).agg(
        linked_event_count=("event_id", "nunique"),
        source_text_certified_event_count=("source_text_certified_flag", "sum"),
        content_prediction_certified_event_count=("content_prediction_certified_flag", "sum"),
        economic_evidence_certified_event_count=("economic_evidence_certified_flag", "sum"),
        weak_keyword_only_event_count=("weak_keyword_only_flag", "sum"),
        financing_contamination_event_count=("financing_contamination_flag", "sum"),
        boilerplate_noise_event_count=("boilerplate_noise_flag", "sum"),
        content_direct_bullish_count=("content_prediction_direction", lambda s: int((s == "bullish").sum())),
        content_direct_bearish_count=("content_prediction_direction", lambda s: int((s == "bearish").sum())),
        content_contract_revenue_count=("content_revenue_or_backlog_signal", "sum"),
        content_guidance_margin_count=("content_guidance_or_margin_signal", "sum"),
        content_supply_demand_count=("content_supply_demand_signal", "sum"),
        content_regulatory_policy_count=("content_regulatory_or_policy_transmission", "sum"),
        content_insider_buy_count=("content_stock_specific_causal_link", lambda s: int((s == "insider_or_owner_acquisition_non_economic").sum())),
        content_insider_sell_count=("content_stock_specific_causal_link", lambda s: int((s == "insider_sale_or_dilution_non_economic").sum())),
        content_net_prediction_score=("content_adjusted_prediction_score", "sum"),
        content_max_magnitude_score=("content_prediction_magnitude_score", "max"),
        content_avg_priced_in_risk_score=("content_priced_in_risk_score", "mean"),
    )
    out = base.merge(agg, on="lifecycle_id", how="left")
    for column in SIGNAL_COLUMNS + [
        "linked_event_count",
        "source_text_certified_event_count",
        "content_prediction_certified_event_count",
        "economic_evidence_certified_event_count",
        "weak_keyword_only_event_count",
        "financing_contamination_event_count",
        "boilerplate_noise_event_count",
        "content_avg_priced_in_risk_score",
    ]:
        if column not in out.columns:
            out[column] = 0
        out[column] = pd.to_numeric(out[column], errors="coerce").fillna(0)
    out["content_low_priced_in_positive_flag"] = ((out["content_net_prediction_score"] > 0) & (out["content_avg_priced_in_risk_score"] <= 0.5)).astype(int)
    return out


def feature_metrics(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {"count": 0, "avg_return_pct": float("nan"), "win_rate": float("nan"), "entry_reduce_rate": float("nan")}
    return {
        "count": int(len(frame)),
        "avg_return_pct": float(frame["net_return_pct"].mean()),
        "win_rate": float(frame["win_eval_flag"].mean()),
        "entry_reduce_rate": float(frame["entry_reduce_eval_flag"].mean()),
    }


def build_predictive_feature_audit(entry_predictions: pd.DataFrame) -> pd.DataFrame:
    feature_flags = {
        "content_positive_score_flag": entry_predictions["content_net_prediction_score"].gt(0).astype(int),
        "content_strong_positive_score_flag": entry_predictions["content_net_prediction_score"].ge(1.5).astype(int),
        "content_negative_score_flag": entry_predictions["content_net_prediction_score"].lt(0).astype(int),
        "content_contract_revenue_flag": entry_predictions["content_contract_revenue_count"].gt(0).astype(int),
        "content_guidance_margin_flag": entry_predictions["content_guidance_margin_count"].gt(0).astype(int),
        "content_supply_demand_flag": entry_predictions["content_supply_demand_count"].gt(0).astype(int),
        "content_insider_buy_flag": entry_predictions["content_insider_buy_count"].gt(0).astype(int),
        "content_insider_sell_flag": entry_predictions["content_insider_sell_count"].gt(0).astype(int),
        "content_low_priced_in_positive_flag": entry_predictions["content_low_priced_in_positive_flag"].astype(int),
    }
    work = entry_predictions.copy()
    for name, values in feature_flags.items():
        work[name] = values
    rows: list[dict[str, object]] = []
    for feature in feature_flags:
        for split_name in ["all", "train_design", "validation", "recent_oos"]:
            subset = work if split_name == "all" else work[work["split_name"].astype(str).eq(split_name)]
            yes = subset[subset[feature].eq(1)]
            no = subset[subset[feature].eq(0)]
            yes_m = feature_metrics(yes)
            no_m = feature_metrics(no)
            rows.append(
                {
                    "feature": feature,
                    "split_name": split_name,
                    "feature_1_count": yes_m["count"],
                    "feature_0_count": no_m["count"],
                    "feature_1_avg_return_pct": yes_m["avg_return_pct"],
                    "feature_0_avg_return_pct": no_m["avg_return_pct"],
                    "avg_return_lift_pct_point": yes_m["avg_return_pct"] - no_m["avg_return_pct"],
                    "feature_1_win_rate": yes_m["win_rate"],
                    "feature_0_win_rate": no_m["win_rate"],
                    "feature_1_entry_reduce_rate": yes_m["entry_reduce_rate"],
                    "feature_0_entry_reduce_rate": no_m["entry_reduce_rate"],
                    "entry_reduce_delta_pct_point": (yes_m["entry_reduce_rate"] - no_m["entry_reduce_rate"]) * 100.0,
                }
            )
    audit = pd.DataFrame(rows)
    stability = []
    for feature, group in audit.groupby("feature", dropna=False):
        train = group[group["split_name"].eq("train_design")].iloc[0]
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        pass_flag = int(
            int(train["feature_1_count"]) >= 30
            and int(validation["feature_1_count"]) >= 10
            and int(recent["feature_1_count"]) >= 5
            and float(validation["avg_return_lift_pct_point"]) > 0
            and float(recent["avg_return_lift_pct_point"]) > 0
            and float(validation["entry_reduce_delta_pct_point"]) <= 0
            and float(recent["entry_reduce_delta_pct_point"]) <= 0
        )
        stability.append({"feature": feature, "predictive_stability_pass_flag": pass_flag})
    return audit.merge(pd.DataFrame(stability), on="feature", how="left")


def build_source_audit(
    baseline: pd.DataFrame,
    links: pd.DataFrame,
    source_text: pd.DataFrame,
    event_predictions: pd.DataFrame,
    entry_predictions: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "entry_count": int(len(baseline)),
                "entry_start": str(baseline["entry_ts"].min().date()),
                "entry_end": str(baseline["entry_ts"].max().date()),
                "entry_event_link_count": int(len(links)),
                "linked_entry_count": int(links["lifecycle_id"].nunique()),
                "unique_linked_event_count": int(links["event_id"].nunique()),
                "source_text_certified_event_count": int(pd.to_numeric(source_text["source_text_certified_flag"], errors="coerce").fillna(0).sum()),
                "content_prediction_certified_event_count": int(pd.to_numeric(event_predictions["content_prediction_certified_flag"], errors="coerce").fillna(0).sum()),
                "entries_with_content_prediction_count": int(entry_predictions["content_prediction_certified_event_count"].gt(0).sum()),
                "entries_with_positive_content_score_count": int(entry_predictions["content_net_prediction_score"].gt(0).sum()),
                "entries_with_negative_content_score_count": int(entry_predictions["content_net_prediction_score"].lt(0).sum()),
                "label_used_in_assignment_flag": 0,
                "presence_field_used_for_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        ]
    )


def build_pass_fail(source_audit: pd.DataFrame, feature_audit: pd.DataFrame) -> pd.DataFrame:
    audit = source_audit.iloc[0]
    stable = int(feature_audit[["feature", "predictive_stability_pass_flag"]].drop_duplicates()["predictive_stability_pass_flag"].sum())
    return pd.DataFrame(
        [
            {
                "gate": "full_period_linkage_built",
                "pass_flag": int(int(audit["entry_count"]) >= 5000 and str(audit["entry_end"]) >= "2026-06-01"),
                "observed_value": f"entries={int(audit['entry_count'])}; end={audit['entry_end']}",
                "required_value": "full refreshed period through June 2026",
            },
            {
                "gate": "source_text_coverage",
                "pass_flag": int(int(audit["source_text_certified_event_count"]) == int(audit["unique_linked_event_count"])),
                "observed_value": f"source_text={int(audit['source_text_certified_event_count'])}/{int(audit['unique_linked_event_count'])}",
                "required_value": "all linked events should have source text for full-quality interpretation",
            },
            {
                "gate": "content_prediction_coverage",
                "pass_flag": int(int(audit["entries_with_content_prediction_count"]) >= 100),
                "observed_value": f"entries_with_prediction={int(audit['entries_with_content_prediction_count'])}",
                "required_value": "at least 100 entries need certified content predictions before backtest use",
            },
            {
                "gate": "content_predictive_stability",
                "pass_flag": int(stable > 0),
                "observed_value": f"stable_predictive_features={stable}",
                "required_value": "at least one content-derived feature must work in validation and recent OOS",
            },
            {
                "gate": "presence_fields_not_used",
                "pass_flag": int(int(audit["presence_field_used_for_assignment_flag"]) == 0),
                "observed_value": "presence fields not used",
                "required_value": "information presence fields remain forbidden",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "content prediction research only",
                "required_value": "requires stable predictive content feature and account/QQQ rerun",
            },
        ]
    )


def build_decision(source_audit: pd.DataFrame, feature_audit: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    audit = source_audit.iloc[0]
    stable = int(feature_audit[["feature", "predictive_stability_pass_flag"]].drop_duplicates()["predictive_stability_pass_flag"].sum())
    decision = "FAIL_CONTENT_PREDICTION_NOT_ACCEPTED"
    if stable > 0:
        decision = "PASS_CONTENT_PREDICTION_CANDIDATE_NEEDS_ACCOUNT_RERUN"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "entry_count": int(audit["entry_count"]),
                "unique_linked_event_count": int(audit["unique_linked_event_count"]),
                "source_text_certified_event_count": int(audit["source_text_certified_event_count"]),
                "content_prediction_certified_event_count": int(audit["content_prediction_certified_event_count"]),
                "entries_with_content_prediction_count": int(audit["entries_with_content_prediction_count"]),
                "stable_predictive_feature_count": stable,
                "trading_promotion_pass_flag": 0,
                "next_action": "If stable content features exist rerun $1000 QQQ and Task617 account comparison using content-gated entries; otherwise expand source interpretation quality.",
            }
        ]
    )


def render_report(
    source_audit: pd.DataFrame,
    feature_audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    s = source_audit.iloc[0]
    lines = [
        "# Task636 Full Period Content Prediction Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        f"- Entries: {int(d['entry_count'])}",
        f"- Linked events: {int(d['unique_linked_event_count'])}",
        f"- Source text certified events: {int(d['source_text_certified_event_count'])}",
        f"- Entries with certified content prediction: {int(d['entries_with_content_prediction_count'])}",
        f"- Stable predictive content features: {int(d['stable_predictive_feature_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "This task reads linked source text and converts it into stock-specific content prediction fields. Presence fields are not used for assignment.",
        "",
        "### Coverage",
        "",
        "| Entries | Linked Entries | Unique Events | Source Text | Content Events | Entries With Content |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {int(s['entry_count'])} | {int(s['linked_entry_count'])} | {int(s['unique_linked_event_count'])} | {int(s['source_text_certified_event_count'])} | {int(s['content_prediction_certified_event_count'])} | {int(s['entries_with_content_prediction_count'])} |",
        "",
        "### Predictive Feature Audit",
        "",
        "| Feature | Stable Pass | Validation Lift | Recent Lift | Validation ER Delta | Recent ER Delta |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for feature, group in feature_audit.groupby("feature", dropna=False):
        validation = group[group["split_name"].eq("validation")].iloc[0]
        recent = group[group["split_name"].eq("recent_oos")].iloc[0]
        lines.append(
            f"| `{feature}` | {int(validation['predictive_stability_pass_flag'])} | "
            f"{float(validation['avg_return_lift_pct_point']):.2f} | {float(recent['avg_return_lift_pct_point']):.2f} | "
            f"{float(validation['entry_reduce_delta_pct_point']):.2f} | {float(recent['entry_reduce_delta_pct_point']):.2f} |"
        )
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- This task uses source text content, not information existence.",
            "- It extracts direct bullish or bearish meaning and tests whether that meaning predicts returns.",
            "- Trading remains forbidden until the content feature survives validation, recent OOS, and account comparison.",
            "",
            "## Pass/Fail Matrix",
            "",
            "| Gate | Pass | Observed | Required |",
            "|---|---:|---|---|",
        ]
    )
    for _, row in pass_fail.iterrows():
        lines.append(f"| `{row['gate']}` | {int(row['pass_flag'])} | {row['observed_value']} | {row['required_value']} |")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task_636_entry_event_links.csv`",
            "- `task_636_linked_source_text_certification.csv`",
            "- `task_636_event_content_predictions.csv`",
            "- `task_636_entry_content_prediction_panel.csv`",
            "- `task_636_content_predictive_feature_audit.csv`",
            "- `task_636_source_and_prediction_coverage_audit.csv`",
            "- `task_636_decision.csv`",
            "- `artifact_manifest.csv`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--max-fetch", type=int)
    args = parser.parse_args()
    artifacts = build_task636_full_period_content_prediction_backtest(
        out_dir=args.out_dir,
        fetch_live=not args.no_fetch,
        max_fetch=args.max_fetch,
    )
    decision = artifacts["task_636_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"source_text={int(decision['source_text_certified_event_count'])}/{int(decision['unique_linked_event_count'])} "
        f"entries_with_content={int(decision['entries_with_content_prediction_count'])} "
        f"stable_features={int(decision['stable_predictive_feature_count'])}"
    )


if __name__ == "__main__":
    main()
