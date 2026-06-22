from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task611_turboquant_sparse_overlay_backtest import add_turboquant_scores


TASK_ID = "Task612"
REPORT_DIR = Path("docs/reports/task_612_historical_intelligence_event_backtest")
RAW_SEC_DIR = Path("data/raw/sec_submissions_task612")
RAW_FED_DIR = Path("data/raw/fed_fomc_task612")
TASK608K_PANEL = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv")
TASK608K_TAXONOMY = Path("docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv")
CIK_MAP = Path("data/raw/fundamental/sec_companyfacts/company_tickers.json")
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
FED_FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
SEC_USER_AGENT = "Minjo Quant Research Task612 contact@example.com"


SEC_RELEVANT_FORMS = {
    "8-K",
    "6-K",
    "10-Q",
    "10-K",
    "20-F",
    "40-F",
    "DEF 14A",
    "DEFA14A",
    "S-1",
    "S-3",
    "424B2",
    "424B3",
    "424B5",
}
EARNINGS_PROXY_FORMS = {"10-Q", "10-K", "20-F", "40-F"}
IR_PROXY_FORMS = {"8-K", "6-K"}
CAPITAL_MARKET_FORMS = {"S-1", "S-3", "424B2", "424B3", "424B5"}


def build_task612_historical_intelligence_event_backtest(
    *,
    task608k_panel: Path = TASK608K_PANEL,
    task608k_taxonomy: Path = TASK608K_TAXONOMY,
    cik_map_path: Path = CIK_MAP,
    raw_sec_dir: Path = RAW_SEC_DIR,
    raw_fed_dir: Path = RAW_FED_DIR,
    out_dir: Path = REPORT_DIR,
    fetch_sources: bool = True,
) -> dict[str, pd.DataFrame]:
    panel = load_task608k_panel(task608k_panel, task608k_taxonomy)
    symbols = sorted(panel["symbol"].astype(str).unique().tolist())
    symbol_ciks = load_symbol_ciks(cik_map_path, symbols)
    sec_events, sec_status = load_or_fetch_sec_events(symbol_ciks, raw_sec_dir, fetch_sources=fetch_sources)
    fomc_events, fed_status = load_or_fetch_fomc_events(raw_fed_dir, fetch_sources=fetch_sources)
    gpt_review = build_gpt_review_pack()
    coverage = build_source_lane_coverage(symbols, sec_status, fed_status)
    linked = link_events_to_entries(panel, sec_events, fomc_events)
    scenario_summary = build_event_overlay_scenarios(linked)
    pass_fail = build_pass_fail_matrix(scenario_summary, coverage)
    decision = build_decision(linked, scenario_summary, coverage, pass_fail, gpt_review)

    out_dir.mkdir(parents=True, exist_ok=True)
    sec_events.to_csv(out_dir / "historical_intelligence_events.csv", index=False)
    fomc_events.to_csv(out_dir / "fed_fomc_events.csv", index=False)
    coverage.to_csv(out_dir / "source_lane_coverage.csv", index=False)
    linked.to_csv(out_dir / "entry_event_linkage.csv", index=False)
    scenario_summary.to_csv(out_dir / "event_overlay_scenario_summary.csv", index=False)
    pass_fail.to_csv(out_dir / "task_612_pass_fail_matrix.csv", index=False)
    gpt_review.to_csv(out_dir / "gpt_historical_event_review_pack.csv", index=False)
    decision.to_csv(out_dir / "task_612_decision.csv", index=False)
    (out_dir / "task_612_historical_intelligence_event_backtest.md").write_text(
        render_report(sec_events, fomc_events, coverage, scenario_summary, pass_fail, decision, gpt_review),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "historical_intelligence_events": sec_events,
        "fed_fomc_events": fomc_events,
        "source_lane_coverage": coverage,
        "entry_event_linkage": linked,
        "event_overlay_scenario_summary": scenario_summary,
        "task_612_pass_fail_matrix": pass_fail,
        "gpt_historical_event_review_pack": gpt_review,
        "task_612_decision": decision,
    }


def load_task608k_panel(panel_path: Path, taxonomy_path: Path) -> pd.DataFrame:
    panel = pd.read_csv(panel_path)
    taxonomy = pd.read_csv(taxonomy_path)
    taxonomy_cols = ["lifecycle_id", "failure_type_v2", "failure_reason_v2", "detection_horizon"]
    panel = panel.merge(taxonomy[taxonomy_cols], on="lifecycle_id", how="left")
    panel["failure_type_v2"] = panel["failure_type_v2"].fillna("clean_or_non_failure")
    panel["failure_reason_v2"] = panel["failure_reason_v2"].fillna("not_failure")
    panel["detection_horizon"] = panel["detection_horizon"].fillna("not_failure")
    panel["entry_reduce_failure_flag"] = pd.to_numeric(panel["entry_reduce_failure_flag"], errors="coerce").fillna(0).astype(int)
    panel["net_return_from_entry"] = pd.to_numeric(panel["net_return_from_entry"], errors="coerce").fillna(0.0)
    panel["trade_date"] = pd.to_datetime(panel["trade_date"]).dt.date
    panel["entry_ts_utc"] = pd.to_datetime(panel["entry_ts"], utc=True)
    panel["quarter"] = panel["quarter"].astype(str)
    scored = add_turboquant_scores(panel)
    return scored


def load_symbol_ciks(cik_map_path: Path, symbols: list[str]) -> dict[str, dict[str, Any]]:
    raw = json.loads(cik_map_path.read_text(encoding="utf-8"))
    by_symbol = {str(value["ticker"]).upper(): value for value in raw.values()}
    rows: dict[str, dict[str, Any]] = {}
    for symbol in symbols:
        value = by_symbol.get(symbol.upper())
        if value is None:
            rows[symbol] = {"symbol": symbol, "cik": None, "company_name": None, "cik_status": "MISSING"}
        else:
            rows[symbol] = {
                "symbol": symbol,
                "cik": int(value["cik_str"]),
                "company_name": value["title"],
                "cik_status": "FOUND",
            }
    return rows


def load_or_fetch_sec_events(
    symbol_ciks: dict[str, dict[str, Any]],
    raw_dir: Path,
    *,
    fetch_sources: bool,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    headers = {"User-Agent": SEC_USER_AGENT}
    for symbol, cik_info in symbol_ciks.items():
        cik = cik_info["cik"]
        if cik is None:
            status_rows.append(
                {
                    "symbol": symbol,
                    "source_lane": "sec_company_submissions",
                    "status": "CIK_MISSING",
                    "raw_path": "",
                    "event_count": 0,
                }
            )
            continue
        cik10 = f"{int(cik):010d}"
        raw_path = raw_dir / f"CIK{cik10}.json"
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
                    "symbol": symbol,
                    "source_lane": "sec_company_submissions",
                    "status": "RAW_MISSING",
                    "raw_path": raw_path.as_posix(),
                    "event_count": 0,
                }
            )
            continue
        data = json.loads(raw_path.read_text(encoding="utf-8"))
        symbol_rows = parse_sec_submission_events(symbol, cik_info, data)
        rows.extend(symbol_rows)
        status_rows.append(
            {
                "symbol": symbol,
                "source_lane": "sec_company_submissions",
                "status": status,
                "raw_path": raw_path.as_posix(),
                "event_count": len(symbol_rows),
            }
        )
    events = pd.DataFrame(rows)
    if events.empty:
        events = pd.DataFrame(
            columns=[
                "event_id",
                "symbol",
                "company_name",
                "source_lane",
                "event_date",
                "acceptance_ts_utc",
                "form",
                "event_group",
                "accession_number",
                "primary_document",
                "primary_doc_description",
                "source_url",
                "official_source_flag",
            ]
        )
    else:
        events = events.sort_values(["symbol", "event_date", "acceptance_ts_utc", "form"], kind="stable").reset_index(drop=True)
    return events, pd.DataFrame(status_rows)


def parse_sec_submission_events(symbol: str, cik_info: dict[str, Any], data: dict[str, Any]) -> list[dict[str, Any]]:
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
        if form not in SEC_RELEVANT_FORMS and not form.startswith("424B"):
            continue
        filing_date = _parse_date(_get_list_value(filing_dates, idx))
        if filing_date is None:
            continue
        accession = str(_get_list_value(accessions, idx) or "")
        acceptance_ts = parse_sec_acceptance(_get_list_value(acceptance_times, idx))
        primary_doc = str(_get_list_value(docs, idx) or "")
        cik10 = f"{int(cik_info['cik']):010d}"
        accession_no_dash = accession.replace("-", "")
        source_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_info['cik'])}/{accession_no_dash}/{primary_doc}" if accession and primary_doc else ""
        rows.append(
            {
                "event_id": f"SEC|{symbol}|{filing_date.isoformat()}|{form}|{accession}",
                "symbol": symbol,
                "company_name": cik_info["company_name"],
                "source_lane": "sec_company_submissions",
                "event_date": filing_date.isoformat(),
                "acceptance_ts_utc": acceptance_ts.isoformat() if acceptance_ts is not None else "",
                "form": form,
                "event_group": classify_sec_form(form),
                "accession_number": accession,
                "primary_document": primary_doc,
                "primary_doc_description": str(_get_list_value(descriptions, idx) or ""),
                "source_url": source_url,
                "official_source_flag": 1,
                "cik10": cik10,
            }
        )
    return rows


def parse_sec_acceptance(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value)
    try:
        parsed = pd.to_datetime(text, utc=True, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()
    except (TypeError, ValueError):
        return None


def classify_sec_form(form: str) -> str:
    if form in EARNINGS_PROXY_FORMS:
        return "periodic_earnings_proxy"
    if form in IR_PROXY_FORMS:
        return "current_report_or_ir_proxy"
    if form in CAPITAL_MARKET_FORMS or form.startswith("424B"):
        return "capital_markets_proxy"
    if form in {"DEF 14A", "DEFA14A"}:
        return "governance_proxy"
    return "other_relevant_sec"


def load_or_fetch_fomc_events(raw_dir: Path, *, fetch_sources: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "fomccalendars.html"
    status = "CACHE_USED"
    if fetch_sources and not raw_path.exists():
        response = requests.get(FED_FOMC_URL, timeout=30)
        response.raise_for_status()
        raw_path.write_text(response.text, encoding="utf-8")
        status = "FETCHED"
    if not raw_path.exists():
        events = pd.DataFrame(columns=["event_id", "source_lane", "event_date", "meeting_label", "source_url", "official_source_flag"])
        status_df = pd.DataFrame(
            [{"source_lane": "fed_fomc_calendar", "status": "RAW_MISSING", "raw_path": raw_path.as_posix(), "event_count": 0}]
        )
        return events, status_df
    html = raw_path.read_text(encoding="utf-8")
    events = parse_fomc_calendar(html)
    status_df = pd.DataFrame(
        [{"source_lane": "fed_fomc_calendar", "status": status, "raw_path": raw_path.as_posix(), "event_count": len(events)}]
    )
    return events, status_df


def parse_fomc_calendar(html: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    plain = re.sub(r"<[^>]+>", " ", html)
    plain = re.sub(r"\s+", " ", plain)
    month_map = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    for year in (2024, 2025, 2026):
        start = plain.find(f"{year} FOMC Meetings")
        if start < 0:
            continue
        following_year_match = re.search(r"\b20\d{2} FOMC Meetings\b", plain[start + 20 :])
        end = start + 20 + following_year_match.start() if following_year_match else len(plain)
        section = plain[start:end]
        for match in re.finditer(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:-(\d{1,2}))?\*?",
            section,
        ):
            month_name, start_day, end_day = match.groups()
            event_day = int(end_day or start_day)
            event_date = date(year, month_map[month_name], event_day)
            rows.append(
                {
                    "event_id": f"FED_FOMC|{event_date.isoformat()}",
                    "source_lane": "fed_fomc_calendar",
                    "event_date": event_date.isoformat(),
                    "meeting_label": f"{month_name} {start_day}" + (f"-{end_day}" if end_day else ""),
                    "source_url": FED_FOMC_URL,
                    "official_source_flag": 1,
                }
            )
    return pd.DataFrame(rows).drop_duplicates("event_id").sort_values("event_date").reset_index(drop=True)


def build_source_lane_coverage(symbols: list[str], sec_status: pd.DataFrame, fed_status: pd.DataFrame) -> pd.DataFrame:
    sec_active_symbols = int(sec_status["status"].isin(["FETCHED", "CACHE_USED"]).sum()) if not sec_status.empty else 0
    fed_active = int(fed_status["status"].isin(["FETCHED", "CACHE_USED"]).any()) if not fed_status.empty else 0
    rows = [
        {
            "source_lane": "sec_company_submissions",
            "source_owner": "Data & Market Microstructure",
            "coverage_status": "ACTIVE_OFFICIAL",
            "official_source_flag": 1,
            "symbols_covered": sec_active_symbols,
            "symbols_required": len(symbols),
            "backtest_use": "company filing event flags only",
        },
        {
            "source_lane": "fed_fomc_calendar",
            "source_owner": "Regime Research",
            "coverage_status": "ACTIVE_OFFICIAL" if fed_active else "SOURCE_MISSING",
            "official_source_flag": fed_active,
            "symbols_covered": len(symbols) if fed_active else 0,
            "symbols_required": len(symbols),
            "backtest_use": "scheduled macro event risk flag only",
        },
        {
            "source_lane": "trump_and_major_person_statements",
            "source_owner": "News Research Desk",
            "coverage_status": "SOURCE_LANE_PENDING",
            "official_source_flag": 0,
            "symbols_covered": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used; no approximation",
        },
        {
            "source_lane": "war_geopolitical_events",
            "source_owner": "News Research Desk",
            "coverage_status": "SOURCE_LANE_PENDING",
            "official_source_flag": 0,
            "symbols_covered": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used; no approximation",
        },
        {
            "source_lane": "institution_reports_and_investment_actions",
            "source_owner": "Public Equity Investing",
            "coverage_status": "SOURCE_LANE_PENDING",
            "official_source_flag": 0,
            "symbols_covered": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used; no approximation",
        },
        {
            "source_lane": "ceo_ir_transcripts_and_presentations",
            "source_owner": "Public Equity Investing",
            "coverage_status": "SOURCE_LANE_PENDING",
            "official_source_flag": 0,
            "symbols_covered": 0,
            "symbols_required": len(symbols),
            "backtest_use": "not used until transcript source is certified",
        },
    ]
    return pd.DataFrame(rows)


def link_events_to_entries(panel: pd.DataFrame, sec_events: pd.DataFrame, fomc_events: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    if not sec_events.empty:
        sec = sec_events.copy()
        sec["event_date_obj"] = pd.to_datetime(sec["event_date"]).dt.date
        sec["acceptance_dt"] = pd.to_datetime(sec["acceptance_ts_utc"], utc=True, errors="coerce")
    else:
        sec = pd.DataFrame(columns=["symbol", "event_date_obj", "acceptance_dt", "event_group", "form", "event_id"])
    if not fomc_events.empty:
        fomc_dates = [pd.to_datetime(value).date() for value in fomc_events["event_date"].tolist()]
    else:
        fomc_dates = []

    rows: list[dict[str, Any]] = []
    for _, row in out.iterrows():
        trade_date = row["trade_date"]
        symbol_sec = sec[sec["symbol"].eq(row["symbol"])]
        eligible_sec = symbol_sec[symbol_sec.apply(lambda event: _event_known_by_entry(event, trade_date, row["entry_ts_utc"]), axis=1)]
        pre7 = eligible_sec[eligible_sec["event_date_obj"].between(trade_date - timedelta(days=7), trade_date)]
        pre3 = eligible_sec[eligible_sec["event_date_obj"].between(trade_date - timedelta(days=3), trade_date)]
        same_day = eligible_sec[eligible_sec["event_date_obj"].eq(trade_date)]
        earnings_pre14 = eligible_sec[
            eligible_sec["event_group"].eq("periodic_earnings_proxy")
            & eligible_sec["event_date_obj"].between(trade_date - timedelta(days=14), trade_date)
        ]
        ir_pre7 = eligible_sec[
            eligible_sec["event_group"].eq("current_report_or_ir_proxy")
            & eligible_sec["event_date_obj"].between(trade_date - timedelta(days=7), trade_date)
        ]
        capital_pre30 = eligible_sec[
            eligible_sec["event_group"].eq("capital_markets_proxy")
            & eligible_sec["event_date_obj"].between(trade_date - timedelta(days=30), trade_date)
        ]
        nearest_sec = _nearest_event(pre7, trade_date)
        fomc_near = [d for d in fomc_dates if abs((trade_date - d).days) <= 3]
        prior_fomc = [d for d in fomc_dates if 0 <= (trade_date - d).days <= 3]
        event_density = int(len(pre7)) + int(len(fomc_near))
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "company_sec_event_pre7d_flag": int(len(pre7) > 0),
                "company_sec_event_pre3d_flag": int(len(pre3) > 0),
                "company_sec_same_day_before_entry_flag": int(len(same_day) > 0),
                "earnings_proxy_sec_pre14d_flag": int(len(earnings_pre14) > 0),
                "ir_proxy_sec_pre7d_flag": int(len(ir_pre7) > 0),
                "capital_market_sec_pre30d_flag": int(len(capital_pre30) > 0),
                "fomc_calendar_near_3d_flag": int(len(fomc_near) > 0),
                "fomc_calendar_prior_3d_flag": int(len(prior_fomc) > 0),
                "official_event_density": event_density,
                "official_event_density_ge2_flag": int(event_density >= 2),
                "nearest_sec_event_id": nearest_sec.get("event_id", ""),
                "nearest_sec_event_group": nearest_sec.get("event_group", ""),
                "nearest_sec_event_date": nearest_sec.get("event_date", ""),
                "nearest_sec_event_form": nearest_sec.get("form", ""),
                "source_lanes_pending_count": 4,
                "label_used_in_assignment_flag": 0,
                "gpt_or_plugin_used_as_source_flag": 0,
            }
        )
    linkage = out.merge(pd.DataFrame(rows), on="lifecycle_id", how="left")
    if "label_used_in_assignment_flag_x" in linkage.columns:
        linkage["label_used_in_assignment_flag"] = linkage["label_used_in_assignment_flag_x"].fillna(
            linkage.get("label_used_in_assignment_flag_y", 0)
        )
        linkage = linkage.drop(
            columns=[col for col in ["label_used_in_assignment_flag_x", "label_used_in_assignment_flag_y"] if col in linkage.columns]
        )
    linkage["event_task610_exact_flag"] = linkage["task610_exact_review_trigger_flag"].astype(int)
    linkage["event_task610_or_density_ge2_flag"] = (
        linkage["event_task610_exact_flag"].eq(1) | linkage["official_event_density_ge2_flag"].eq(1)
    ).astype(int)
    linkage["event_task610_and_company_pre7_flag"] = (
        linkage["event_task610_exact_flag"].eq(1) & linkage["company_sec_event_pre7d_flag"].eq(1)
    ).astype(int)
    linkage["turboquant_attention_event_gate_flag"] = (
        linkage["plugin_need_gate_flag"].eq(1)
        & (
            linkage["company_sec_event_pre7d_flag"].eq(1)
            | linkage["fomc_calendar_near_3d_flag"].eq(1)
            | linkage["official_event_density_ge2_flag"].eq(1)
        )
    ).astype(int)
    return linkage


def _event_known_by_entry(event: pd.Series, trade_date: date, entry_ts_utc: pd.Timestamp) -> bool:
    event_date = event["event_date_obj"]
    if event_date < trade_date:
        return True
    if event_date > trade_date:
        return False
    acceptance_dt = event.get("acceptance_dt")
    if pd.isna(acceptance_dt):
        return False
    return acceptance_dt <= entry_ts_utc


def _nearest_event(events: pd.DataFrame, trade_date: date) -> dict[str, Any]:
    if events.empty:
        return {}
    ranked = events.copy()
    ranked["days_abs"] = ranked["event_date_obj"].map(lambda value: abs((trade_date - value).days))
    selected = ranked.sort_values(["days_abs", "event_date_obj"], ascending=[True, False], kind="stable").iloc[0]
    return selected.to_dict()


def build_event_overlay_scenarios(linked: pd.DataFrame) -> pd.DataFrame:
    scenario_cols = [
        ("company_sec_event_pre7d", "company_sec_event_pre7d_flag"),
        ("company_sec_event_pre3d", "company_sec_event_pre3d_flag"),
        ("company_sec_same_day_before_entry", "company_sec_same_day_before_entry_flag"),
        ("earnings_proxy_sec_pre14d", "earnings_proxy_sec_pre14d_flag"),
        ("ir_proxy_sec_pre7d", "ir_proxy_sec_pre7d_flag"),
        ("capital_market_sec_pre30d", "capital_market_sec_pre30d_flag"),
        ("fomc_calendar_near_3d", "fomc_calendar_near_3d_flag"),
        ("fomc_calendar_prior_3d", "fomc_calendar_prior_3d_flag"),
        ("official_event_density_ge2", "official_event_density_ge2_flag"),
        ("task610_exact_review_trigger", "event_task610_exact_flag"),
        ("task610_or_event_density_ge2", "event_task610_or_density_ge2_flag"),
        ("task610_and_company_pre7", "event_task610_and_company_pre7_flag"),
        ("turboquant_attention_event_gate", "turboquant_attention_event_gate_flag"),
    ]
    rows = []
    for scenario, flag_col in scenario_cols:
        selected = linked[linked[flag_col].fillna(0).astype(int).eq(1)]
        rows.append(_profile_scenario(linked, selected, scenario))
    return pd.DataFrame(rows)


def _profile_scenario(panel: pd.DataFrame, selected: pd.DataFrame, scenario: str) -> dict[str, Any]:
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


def build_pass_fail_matrix(scenarios: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    active_official_count = int(coverage["coverage_status"].eq("ACTIVE_OFFICIAL").sum())
    pending_count = int(coverage["coverage_status"].eq("SOURCE_LANE_PENDING").sum())
    pure_event = scenarios[~scenarios["scenario"].str.contains("task610|turboquant", case=False, regex=True)].copy()
    best_event = pure_event.sort_values(
        ["failure_rate_lift_pct_point", "failure_count", "trigger_count"],
        ascending=[False, False, False],
        kind="stable",
    ).iloc[0]
    task610 = scenarios[scenarios["scenario"].eq("task610_exact_review_trigger")].iloc[0]
    best_diagnostic_pass = int(
        int(best_event["trigger_count"]) >= 5
        and float(best_event["failure_rate_lift_pct_point"]) >= 15.0
        and float(best_event["clean_false_ratio"]) <= 0.60
    )
    source_completeness_pass = int(active_official_count >= 2 and pending_count == 0)
    rows = [
        {
            "gate": "official_source_ingestion",
            "pass_flag": int(active_official_count >= 2),
            "metric": f"{active_official_count} official lanes active",
            "threshold": ">=2 active official lanes",
        },
        {
            "gate": "event_overlay_diagnostic_candidate",
            "pass_flag": best_diagnostic_pass,
            "metric": f"{best_event['scenario']} triggers={int(best_event['trigger_count'])} lift={float(best_event['failure_rate_lift_pct_point']):.2f}pp clean_false={float(best_event['clean_false_ratio']):.2%}",
            "threshold": "triggers>=5, failure lift>=15pp, clean false<=60%",
        },
        {
            "gate": "task610_reference_review_trigger",
            "pass_flag": int(
                int(task610["trigger_count"]) >= 5
                and float(task610["failure_rate_lift_pct_point"]) >= 15.0
                and float(task610["clean_false_ratio"]) <= 0.60
            ),
            "metric": f"{task610['scenario']} triggers={int(task610['trigger_count'])} lift={float(task610['failure_rate_lift_pct_point']):.2f}pp clean_false={float(task610['clean_false_ratio']):.2%}",
            "threshold": "reference only; not event-lane promotion",
        },
        {
            "gate": "source_completeness_for_trading_promotion",
            "pass_flag": source_completeness_pass,
            "metric": f"{pending_count} source lanes pending",
            "threshold": "0 pending material intelligence lanes",
        },
        {
            "gate": "no_leakage_or_label_assignment",
            "pass_flag": 1,
            "metric": "same-day SEC filings require acceptance_ts <= entry_ts; labels not used in assignment",
            "threshold": "no inferred lifecycle, no post-entry same-day filings, no labels",
        },
    ]
    return pd.DataFrame(rows)


def build_gpt_review_pack() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT coding/investment project",
                "captured_status": "CAPTURED",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "Use official sparse event lanes as diagnostic risk flags; do not infer news/person/war/institution events without certified sources.",
                "repo_action": "Task612 uses SEC submissions and Fed calendar only; source gaps are explicit pending lanes.",
                "review_checklist": "Time-valid official sources only; accepted_time guard for filings; no Task610-specific after-the-fact tuning; source-missing narrative lanes stay excluded.",
            },
            {
                "reviewer": "Chrome ChatGPT coding/investment project",
                "captured_status": "CAPTURED",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "Diagnostic promotion needs enough triggers, clear lift over 39.33% baseline, clean-false control, fold-forward direction, and timestamp audit.",
                "repo_action": "Task612 pass/fail separates pure event overlays from the existing Task610 review trigger.",
                "review_checklist": "Promote as diagnostic overlay only when source audit and fold evidence are strong; never promote to trading rule in this task.",
            }
        ]
    )


def build_decision(
    linked: pd.DataFrame,
    scenarios: pd.DataFrame,
    coverage: pd.DataFrame,
    pass_fail: pd.DataFrame,
    gpt_review: pd.DataFrame,
) -> pd.DataFrame:
    official_lanes = int(coverage["coverage_status"].eq("ACTIVE_OFFICIAL").sum())
    pending_lanes = int(coverage["coverage_status"].eq("SOURCE_LANE_PENDING").sum())
    best = scenarios.sort_values(
        ["failure_rate_lift_pct_point", "failure_count", "trigger_count"],
        ascending=[False, False, False],
        kind="stable",
    ).iloc[0]
    pure_event = scenarios[~scenarios["scenario"].str.contains("task610|turboquant", case=False, regex=True)].copy()
    best_event = pure_event.sort_values(
        ["failure_rate_lift_pct_point", "failure_count", "trigger_count"],
        ascending=[False, False, False],
        kind="stable",
    ).iloc[0]
    diagnostic_pass = int(pass_fail[pass_fail["gate"].eq("event_overlay_diagnostic_candidate")]["pass_flag"].iloc[0])
    trading_promotion_pass = int(pass_fail[pass_fail["gate"].eq("source_completeness_for_trading_promotion")]["pass_flag"].iloc[0])
    decision = (
        "PASS_OFFICIAL_EVENT_DIAGNOSTIC_FAIL_TRADING_PROMOTION"
        if diagnostic_pass
        else "FAIL_OFFICIAL_EVENT_OVERLAY_KEEP_TASK610_REVIEW_TRIGGER"
    )
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": decision,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "entry_count": int(len(linked)),
                "failure_count": int(linked["entry_reduce_failure_flag"].sum()),
                "baseline_failure_rate": float(linked["entry_reduce_failure_flag"].mean()),
                "official_source_lanes_active": official_lanes,
                "source_lanes_pending": pending_lanes,
                "best_overall_scenario": best["scenario"],
                "best_overall_trigger_count": int(best["trigger_count"]),
                "best_overall_failure_count": int(best["failure_count"]),
                "best_event_scenario": best_event["scenario"],
                "best_trigger_count": int(best_event["trigger_count"]),
                "best_failure_count": int(best_event["failure_count"]),
                "best_failure_rate": float(best_event["failure_rate"]),
                "best_failure_rate_lift_pct_point": float(best_event["failure_rate_lift_pct_point"]),
                "best_clean_false_ratio": float(best_event["clean_false_ratio"]),
                "event_diagnostic_pass_flag": diagnostic_pass,
                "trading_promotion_pass_flag": trading_promotion_pass,
                "gpt_review_used_flag": 1,
                "gpt_used_as_source_flag": int(gpt_review["gpt_output_used_as_source_flag"].max()),
                "next_action": "Certify missing Trump/person/war/institution/transcript lanes, then rerun sparse event overlay with fold-forward and source-health gates.",
            }
        ]
    )


def render_report(
    sec_events: pd.DataFrame,
    fomc_events: pd.DataFrame,
    coverage: pd.DataFrame,
    scenarios: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
    gpt_review: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    best = scenarios[scenarios["scenario"].eq(d["best_event_scenario"])].iloc[0]
    top = scenarios.sort_values(["failure_rate_lift_pct_point", "failure_count"], ascending=[False, False], kind="stable").head(6)
    return f"""# Task612 Historical Intelligence Event Backtest

## Decision Summary

- Verdict: `{d['decision']}`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Entries tested: {int(d['entry_count'])}
- Failures tested: {int(d['failure_count'])}
- Baseline failure rate: {float(d['baseline_failure_rate']) * 100.0:.2f}%
- Official source lanes active: {int(d['official_source_lanes_active'])}
- Source lanes pending: {int(d['source_lanes_pending'])}
- Best event scenario: `{d['best_event_scenario']}` ({int(best['trigger_count'])} triggers, {int(best['failure_count'])} failures, {float(best['failure_rate']) * 100.0:.2f}% failure rate, {float(best['failure_rate_lift_pct_point']):.2f}pp lift)
- What changed: SEC company submissions and Federal Reserve FOMC calendar are now connected to the Task608K entry panel without post-entry same-day filing leakage.
- Next action: certify the missing Trump/person/war/institution/transcript lanes before any event overlay can become more than diagnostic review.

## Quant Expert Report

### Data Source And Source Readiness

- SEC company submissions: {len(sec_events)} relevant events from official SEC submission JSON.
- Federal Reserve FOMC calendar: {len(fomc_events)} scheduled events from the official Fed calendar.
- Pending lanes are not approximated: Trump and major-person statements, war/geopolitical events, institution reports and investment actions, CEO/IR transcripts and presentations.
- GPT/Chrome output is review-only and has `gpt_output_used_as_source_flag=0`.

### Exact Join Keys

- Company event join: `symbol` plus `event_date <= trade_date`.
- Same-day SEC leakage guard: same-day filings count only when `acceptance_ts_utc <= entry_ts_utc`.
- Fed event join: scheduled `event_date` within calendar windows around `trade_date`; no policy outcome text is used.
- Lifecycle join remains exact `lifecycle_id`; no symbol/date/price/time proximity fallback is used for lifecycle labels.

### Leakage Audit

- Labels/outcomes are evaluation-only.
- SEC post-entry same-day filings are excluded.
- FOMC is used as known scheduled calendar risk, not statement interpretation.
- Missing source lanes are reported as source gaps, not filled with guesses.

### Split/OOS Metrics

- This is a first diagnostic overlay, not a rule-lock.
- Fold-forward promotion remains blocked until more source lanes are certified and event sample sizes are larger.

### Failure Decomposition

{markdown_table(top[['scenario','trigger_count','failure_count','clean_false_count','failure_rate','failure_rate_lift_pct_point','clean_false_ratio','size_down_50_avg_return_delta_pct_point']])}

### Cost/Slippage Stress

- No new trade execution rule is promoted.
- The 50% size-down delta is reported only as a diagnostic stress proxy.

### Remaining Blockers

{markdown_table(coverage[['source_lane','coverage_status','backtest_use']])}

## No-Background Decision-Maker Report

- 한 줄 결론: 공식 이벤트를 붙이는 길은 맞지만, 아직 돈 넣을 규칙은 아닙니다.
- SEC/Fed만 붙였고, 나머지 큰 뉴스 줄은 아직 빈칸입니다.
- 가장 좋은 표식도 지금은 위험 알림 수준입니다.
- 그래서 전략 상태는 그대로 `NOT_ACCEPTED` 입니다.
- 다음은 Trump/전쟁/기관/CEO 발언 줄을 공식 출처로 붙이는 일입니다.

## Artifact Manifest

### Inputs

- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/entry_upgrade_feature_panel_v2.csv`
- `docs/reports/task_608k_failure_taxonomy_v2_conditional_treatment/failure_taxonomy_v2_panel.csv`
- `data/raw/fundamental/sec_companyfacts/company_tickers.json`
- `data/raw/sec_submissions_task612/`
- `data/raw/fed_fomc_task612/fomccalendars.html`

### Outputs

- `historical_intelligence_events.csv`
- `fed_fomc_events.csv`
- `source_lane_coverage.csv`
- `entry_event_linkage.csv`
- `event_overlay_scenario_summary.csv`
- `task_612_pass_fail_matrix.csv`
- `gpt_historical_event_review_pack.csv`
- `task_612_decision.csv`
- `task_612_historical_intelligence_event_backtest.md`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task612_historical_intelligence_event_backtest`
- `python scripts\\task_registry_validate.py`
- `python scripts\\operating_closeout_validate.py`
- `python scripts\\governance_completion_audit.py`
"""


def _get_list_value(values: list[Any], idx: int) -> Any:
    return values[idx] if idx < len(values) else None


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "| empty |\n|---|"
    string_frame = frame.copy()
    for col in string_frame.columns:
        if pd.api.types.is_float_dtype(string_frame[col]):
            string_frame[col] = string_frame[col].map(lambda value: f"{float(value):.4f}")
        else:
            string_frame[col] = string_frame[col].astype(str)
    header = "| " + " | ".join(string_frame.columns) + " |"
    divider = "| " + " | ".join(["---"] * len(string_frame.columns)) + " |"
    body = ["| " + " | ".join(row) + " |" for row in string_frame.to_numpy(dtype=str)]
    return "\n".join([header, divider, *body])


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return pd.to_datetime(str(value)).date()
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-fetch", action="store_true", help="Use cached raw source files only.")
    args = parser.parse_args()
    artifacts = build_task612_historical_intelligence_event_backtest(fetch_sources=not args.no_fetch)
    decision = artifacts["task_612_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={decision['decision']} "
        f"best={decision['best_event_scenario']} "
        f"triggers={decision['best_trigger_count']} "
        f"failures={decision['best_failure_count']}"
    )


if __name__ == "__main__":
    main()
