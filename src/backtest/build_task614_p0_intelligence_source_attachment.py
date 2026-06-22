from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from datetime import date, datetime, time as dt_time, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task612_historical_intelligence_event_backtest import (
    CIK_MAP,
    RAW_SEC_DIR,
    SEC_SUBMISSIONS_URL,
    SEC_USER_AGENT,
    TASK608K_PANEL,
    TASK608K_TAXONOMY,
    load_symbol_ciks,
    load_task608k_panel,
    markdown_table,
    parse_sec_acceptance,
)


TASK_ID = "Task614"
REPORT_DIR = Path("docs/reports/task_614_p0_intelligence_source_attachment")
ARTIFACT_DIR = Path("data/artifacts/task_614_p0_intelligence_source_attachment")
RAW_DIR = Path("data/raw/intelligence_task614")
WHITEHOUSE_LISTING_BASES = {
    "whitehouse_briefings_statements": "https://www.whitehouse.gov/briefings-statements/",
    "whitehouse_presidential_actions": "https://www.whitehouse.gov/presidential-actions/",
}
WHITEHOUSE_RSS = {
    "whitehouse_briefings_statements_feed": "https://www.whitehouse.gov/briefings-statements/feed/",
    "whitehouse_remarks_feed": "https://www.whitehouse.gov/remarks/feed/",
    "whitehouse_presidential_actions_feed": "https://www.whitehouse.gov/presidential-actions/feed/",
}
OFAC_RECENT_ACTIONS = "https://ofac.treasury.gov/recent-actions"
DEFENSE_RSS = "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1&Site=945&Category=15115&max=100"
SEC_CURRENT_FEEDS = {
    "sec_current_sc_13d": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013D&owner=include&count=100&output=atom",
    "sec_current_sc_13g": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SC%2013G&owner=include&count=100&output=atom",
    "sec_current_13f_hr": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13F-HR&owner=include&count=100&output=atom",
}


POLICY_KEYWORDS = {
    "tariff": "tariff_trade",
    "tariffs": "tariff_trade",
    "trade": "tariff_trade",
    "china": "china_export_control",
    "export": "export_control",
    "sanction": "sanctions",
    "sanctions": "sanctions",
    "energy": "energy_policy",
    "nuclear": "energy_policy",
    "electric": "energy_policy",
    "grid": "energy_policy",
    "defense": "defense_policy",
    "military": "defense_policy",
    "space": "space_policy",
    "semiconductor": "semiconductor_policy",
    "artificial intelligence": "ai_policy",
    "cyber": "cyber_policy",
    "federal reserve": "fed_policy",
}
THEME_KEYWORDS = {
    "aerospace_defense": {"defense", "military", "war", "missile", "aircraft", "aviation", "space", "nasa", "boeing", "rocket"},
    "energy_power": {"energy", "nuclear", "electric", "grid", "power", "gas", "oil", "utility"},
    "data_devops_software": {"artificial intelligence", "ai", "cyber", "software", "data", "cloud", "technology"},
    "industrial_automation": {"manufacturing", "industrial", "factory", "automation", "tariff", "trade"},
    "semiconductor_equipment": {"semiconductor", "chips", "export control", "china", "technology"},
}
SYMBOL_KEYWORDS = {
    "ASTS": {"ast spacemobile", "satellite", "space"},
    "BA": {"boeing", "aircraft", "aviation"},
    "CEG": {"constellation energy", "nuclear", "energy"},
    "DDOG": {"datadog"},
    "GE": {"general electric"},
    "GEV": {"ge vernova", "vernova", "grid", "power"},
    "MDB": {"mongodb"},
    "PH": {"parker-hannifin", "parker hannifin"},
    "PLTR": {"palantir"},
    "RKLB": {"rocket lab", "space", "launch"},
    "ROK": {"rockwell automation"},
    "RTX": {"rtx", "raytheon", "pratt", "missile", "defense"},
    "SNOW": {"snowflake"},
    "TEAM": {"atlassian"},
    "TER": {"teradyne", "semiconductor"},
}
OWNERSHIP_FORMS = {
    "SC 13D",
    "SC 13D/A",
    "SCHEDULE 13D",
    "SCHEDULE 13D/A",
    "SC 13G",
    "SC 13G/A",
    "SCHEDULE 13G",
    "SCHEDULE 13G/A",
    "13F-HR",
    "13F-HR/A",
    "4",
    "4/A",
    "144",
}
CEO_IR_FORMS = {"8-K", "6-K"}


def build_task614_p0_intelligence_source_attachment(
    *,
    task608k_panel: Path = TASK608K_PANEL,
    task608k_taxonomy: Path = TASK608K_TAXONOMY,
    cik_map_path: Path = CIK_MAP,
    raw_sec_dir: Path = RAW_SEC_DIR,
    raw_dir: Path = RAW_DIR,
    artifact_dir: Path = ARTIFACT_DIR,
    out_dir: Path = REPORT_DIR,
    fetch_sources: bool = True,
) -> dict[str, pd.DataFrame]:
    panel = load_task608k_panel(task608k_panel, task608k_taxonomy)
    symbols = sorted(panel["symbol"].astype(str).unique().tolist())
    symbol_ciks = load_symbol_ciks(cik_map_path, symbols)
    political, political_status = load_or_fetch_whitehouse_events(raw_dir, panel, fetch_sources=fetch_sources)
    geopolitical, geopolitical_status = load_or_fetch_geopolitical_events(raw_dir, panel, fetch_sources=fetch_sources)
    sec_events, sec_status = load_or_fetch_sec_intelligence_events(symbol_ciks, raw_sec_dir, raw_dir, fetch_sources=fetch_sources)
    events = pd.concat([political, geopolitical, sec_events], ignore_index=True)
    events = events.sort_values(["event_date", "source_lane", "event_title"], kind="stable").reset_index(drop=True)
    coverage = build_source_coverage(political, geopolitical, sec_events, political_status, geopolitical_status, sec_status, symbols)

    artifact_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(artifact_dir / "p0_intelligence_event_store.csv", index=False)
    coverage.to_csv(artifact_dir / "source_collection_status.csv", index=False)
    write_manifest(artifact_dir, artifact_dir / "artifact_manifest.csv")

    linked = link_intelligence_events(panel, events)
    summary = build_scenario_summary(linked)
    pass_fail = build_pass_fail(summary, coverage)
    decision = build_decision(linked, summary, coverage, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(out_dir / "p0_intelligence_events.csv", index=False)
    coverage.to_csv(out_dir / "source_lane_attachment_status.csv", index=False)
    linked.to_csv(out_dir / "entry_p0_intelligence_linkage.csv", index=False)
    summary.to_csv(out_dir / "p0_event_overlay_scenario_summary.csv", index=False)
    pass_fail.to_csv(out_dir / "task_614_pass_fail_matrix.csv", index=False)
    decision.to_csv(out_dir / "task_614_decision.csv", index=False)
    (out_dir / "task_614_p0_intelligence_source_attachment.md").write_text(
        render_report(events, coverage, summary, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "p0_intelligence_events": events,
        "source_lane_attachment_status": coverage,
        "entry_p0_intelligence_linkage": linked,
        "p0_event_overlay_scenario_summary": summary,
        "task_614_pass_fail_matrix": pass_fail,
        "task_614_decision": decision,
    }


def load_or_fetch_whitehouse_events(
    raw_dir: Path,
    panel: pd.DataFrame,
    *,
    fetch_sources: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_dir = raw_dir / "whitehouse"
    source_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    min_date = min(panel["trade_date"]) - timedelta(days=30)
    max_date = max(panel["trade_date"]) + timedelta(days=1)

    for source_name, base_url in WHITEHOUSE_LISTING_BASES.items():
        fetched_pages = 0
        parsed_rows = 0
        for page in range(1, 61):
            url = base_url if page == 1 else f"{base_url}page/{page}/"
            raw_path = source_dir / f"{source_name}_page_{page:03d}.html"
            status = fetch_text(url, raw_path, fetch_sources=fetch_sources)
            if status.startswith("HTTP_404"):
                break
            if raw_path.exists():
                fetched_pages += 1
                page_rows = parse_whitehouse_listing(raw_path.read_text(encoding="utf-8"), source_name)
                rows.extend(page_rows)
                parsed_rows += len(page_rows)
                dates = [_parse_date(row["event_date"]) for row in page_rows if _parse_date(row["event_date"]) is not None]
                if dates and min(dates) < min_date:
                    break
            time.sleep(0.03)
        status_rows.append(
            {
                "source_lane": "trump_major_person_political_statements",
                "source_name": source_name,
                "status": "FETCHED_OR_CACHED" if fetched_pages else "SOURCE_BLOCKED",
                "raw_path": source_dir.as_posix(),
                "event_count": parsed_rows,
                "notes": "White House listing pages; official timestamped pages.",
            }
        )

    for source_name, url in WHITEHOUSE_RSS.items():
        raw_path = source_dir / f"{source_name}.xml"
        status = fetch_text(url, raw_path, fetch_sources=fetch_sources)
        page_rows = parse_rss_events(raw_path, source_name, "trump_major_person_political_statements") if raw_path.exists() else []
        rows.extend(page_rows)
        status_rows.append(
            {
                "source_lane": "trump_major_person_political_statements",
                "source_name": source_name,
                "status": status,
                "raw_path": raw_path.as_posix(),
                "event_count": len(page_rows),
                "notes": "White House RSS feed.",
            }
        )

    events = pd.DataFrame(rows)
    events = normalize_event_frame(events)
    if not events.empty:
        events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
        events = events[events["event_date_obj"].between(min_date, max_date)].drop(columns=["event_date_obj"])
    return events, pd.DataFrame(status_rows)


def parse_whitehouse_listing(text: str, source_name: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r'<h2[^>]*wp-block-post-title[^>]*>\s*<a href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'<time datetime="(?P<dt>[^"]+)">(?P<date>.*?)</time>',
        re.S,
    )
    rows = []
    for match in pattern.finditer(text):
        title = clean_html(match.group("title"))
        event_dt = pd.to_datetime(match.group("dt"), utc=True, errors="coerce")
        rows.append(build_text_event_row(
            source_lane="trump_major_person_political_statements",
            source_name=source_name,
            event_title=title,
            event_url=html.unescape(match.group("url")),
            event_dt=event_dt.to_pydatetime() if not pd.isna(event_dt) else None,
            fallback_date=parse_month_date(match.group("date")),
            text_for_tags=title,
            time_precision="timestamp",
        ))
    return rows


def load_or_fetch_geopolitical_events(
    raw_dir: Path,
    panel: pd.DataFrame,
    *,
    fetch_sources: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    source_dir = raw_dir / "geopolitical"
    source_dir.mkdir(parents=True, exist_ok=True)
    min_date = min(panel["trade_date"]) - timedelta(days=30)
    max_date = max(panel["trade_date"]) + timedelta(days=1)
    rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    ofac_count = 0
    for page in range(0, 45):
        url = OFAC_RECENT_ACTIONS if page == 0 else f"{OFAC_RECENT_ACTIONS}?page={page}"
        raw_path = source_dir / f"ofac_recent_actions_page_{page:03d}.html"
        status = fetch_text(url, raw_path, fetch_sources=fetch_sources)
        if not raw_path.exists():
            continue
        page_rows = parse_ofac_recent_actions(raw_path.read_text(encoding="utf-8"), page)
        rows.extend(page_rows)
        ofac_count += len(page_rows)
        dates = [_parse_date(row["event_date"]) for row in page_rows if _parse_date(row["event_date"]) is not None]
        if dates and min(dates) < min_date:
            break
        time.sleep(0.03)
    status_rows.append(
        {
            "source_lane": "war_geopolitical_conflict_events",
            "source_name": "ofac_recent_actions",
            "status": "FETCHED_OR_CACHED" if ofac_count else "SOURCE_BLOCKED",
            "raw_path": source_dir.as_posix(),
            "event_count": ofac_count,
            "notes": "OFAC official recent actions; date-only, same-day entry use blocked.",
        }
    )

    raw_path = source_dir / "defense_rss.xml"
    defense_status = fetch_text(DEFENSE_RSS, raw_path, fetch_sources=fetch_sources)
    defense_rows = parse_rss_events(raw_path, "defense_rss", "war_geopolitical_conflict_events") if raw_path.exists() else []
    rows.extend(defense_rows)
    status_rows.append(
        {
            "source_lane": "war_geopolitical_conflict_events",
            "source_name": "defense_rss",
            "status": defense_status,
            "raw_path": raw_path.as_posix(),
            "event_count": len(defense_rows),
            "notes": "Defense/War Department RSS path accessible; ordinary web page was blocked.",
        }
    )
    events = normalize_event_frame(pd.DataFrame(rows))
    if not events.empty:
        events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
        events = events[events["event_date_obj"].between(min_date, max_date)].drop(columns=["event_date_obj"])
    return events, pd.DataFrame(status_rows)


def parse_ofac_recent_actions(text: str, page: int) -> list[dict[str, Any]]:
    pattern = re.compile(
        r'<div class="margin-bottom-4 search-result views-row">.*?<a href="(?P<url>/recent-actions/[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
        r'(?P<date>(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2},\s+20\d{2})\s+-\s*'
        r'<a href="[^"]+">(?P<category>.*?)</a>',
        re.S,
    )
    rows = []
    for match in pattern.finditer(text):
        event_date = parse_month_date(match.group("date"))
        title = clean_html(match.group("title"))
        category = clean_html(match.group("category"))
        rows.append(build_text_event_row(
            source_lane="war_geopolitical_conflict_events",
            source_name="ofac_recent_actions",
            event_title=title,
            event_url="https://ofac.treasury.gov" + html.unescape(match.group("url")),
            event_dt=None,
            fallback_date=event_date,
            text_for_tags=f"{title} {category}",
            time_precision="date",
            event_category=category,
            row_suffix=str(page),
        ))
    return rows


def load_or_fetch_sec_intelligence_events(
    symbol_ciks: dict[str, dict[str, Any]],
    raw_sec_dir: Path,
    raw_dir: Path,
    *,
    fetch_sources: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_sec_dir.mkdir(parents=True, exist_ok=True)
    source_dir = raw_dir / "sec_current_feeds"
    source_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": SEC_USER_AGENT}
    rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    for symbol, cik_info in symbol_ciks.items():
        cik = cik_info["cik"]
        if cik is None:
            continue
        cik10 = f"{int(cik):010d}"
        raw_path = raw_sec_dir / f"CIK{cik10}.json"
        status = "CACHE_USED"
        if fetch_sources and not raw_path.exists():
            response = requests.get(SEC_SUBMISSIONS_URL.format(cik10=cik10), headers=headers, timeout=30)
            response.raise_for_status()
            raw_path.write_text(response.text, encoding="utf-8")
            status = "FETCHED"
            time.sleep(0.12)
        if not raw_path.exists():
            status_rows.append(
                {
                    "source_lane": "institution_investment_actions",
                    "source_name": f"sec_company_submissions_{symbol}",
                    "status": "SOURCE_BLOCKED",
                    "raw_path": raw_path.as_posix(),
                    "event_count": 0,
                    "notes": "Company SEC submissions cache missing.",
                }
            )
            continue
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        symbol_rows = parse_sec_submission_intelligence(symbol, cik_info, data)
        rows.extend(symbol_rows)
        status_rows.append(
            {
                "source_lane": "institution_investment_actions",
                "source_name": f"sec_company_submissions_{symbol}",
                "status": status,
                "raw_path": raw_path.as_posix(),
                "event_count": len([r for r in symbol_rows if r["source_lane"] == "institution_investment_actions"]),
                "notes": "Target-company SEC ownership/proxy forms from submissions API.",
            }
        )
    for source_name, url in SEC_CURRENT_FEEDS.items():
        raw_path = source_dir / f"{source_name}.xml"
        status = fetch_text(url, raw_path, fetch_sources=fetch_sources, headers=headers)
        feed_rows = parse_sec_atom_feed(raw_path, source_name) if raw_path.exists() else []
        rows.extend(feed_rows)
        status_rows.append(
            {
                "source_lane": "institution_investment_actions",
                "source_name": source_name,
                "status": status,
                "raw_path": raw_path.as_posix(),
                "event_count": len(feed_rows),
                "notes": "SEC current ownership feed is live/latest context, not full historical 13F holdings reconstruction.",
            }
        )
    return normalize_event_frame(pd.DataFrame(rows)), pd.DataFrame(status_rows)


def parse_sec_submission_intelligence(symbol: str, cik_info: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    filing_dates = filings.get("filingDate", [])
    acceptance_times = filings.get("acceptanceDateTime", [])
    accessions = filings.get("accessionNumber", [])
    docs = filings.get("primaryDocument", [])
    descriptions = filings.get("primaryDocDescription", [])
    rows: list[dict[str, Any]] = []
    for idx, form in enumerate(forms):
        form = str(form).strip().upper()
        if form not in OWNERSHIP_FORMS and form not in CEO_IR_FORMS:
            continue
        filing_date = _parse_date(_get(filing_dates, idx))
        if filing_date is None:
            continue
        acceptance_ts = parse_sec_acceptance(_get(acceptance_times, idx))
        accession = str(_get(accessions, idx) or "")
        primary_doc = str(_get(docs, idx) or "")
        accession_no_dash = accession.replace("-", "")
        source_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_info['cik'])}/{accession_no_dash}/{primary_doc}" if accession and primary_doc else ""
        source_lane = "ceo_ir_transcripts_and_presentations" if form in CEO_IR_FORMS else "institution_investment_actions"
        title = f"{symbol} {form} {str(_get(descriptions, idx) or '').strip()}"
        rows.append(
            {
                "event_id": f"SEC_INTEL|{symbol}|{filing_date.isoformat()}|{form}|{accession}",
                "source_lane": source_lane,
                "source_name": "sec_company_submissions",
                "event_date": filing_date.isoformat(),
                "event_timestamp_utc": acceptance_ts.isoformat() if acceptance_ts is not None else "",
                "time_precision": "timestamp" if acceptance_ts is not None else "date",
                "event_title": title,
                "event_category": classify_sec_intel_form(form),
                "source_url": source_url,
                "symbol_tags": symbol,
                "theme_tags": "",
                "policy_tags": "",
                "official_source_flag": 1,
                "source_quality": "official_sec_submission",
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    return rows


def parse_sec_atom_feed(raw_path: Path, source_name: str) -> list[dict[str, Any]]:
    text = raw_path.read_text(encoding="ISO-8859-1")
    root = ET.fromstring(text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    rows = []
    for entry in root.findall("a:entry", ns):
        title = entry.findtext("a:title", default="", namespaces=ns)
        updated = entry.findtext("a:updated", default="", namespaces=ns)
        link = entry.find("a:link", ns)
        category = entry.find("a:category", ns)
        event_dt = pd.to_datetime(updated, utc=True, errors="coerce")
        form = category.attrib.get("term", "") if category is not None else ""
        url = link.attrib.get("href", "") if link is not None else ""
        rows.append(
            {
                "event_id": f"SEC_CURRENT|{source_name}|{updated}|{title}",
                "source_lane": "institution_investment_actions",
                "source_name": source_name,
                "event_date": event_dt.date().isoformat() if not pd.isna(event_dt) else "",
                "event_timestamp_utc": event_dt.to_pydatetime().isoformat() if not pd.isna(event_dt) else "",
                "time_precision": "timestamp" if not pd.isna(event_dt) else "date",
                "event_title": clean_html(title),
                "event_category": classify_sec_intel_form(form),
                "source_url": url,
                "symbol_tags": "",
                "theme_tags": "",
                "policy_tags": "",
                "official_source_flag": 1,
                "source_quality": "official_sec_current_feed_latest_only",
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    return rows


def parse_rss_events(raw_path: Path, source_name: str, source_lane: str) -> list[dict[str, Any]]:
    text = raw_path.read_text(encoding="utf-8")
    root = ET.fromstring(text)
    rows = []
    channel = root.find("channel")
    if channel is None:
        return rows
    for item in channel.findall("item"):
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")
        description = item.findtext("description", default="")
        try:
            event_dt = parsedate_to_datetime(pub_date)
        except (TypeError, ValueError):
            event_dt = None
        rows.append(build_text_event_row(
            source_lane=source_lane,
            source_name=source_name,
            event_title=clean_html(title),
            event_url=link,
            event_dt=event_dt,
            fallback_date=None,
            text_for_tags=f"{title} {description}",
            time_precision="timestamp" if event_dt else "date",
        ))
    return rows


def build_text_event_row(
    *,
    source_lane: str,
    source_name: str,
    event_title: str,
    event_url: str,
    event_dt: datetime | None,
    fallback_date: date | None,
    text_for_tags: str,
    time_precision: str,
    event_category: str = "",
    row_suffix: str = "",
) -> dict[str, Any]:
    event_date = event_dt.date() if event_dt else fallback_date
    symbol_tags, theme_tags, policy_tags = tag_event(text_for_tags)
    row_id = f"{source_lane}|{source_name}|{event_date}|{event_title}|{row_suffix}"
    return {
        "event_id": row_id,
        "source_lane": source_lane,
        "source_name": source_name,
        "event_date": event_date.isoformat() if event_date else "",
        "event_timestamp_utc": event_dt.isoformat() if event_dt else "",
        "time_precision": time_precision,
        "event_title": event_title,
        "event_category": event_category,
        "source_url": event_url,
        "symbol_tags": ";".join(symbol_tags),
        "theme_tags": ";".join(theme_tags),
        "policy_tags": ";".join(policy_tags),
        "official_source_flag": 1,
        "source_quality": "official_timestamped" if time_precision == "timestamp" else "official_date_only",
        "gpt_or_plugin_used_as_source_flag": 0,
    }


def tag_event(text: str) -> tuple[list[str], list[str], list[str]]:
    haystack = clean_html(text).lower()
    symbols = [symbol for symbol, words in SYMBOL_KEYWORDS.items() if any(word in haystack for word in words)]
    themes = [theme for theme, words in THEME_KEYWORDS.items() if any(word in haystack for word in words)]
    policy_tags = sorted({tag for word, tag in POLICY_KEYWORDS.items() if word in haystack})
    return sorted(symbols), sorted(themes), policy_tags


def link_intelligence_events(panel: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    if events.empty:
        events = normalize_event_frame(events)
    events = events.copy()
    events["event_date_obj"] = pd.to_datetime(events["event_date"], errors="coerce").dt.date
    events["event_timestamp_dt"] = pd.to_datetime(events["event_timestamp_utc"], utc=True, errors="coerce")
    rows: list[dict[str, Any]] = []
    for _, entry in out.iterrows():
        known = events[
            (events["event_date_obj"] < entry["trade_date"])
            | (
                events["event_date_obj"].eq(entry["trade_date"])
                & events["time_precision"].eq("timestamp")
                & events["event_timestamp_dt"].notna()
                & (events["event_timestamp_dt"] <= entry["entry_ts_utc"])
            )
        ]
        symbol = str(entry["symbol"])
        theme = str(entry["theme_id"])
        political = relevant_events(known, "trump_major_person_political_statements", symbol, theme)
        geopolitical = relevant_events(known, "war_geopolitical_conflict_events", symbol, theme)
        institution = known[(known["source_lane"].eq("institution_investment_actions")) & tag_contains(known["symbol_tags"], symbol)]
        ceo_ir = known[(known["source_lane"].eq("ceo_ir_transcripts_and_presentations")) & tag_contains(known["symbol_tags"], symbol)]
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "political_statement_pre7d_count": count_window(political, entry["trade_date"], 7),
                "political_statement_pre7d_flag": int(count_window(political, entry["trade_date"], 7) > 0),
                "geopolitical_event_pre7d_count": count_window(geopolitical, entry["trade_date"], 7),
                "geopolitical_event_pre7d_flag": int(count_window(geopolitical, entry["trade_date"], 7) > 0),
                "institution_ownership_pre30d_count": count_window(institution, entry["trade_date"], 30),
                "institution_ownership_pre30d_flag": int(count_window(institution, entry["trade_date"], 30) > 0),
                "activist_13d_pre30d_flag": int(count_window(institution[institution["event_category"].eq("activist_13d")], entry["trade_date"], 30) > 0),
                "passive_13g_pre30d_flag": int(count_window(institution[institution["event_category"].eq("passive_13g")], entry["trade_date"], 30) > 0),
                "insider_form4_or_144_pre30d_flag": int(count_window(institution[institution["event_category"].eq("insider_or_sale_notice")], entry["trade_date"], 30) > 0),
                "ceo_ir_proxy_pre14d_count": count_window(ceo_ir, entry["trade_date"], 14),
                "ceo_ir_proxy_pre14d_flag": int(count_window(ceo_ir, entry["trade_date"], 14) > 0),
                "p0_source_event_density": (
                    count_window(political, entry["trade_date"], 7)
                    + count_window(geopolitical, entry["trade_date"], 7)
                    + count_window(institution, entry["trade_date"], 30)
                    + count_window(ceo_ir, entry["trade_date"], 14)
                ),
                "label_used_in_assignment_flag_task614": 0,
                "gpt_or_plugin_used_as_source_flag_task614": 0,
            }
        )
    linked = out.merge(pd.DataFrame(rows), on="lifecycle_id", how="left")
    linked["p0_source_event_density_ge2_flag"] = linked["p0_source_event_density"].ge(2).astype(int)
    linked["task610_and_p0_density_ge2_flag"] = (
        linked["task610_exact_review_trigger_flag"].eq(1) & linked["p0_source_event_density_ge2_flag"].eq(1)
    ).astype(int)
    return linked


def relevant_events(events: pd.DataFrame, source_lane: str, symbol: str, theme: str) -> pd.DataFrame:
    lane = events[events["source_lane"].eq(source_lane)]
    if lane.empty:
        return lane
    return lane[
        tag_contains(lane["symbol_tags"], symbol)
        | tag_contains(lane["theme_tags"], theme)
        | lane["policy_tags"].astype(str).ne("")
    ]


def tag_contains(series: pd.Series, value: str) -> pd.Series:
    escaped = re.escape(value)
    return series.astype(str).str.contains(rf"(?:^|;){escaped}(?:;|$)", regex=True)


def count_window(events: pd.DataFrame, trade_date: date, days: int) -> int:
    if events.empty:
        return 0
    return int(events["event_date_obj"].between(trade_date - timedelta(days=days), trade_date).sum())


def event_known_by_entry(event: pd.Series, trade_date: date, entry_ts_utc: pd.Timestamp) -> bool:
    event_date = event["event_date_obj"]
    if pd.isna(event_date):
        return False
    if event_date < trade_date:
        return True
    if event_date > trade_date:
        return False
    if event.get("time_precision") != "timestamp":
        return False
    event_ts = event.get("event_timestamp_dt")
    if pd.isna(event_ts):
        return False
    return event_ts <= entry_ts_utc


def build_scenario_summary(linked: pd.DataFrame) -> pd.DataFrame:
    scenarios = [
        ("political_statement_pre7d", "political_statement_pre7d_flag"),
        ("geopolitical_event_pre7d", "geopolitical_event_pre7d_flag"),
        ("institution_ownership_pre30d", "institution_ownership_pre30d_flag"),
        ("activist_13d_pre30d", "activist_13d_pre30d_flag"),
        ("passive_13g_pre30d", "passive_13g_pre30d_flag"),
        ("insider_form4_or_144_pre30d", "insider_form4_or_144_pre30d_flag"),
        ("ceo_ir_proxy_pre14d", "ceo_ir_proxy_pre14d_flag"),
        ("p0_source_event_density_ge2", "p0_source_event_density_ge2_flag"),
        ("task610_exact_review_trigger", "task610_exact_review_trigger_flag"),
        ("task610_and_p0_density_ge2", "task610_and_p0_density_ge2_flag"),
    ]
    rows = []
    for scenario, flag_col in scenarios:
        selected = linked[linked[flag_col].fillna(0).astype(int).eq(1)]
        rows.append(profile_scenario(linked, selected, scenario))
    return pd.DataFrame(rows)


def profile_scenario(panel: pd.DataFrame, selected: pd.DataFrame, scenario: str) -> dict[str, Any]:
    baseline_avg = float(panel["net_return_from_entry"].mean())
    baseline_failure_rate = float(panel["entry_reduce_failure_flag"].mean()) if len(panel) else 0.0
    trigger_count = int(len(selected))
    failure_count = int(selected["entry_reduce_failure_flag"].sum()) if trigger_count else 0
    clean_false_count = trigger_count - failure_count
    size_down_returns = panel["net_return_from_entry"].copy()
    if trigger_count:
        size_down_returns.loc[selected.index] = size_down_returns.loc[selected.index] * 0.5
    return {
        "scenario": scenario,
        "trigger_count": trigger_count,
        "failure_count": failure_count,
        "clean_false_count": clean_false_count,
        "failure_rate": float(failure_count / trigger_count) if trigger_count else 0.0,
        "baseline_failure_rate": baseline_failure_rate,
        "failure_rate_lift_pct_point": float(((failure_count / trigger_count) - baseline_failure_rate) * 100.0) if trigger_count else 0.0,
        "clean_false_ratio": float(clean_false_count / trigger_count) if trigger_count else 0.0,
        "selected_avg_return_pct": float(selected["net_return_from_entry"].mean() * 100.0) if trigger_count else 0.0,
        "size_down_50_avg_return_delta_pct_point": float((size_down_returns.mean() - baseline_avg) * 100.0),
        "label_used_in_assignment_flag": 0,
        "gpt_or_plugin_used_as_source_flag": 0,
    }


def build_source_coverage(
    political: pd.DataFrame,
    geopolitical: pd.DataFrame,
    sec_events: pd.DataFrame,
    political_status: pd.DataFrame,
    geopolitical_status: pd.DataFrame,
    sec_status: pd.DataFrame,
    symbols: list[str],
) -> pd.DataFrame:
    rows = [
        coverage_row("trump_major_person_political_statements", "P0", political, political_status, len(symbols), "political/White House official statement features"),
        coverage_row("war_geopolitical_conflict_events", "P0", geopolitical, geopolitical_status, len(symbols), "OFAC/Defense geopolitical and sanctions features"),
        coverage_row("institution_investment_actions", "P0", sec_events[sec_events["source_lane"].eq("institution_investment_actions")], sec_status, len(symbols), "SEC target-company ownership and current ownership feed features"),
        coverage_row("ceo_ir_transcripts_and_presentations", "P1", sec_events[sec_events["source_lane"].eq("ceo_ir_transcripts_and_presentations")], sec_status, len(symbols), "SEC 8-K/6-K IR proxy features"),
        {
            "source_lane": "analyst_reports_and_rating_actions",
            "priority": "P2",
            "coverage_status": "SOURCE_BLOCKED_LICENSED_METADATA_REQUIRED",
            "official_source_flag": 0,
            "event_count": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used",
            "blocked_reason": "No licensed timestamped analyst report/rating-action metadata is available in repo.",
        },
        {
            "source_lane": "full_13f_holdings_reconstruction",
            "priority": "P1",
            "coverage_status": "SOURCE_BLOCKED_LARGE_EDGAR_PANEL_REQUIRED",
            "official_source_flag": 1,
            "event_count": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used in Task614",
            "blocked_reason": "Needs all-manager historical 13F information-table parser; current task only attaches target-company submissions and latest SEC current feed.",
        },
    ]
    return pd.DataFrame(rows)


def coverage_row(source_lane: str, priority: str, events: pd.DataFrame, status: pd.DataFrame, symbols_required: int, backtest_use: str) -> dict[str, Any]:
    event_count = int(len(events))
    blocked = event_count == 0
    status_values = ";".join(sorted(status["status"].astype(str).unique().tolist())) if not status.empty else ""
    return {
        "source_lane": source_lane,
        "priority": priority,
        "coverage_status": "ATTACHED" if not blocked else "SOURCE_BLOCKED",
        "official_source_flag": int(not blocked),
        "event_count": event_count,
        "symbols_required": symbols_required,
        "backtest_use": backtest_use if not blocked else "not used",
        "blocked_reason": "" if not blocked else f"No usable events parsed; source statuses={status_values}",
    }


def build_pass_fail(summary: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    pure = summary[~summary["scenario"].str.contains("task610", case=False, regex=True)]
    best = pure.sort_values(["failure_rate_lift_pct_point", "failure_count", "trigger_count"], ascending=[False, False, False], kind="stable").iloc[0]
    attached_p0 = int(coverage[coverage["priority"].eq("P0") & coverage["coverage_status"].eq("ATTACHED")]["source_lane"].nunique())
    diagnostic_pass = int(
        int(best["trigger_count"]) >= 5
        and float(best["failure_rate_lift_pct_point"]) >= 15.0
        and float(best["clean_false_ratio"]) <= 0.60
    )
    return pd.DataFrame(
        [
            {
                "gate": "p0_source_attachment",
                "pass_flag": int(attached_p0 >= 3),
                "metric": f"{attached_p0} P0 lanes attached",
                "threshold": ">=3 P0 lanes attached",
            },
            {
                "gate": "pure_p0_event_diagnostic_candidate",
                "pass_flag": diagnostic_pass,
                "metric": f"{best['scenario']} triggers={int(best['trigger_count'])} lift={float(best['failure_rate_lift_pct_point']):.2f}pp clean_false={float(best['clean_false_ratio']):.2%}",
                "threshold": "triggers>=5, failure lift>=15pp, clean false<=60%",
            },
            {
                "gate": "no_label_or_gpt_source_leakage",
                "pass_flag": 1,
                "metric": "labels and GPT/plugin outputs are not used as source or assignment inputs",
                "threshold": "must pass",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "metric": "source attachment only; analyst reports and full 13F holdings remain blocked",
                "threshold": "requires fold-forward and full source certification",
            },
        ]
    )


def build_decision(linked: pd.DataFrame, summary: pd.DataFrame, coverage: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    pure = summary[~summary["scenario"].str.contains("task610", case=False, regex=True)]
    best = pure.sort_values(["failure_rate_lift_pct_point", "failure_count", "trigger_count"], ascending=[False, False, False], kind="stable").iloc[0]
    attached_lanes = int(coverage["coverage_status"].eq("ATTACHED").sum())
    diagnostic_pass = int(pass_fail[pass_fail["gate"].eq("pure_p0_event_diagnostic_candidate")]["pass_flag"].iloc[0])
    decision = "PASS_P0_SOURCE_ATTACHMENT_FAIL_EVENT_PROMOTION" if attached_lanes >= 3 else "FAIL_P0_SOURCE_ATTACHMENT_INCOMPLETE"
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "entry_count": int(len(linked)),
                "failure_count": int(linked["entry_reduce_failure_flag"].sum()),
                "baseline_failure_rate": float(linked["entry_reduce_failure_flag"].mean()),
                "attached_source_lanes": attached_lanes,
                "best_p0_event_scenario": best["scenario"],
                "best_p0_trigger_count": int(best["trigger_count"]),
                "best_p0_failure_count": int(best["failure_count"]),
                "best_p0_failure_rate": float(best["failure_rate"]),
                "best_p0_failure_rate_lift_pct_point": float(best["failure_rate_lift_pct_point"]),
                "best_p0_clean_false_ratio": float(best["clean_false_ratio"]),
                "p0_event_diagnostic_pass_flag": diagnostic_pass,
                "trading_promotion_pass_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
                "next_action": "Implement full historical 13F information-table reconstruction and fold-forward P0 event overlay; keep all outputs diagnostic-only.",
            }
        ]
    )


def render_report(events: pd.DataFrame, coverage: pd.DataFrame, summary: pd.DataFrame, pass_fail: pd.DataFrame, decision: pd.DataFrame) -> str:
    d = decision.iloc[0]
    top = summary.sort_values(["failure_rate_lift_pct_point", "failure_count"], ascending=[False, False], kind="stable").head(8)
    return f"""# Task614 P0 Intelligence Source Attachment

## Decision Summary

- Verdict: `{d['decision']}`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Entries tested: {int(d['entry_count'])}
- Failures tested: {int(d['failure_count'])}
- Baseline failure rate: {float(d['baseline_failure_rate']) * 100.0:.2f}%
- Attached source lanes: {int(d['attached_source_lanes'])}
- Best pure P0 event scenario: `{d['best_p0_event_scenario']}` ({int(d['best_p0_trigger_count'])} triggers, {int(d['best_p0_failure_count'])} failures, {float(d['best_p0_failure_rate']) * 100.0:.2f}% failure rate, {float(d['best_p0_failure_rate_lift_pct_point']):.2f}pp lift)
- Canonical event store: `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`
- Next action: full historical 13F information-table reconstruction and fold-forward P0 event overlay.

## Quant Expert Report

### Data Source And Source Readiness

{markdown_table(coverage[['source_lane','priority','coverage_status','event_count','backtest_use','blocked_reason']])}

### Exact Join Keys

- Political and geopolitical events: `event_timestamp_utc/event_date <= entry_ts_utc`, then symbol/theme/policy tags.
- SEC ownership and CEO/IR proxy events: `symbol` plus SEC accepted timestamp.
- Date-only OFAC same-day events are not allowed to explain an entry because intraday availability is unknown.
- No lifecycle proximity fallback is used.
- The event store is collected independently from entries. Entry linkage is validation-only and can be rerun after strategy changes.

### Leakage Audit

- Same-day timestamped events count only if timestamp is before entry.
- Date-only events count only when event date is before trade date.
- GPT/plugin output is not used as a source.
- Labels/outcomes are evaluation-only.

### Failure Decomposition

{markdown_table(top[['scenario','trigger_count','failure_count','clean_false_count','failure_rate','failure_rate_lift_pct_point','clean_false_ratio','size_down_50_avg_return_delta_pct_point']])}

### Remaining Blockers

- Full all-manager 13F holdings reconstruction is not implemented.
- Analyst report/rating-action lane needs licensed timestamped metadata.
- Political/war text is keyword-tagged; this is source attachment, not final NLP classification.
- Strategy remains `NOT_ACCEPTED`.

## No-Background Decision-Maker Report

- P0 소스는 실제로 붙었습니다.
- 그래도 아직 돈 넣을 규칙은 아닙니다.
- 제일 좋은 P0 이벤트 표식이 실패를 충분히 세게 잡지 못하면 통과시키지 않습니다.
- 13F 전체 수급은 아직 큰 작업입니다. 지금은 SEC 회사별 ownership/proxy 공시와 최신 feed만 붙였습니다.

## Artifact Manifest

### Inputs

- Task608K entry panel and taxonomy.
- `data/raw/intelligence_task614/`
- `data/raw/sec_submissions_task612/`

### Outputs

- `p0_intelligence_events.csv`
- `source_lane_attachment_status.csv`
- `entry_p0_intelligence_linkage.csv`
- `p0_event_overlay_scenario_summary.csv`
- `task_614_pass_fail_matrix.csv`
- `task_614_decision.csv`
- `task_614_p0_intelligence_source_attachment.md`
- `artifact_manifest.csv`
- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`
- `data/artifacts/task_614_p0_intelligence_source_attachment/source_collection_status.csv`

### Validation Commands

- `python -m unittest tests.test_task614_p0_intelligence_source_attachment`
- `python scripts\\task_registry_validate.py`
- `python scripts\\operating_closeout_validate.py`
- `python scripts\\governance_completion_audit.py`
"""


def fetch_text(url: str, raw_path: Path, *, fetch_sources: bool, headers: dict[str, str] | None = None) -> str:
    if raw_path.exists() and not fetch_sources:
        return "CACHE_USED"
    if raw_path.exists():
        return "CACHE_USED"
    request_headers = headers or {"User-Agent": "Minjo Quant Research Task614 contact@example.com"}
    try:
        response = requests.get(url, headers=request_headers, timeout=30)
        if response.status_code >= 400:
            return f"HTTP_{response.status_code}"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(response.text, encoding="utf-8")
        return "FETCHED"
    except requests.RequestException as exc:
        return f"ERROR_{type(exc).__name__}"


def normalize_event_frame(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "event_id",
        "source_lane",
        "source_name",
        "event_date",
        "event_timestamp_utc",
        "published_at",
        "received_at",
        "tradable_after_ts",
        "time_precision",
        "event_title",
        "event_category",
        "source_url",
        "symbol_tags",
        "theme_tags",
        "policy_tags",
        "official_source_flag",
        "source_quality",
        "gpt_or_plugin_used_as_source_flag",
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    for col in columns:
        if col not in frame.columns:
            frame[col] = "" if col not in {"official_source_flag", "gpt_or_plugin_used_as_source_flag"} else 0
    frame["published_at"] = frame["published_at"].where(
        frame["published_at"].astype(str).str.strip().ne(""),
        frame["event_timestamp_utc"],
    )
    frame["tradable_after_ts"] = frame["tradable_after_ts"].where(
        frame["tradable_after_ts"].astype(str).str.strip().ne(""),
        frame["published_at"],
    )
    frame = frame[columns].drop_duplicates("event_id").reset_index(drop=True)
    frame["official_source_flag"] = pd.to_numeric(frame["official_source_flag"], errors="coerce").fillna(0).astype(int)
    frame["gpt_or_plugin_used_as_source_flag"] = pd.to_numeric(frame["gpt_or_plugin_used_as_source_flag"], errors="coerce").fillna(0).astype(int)
    return frame


def classify_sec_intel_form(form: str) -> str:
    form = str(form).upper()
    if "13D" in form:
        return "activist_13d"
    if "13G" in form:
        return "passive_13g"
    if form.startswith("13F"):
        return "institutional_13f_disclosure"
    if form in {"4", "4/A", "144"}:
        return "insider_or_sale_notice"
    if form in CEO_IR_FORMS:
        return "company_ir_proxy"
    return "other_sec_intelligence"


def clean_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_month_date(value: str) -> date | None:
    try:
        return datetime.strptime(clean_html(value), "%B %d, %Y").date()
    except ValueError:
        try:
            return datetime.strptime(clean_html(value), "%B %d, %Y").date()
        except ValueError:
            return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return pd.to_datetime(str(value)).date()
    except (TypeError, ValueError):
        return None


def _get(values: list[Any], idx: int) -> Any:
    return values[idx] if idx < len(values) else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true")
    args = parser.parse_args()
    artifacts = build_task614_p0_intelligence_source_attachment(fetch_sources=not args.no_fetch)
    decision = artifacts["task_614_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_p0_event_scenario']} "
        f"triggers={decision['best_p0_trigger_count']} "
        f"failures={decision['best_p0_failure_count']}"
    )


if __name__ == "__main__":
    main()
