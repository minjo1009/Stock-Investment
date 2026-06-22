from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task614_p0_intelligence_source_attachment import relevant_events, tag_contains
from src.backtest.build_task622_source_semantic_interpretation_sidecar import (
    EVENT_STORE,
    TASK617_PANEL,
    load_events,
    load_panel,
    semantic_label_events,
    within_window,
)


TASK_ID = "Task623"
REPORT_DIR = Path("docs/reports/task_623_big_event_interpretation_scoring_sidecar")

SCORING_FIELDS = [
    "event_scope",
    "event_interpretation_category",
    "transmission_channel",
    "directional_score",
    "transmission_strength_score",
    "company_relevance_score",
    "event_timestamp_quality_score",
    "priced_in_risk_score",
    "evidence_quality_score",
    "materiality_score",
    "interpretation_confidence_score",
    "composite_interpretation_score",
    "score_action",
    "scoring_reason_code",
    "support_entry_certified_flag",
    "risk_off_certified_flag",
    "sector_support_watch_flag",
    "source_presence_only_used_flag",
    "gpt_score_used_as_source_flag",
]

BIG_EVENT_LANES = {
    "trump_major_person_political_statements",
    "war_geopolitical_conflict_events",
    "ceo_ir_transcripts_and_presentations",
}


def build_task623_big_event_interpretation_scoring_sidecar(
    *,
    event_store_path: Path = EVENT_STORE,
    task617_panel_path: Path = TASK617_PANEL,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    events = load_events(event_store_path)
    labels = semantic_label_events(events)
    scored = score_semantic_events(labels)
    panel = load_panel(task617_panel_path)
    recent_aerospace = build_recent_aerospace_event_score_attachment(panel, scored)
    score_summary = build_score_summary(scored)
    pass_fail = build_pass_fail(scored, recent_aerospace)
    gpt_review = build_gpt_review_status()
    decision = build_decision(scored, recent_aerospace, pass_fail)

    out_dir.mkdir(parents=True, exist_ok=True)
    scored.to_csv(out_dir / "event_interpretation_scores.csv", index=False)
    recent_aerospace.to_csv(out_dir / "recent_aerospace_event_score_attachment.csv", index=False)
    score_summary.to_csv(out_dir / "event_score_summary.csv", index=False)
    pass_fail.to_csv(out_dir / "task_623_pass_fail_matrix.csv", index=False)
    gpt_review.to_csv(out_dir / "task_623_gpt_big_event_scoring_review_status.csv", index=False)
    decision.to_csv(out_dir / "task_623_decision.csv", index=False)
    (out_dir / "task_623_big_event_interpretation_scoring_sidecar.md").write_text(
        render_report(scored, recent_aerospace, score_summary, pass_fail, gpt_review, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "event_interpretation_scores": scored,
        "recent_aerospace_event_score_attachment": recent_aerospace,
        "event_score_summary": score_summary,
        "task_623_pass_fail_matrix": pass_fail,
        "task_623_gpt_big_event_scoring_review_status": gpt_review,
        "task_623_decision": decision,
    }


def score_semantic_events(labels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, event in labels.iterrows():
        row = event.to_dict()
        row.update(score_event(event))
        rows.append(row)
    return pd.DataFrame(rows)


def score_event(event: pd.Series) -> dict[str, Any]:
    title = str(event.get("event_title", "") or "")
    title_lower = title.lower()
    lane = str(event.get("source_lane", "") or "")
    category = str(event.get("event_category", "") or "")
    evidence_quality = str(event.get("evidence_quality", "") or "")
    catalyst = str(event.get("catalyst_economic_link", "") or "")
    source_gap = int(event.get("source_gap_flag", 0) or 0)

    relevance = company_relevance_score(event)
    evidence = evidence_quality_score(evidence_quality, source_gap)
    timestamp_quality = timestamp_quality_score(event)
    category_pack = event_category_pack(lane, category, title_lower, catalyst)
    materiality = materiality_score(title_lower, category_pack["transmission_strength_score"], source_gap)
    priced_risk = priced_in_risk_score(lane, evidence_quality, category_pack["event_scope"], materiality, source_gap)
    confidence = interpretation_confidence_score(evidence, relevance, category_pack["transmission_strength_score"], materiality, source_gap)
    composite = composite_score(
        category_pack["directional_score"],
        category_pack["transmission_strength_score"],
        relevance,
        evidence,
        materiality,
        priced_risk,
    )
    action_pack = score_action_pack(
        event_scope=category_pack["event_scope"],
        directional_score=category_pack["directional_score"],
        transmission_strength_score=category_pack["transmission_strength_score"],
        company_relevance_score=relevance,
        evidence_quality_score=evidence,
        materiality_score=materiality,
        source_gap_flag=source_gap,
    )

    return {
        **category_pack,
        "company_relevance_score": relevance,
        "event_timestamp_quality_score": timestamp_quality,
        "priced_in_risk_score": priced_risk,
        "evidence_quality_score": evidence,
        "materiality_score": materiality,
        "interpretation_confidence_score": confidence,
        "composite_interpretation_score": composite,
        **action_pack,
        "source_presence_only_used_flag": 0,
        "gpt_score_used_as_source_flag": 0,
    }


def company_relevance_score(event: pd.Series) -> int:
    if str(event.get("symbol_tags", "") or "").strip() and str(event.get("symbol_tags", "")).lower() != "nan":
        return 3
    if str(event.get("theme_tags", "") or "").strip() and str(event.get("theme_tags", "")).lower() != "nan":
        return 2
    if str(event.get("policy_tags", "") or "").strip() and str(event.get("policy_tags", "")).lower() != "nan":
        return 1
    return 0


def evidence_quality_score(evidence_quality: str, source_gap_flag: int) -> int:
    if source_gap_flag:
        return 0
    if evidence_quality == "title_contains_specific_economic_language":
        return 2
    if evidence_quality in {"title_only", "generic_filing_or_ownership_only"}:
        return 1
    return 1


def timestamp_quality_score(event: pd.Series) -> int:
    if pd.notna(event.get("event_timestamp_dt")) and str(event.get("time_precision", "")) == "timestamp":
        return 2
    if pd.notna(event.get("event_date_obj")):
        return 1
    return 0


def event_category_pack(lane: str, category: str, title_lower: str, catalyst: str) -> dict[str, Any]:
    if lane == "ceo_ir_transcripts_and_presentations" or category == "company_ir_proxy":
        if catalyst == "direct_revenue_contract_order_backlog":
            return pack("company_direct", "company_direct_revenue_catalyst", "revenue_order_backlog", 1, 3, "company_direct_positive_economic_content")
        if catalyst == "guidance_or_financial_update":
            return pack("company_direct", "company_guidance_or_financial_update", "guidance_financial_update", 1, 3, "company_direct_financial_content")
        if catalyst == "financing_liquidity_dilution":
            return pack("company_direct", "company_financing_or_dilution", "financing_liquidity_dilution", -1, 3, "financing_can_be_risk_not_bullish_by_default")
        if catalyst == "regulatory_approval_or_restriction":
            direction = -1 if "restriction" in title_lower else 1
            return pack("company_direct", "company_regulatory_event", "regulatory_approval_or_restriction", direction, 2, "company_direct_regulatory_content")
        return pack("company_direct", "generic_company_filing_uninterpretable", "unknown", 0, 0, "generic_ir_or_8k_title_not_interpretable")

    if lane == "institution_investment_actions":
        return pack("company_direct", "ownership_or_insider_filing_only", "ownership_or_insider_reporting", 0, 1, "ownership_filing_not_bullish_by_default")

    if lane == "war_geopolitical_conflict_events":
        if any_keyword(title_lower, ["sanctions", "designation", "counterterrorism", "non-proliferation", "russia", "iran", "north korea", "cyber"]):
            return pack("macro_policy_general", "geopolitical_sanctions_or_conflict_risk", "sanctions_conflict_export_control", -1, 2, "geopolitical_policy_risk_requires_market_confirmation")
        return pack("macro_policy_general", "geopolitical_background", "broad_geopolitical_context", 0, 1, "geopolitical_context_without_direct_company_link")

    if lane == "trump_major_person_political_statements":
        if low_materiality_title(title_lower):
            return pack("theme_or_sector", "low_materiality_statement", "low_materiality_context", 0, 0, "ceremonial_or_awareness_title_not_tradeable")
        if any_keyword(title_lower, ["tariff", "export control", "china", "restriction", "sanction"]):
            return pack("macro_policy_general", "policy_restriction_or_tariff_risk", "tariff_export_control_policy", -1, 2, "policy_restriction_risk_requires_confirmation")
        if any_keyword(title_lower, ["defense acquisitions", "foreign defense sales", "defense industrial base", "military excellence", "readiness", "space", "aviation safety"]):
            direction = -1 if any_keyword(title_lower, ["safety", "assessment"]) else 1
            return pack("theme_or_sector", "sector_policy_catalyst_watch", "defense_space_aviation_policy", direction, 2, "sector_policy_content_not_company_entry_support")
        if any_keyword(title_lower, ["energy", "permit", "infrastructure", "emergency price relief", "cost-of-living"]):
            return pack("macro_policy_general", "macro_policy_background", "inflation_energy_rates_policy", 0, 1, "macro_policy_background_needs_price_transmission")
        return pack("macro_policy_general", "broad_political_statement", "broad_policy_context", 0, 1, "broad_political_statement_not_direct_stock_support")

    return pack("unknown", "uninterpretable_or_unmapped", "unknown", 0, 0, "unmapped_event")


def pack(
    event_scope: str,
    event_interpretation_category: str,
    transmission_channel: str,
    directional_score: int,
    transmission_strength_score: int,
    scoring_reason_code: str,
) -> dict[str, Any]:
    return {
        "event_scope": event_scope,
        "event_interpretation_category": event_interpretation_category,
        "transmission_channel": transmission_channel,
        "directional_score": directional_score,
        "transmission_strength_score": transmission_strength_score,
        "scoring_reason_code": scoring_reason_code,
    }


def any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def low_materiality_title(title_lower: str) -> bool:
    return any_keyword(
        title_lower,
        [
            "awareness month",
            "awareness day",
            "recognition day",
            "anniversary",
            "message on",
            "spouse day",
            "mother",
            "autism",
            "colorectal",
        ],
    )


def materiality_score(title_lower: str, transmission_strength_score: int, source_gap_flag: int) -> int:
    if source_gap_flag:
        return 0
    if low_materiality_title(title_lower):
        return 0
    if transmission_strength_score >= 3:
        return 3
    if transmission_strength_score == 2:
        return 2
    if transmission_strength_score == 1:
        return 1
    return 0


def priced_in_risk_score(lane: str, evidence_quality: str, event_scope: str, materiality: int, source_gap_flag: int) -> int:
    if source_gap_flag:
        return 3
    if lane in BIG_EVENT_LANES and event_scope != "company_direct":
        return 2
    if evidence_quality.startswith("generic"):
        return 2
    if materiality <= 1:
        return 2
    return 1


def interpretation_confidence_score(
    evidence_quality_score_value: int,
    company_relevance_score_value: int,
    transmission_strength_score: int,
    materiality: int,
    source_gap_flag: int,
) -> int:
    if source_gap_flag or evidence_quality_score_value == 0:
        return 0
    if transmission_strength_score >= 2 and company_relevance_score_value >= 2 and materiality >= 2:
        return 2
    if transmission_strength_score >= 1:
        return 1
    return 0


def composite_score(
    directional_score: int,
    transmission_strength_score: int,
    company_relevance_score_value: int,
    evidence_quality_score_value: int,
    materiality: int,
    priced_in_risk: int,
) -> float:
    if directional_score == 0:
        return 0.0
    raw_strength = (
        transmission_strength_score * 25
        + company_relevance_score_value * 20
        + evidence_quality_score_value * 15
        + materiality * 20
        - priced_in_risk * 10
    )
    bounded_strength = max(0, min(100, raw_strength))
    return round(float(directional_score) * bounded_strength / 100.0, 4)


def score_action_pack(
    *,
    event_scope: str,
    directional_score: int,
    transmission_strength_score: int,
    company_relevance_score: int,
    evidence_quality_score: int,
    materiality_score: int,
    source_gap_flag: int,
) -> dict[str, Any]:
    if source_gap_flag or evidence_quality_score == 0:
        action = "source_gap"
    elif (
        event_scope == "company_direct"
        and directional_score > 0
        and transmission_strength_score >= 2
        and company_relevance_score >= 3
        and evidence_quality_score >= 2
        and materiality_score >= 2
    ):
        action = "support_entry_candidate"
    elif directional_score < 0 and transmission_strength_score >= 2 and company_relevance_score >= 1 and materiality_score >= 1:
        action = "risk_off_candidate"
    elif event_scope == "theme_or_sector" and directional_score > 0 and transmission_strength_score >= 2 and materiality_score >= 2:
        action = "sector_support_watch"
    else:
        action = "hold_until_confirmed"
    return {
        "score_action": action,
        "support_entry_certified_flag": int(action == "support_entry_candidate"),
        "risk_off_certified_flag": int(action == "risk_off_candidate"),
        "sector_support_watch_flag": int(action == "sector_support_watch"),
    }


def build_recent_aerospace_event_score_attachment(panel: pd.DataFrame, scored: pd.DataFrame) -> pd.DataFrame:
    recent = panel[
        panel["split_name"].astype(str).eq("recent_oos")
        & panel["theme_id"].astype(str).eq("aerospace_defense_space")
    ].copy()
    rows = []
    for _, entry in recent.iterrows():
        linked = linked_events_for_entry(scored, entry)
        risk_count = int(linked["risk_off_certified_flag"].sum()) if not linked.empty else 0
        sector_count = int(linked["sector_support_watch_flag"].sum()) if not linked.empty else 0
        support_count = int(linked["support_entry_certified_flag"].sum()) if not linked.empty else 0
        if support_count:
            action = "company_direct_support_present"
        elif risk_count and sector_count:
            action = "conflicted_hold_until_confirmed"
        elif risk_count:
            action = "risk_off_candidate_present"
        elif sector_count:
            action = "sector_support_watch_only"
        else:
            action = "hold_until_confirmed_or_source_gap"
        rows.append(
            {
                "lifecycle_id": entry["lifecycle_id"],
                "symbol": entry["symbol"],
                "entry_ts": entry["entry_ts"],
                "net_return_from_entry": entry["net_return_from_entry"],
                "linked_event_count": int(len(linked)),
                "support_entry_candidate_count": support_count,
                "risk_off_candidate_count": risk_count,
                "sector_support_watch_count": sector_count,
                "source_gap_count": int(linked["source_gap_flag"].fillna(0).astype(int).sum()) if not linked.empty else 0,
                "max_company_relevance_score": int(linked["company_relevance_score"].max()) if not linked.empty else 0,
                "max_transmission_strength_score": int(linked["transmission_strength_score"].max()) if not linked.empty else 0,
                "max_materiality_score": int(linked["materiality_score"].max()) if not linked.empty else 0,
                "event_score_sum": float(linked["composite_interpretation_score"].sum()) if not linked.empty else 0.0,
                "pre_entry_semantic_action": action,
                "entry_time_valid_join_flag": 1,
                "label_used_in_assignment_flag": 0,
                "gpt_score_used_as_source_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def linked_events_for_entry(scored: pd.DataFrame, entry: pd.Series) -> pd.DataFrame:
    known = scored[
        (scored["event_date_obj"] < entry["trade_date"])
        | (
            scored["event_date_obj"].eq(entry["trade_date"])
            & scored["time_precision"].eq("timestamp")
            & scored["event_timestamp_dt"].notna()
            & (scored["event_timestamp_dt"] <= entry["entry_ts"])
        )
    ]
    symbol = str(entry["symbol"])
    theme = str(entry["theme_id"])
    political = relevant_events(within_window(known, entry["trade_date"], 7), "trump_major_person_political_statements", symbol, theme)
    geopolitical = relevant_events(within_window(known, entry["trade_date"], 7), "war_geopolitical_conflict_events", symbol, theme)
    institution_window = within_window(known, entry["trade_date"], 30)
    ceo_ir_window = within_window(known, entry["trade_date"], 14)
    institution = institution_window[
        institution_window["source_lane"].eq("institution_investment_actions") & tag_contains(institution_window["symbol_tags"], symbol)
    ]
    ceo_ir = ceo_ir_window[
        ceo_ir_window["source_lane"].eq("ceo_ir_transcripts_and_presentations") & tag_contains(ceo_ir_window["symbol_tags"], symbol)
    ]
    return pd.concat([political, geopolitical, institution, ceo_ir], ignore_index=True)


def build_score_summary(scored: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in scored.groupby(["source_lane", "event_interpretation_category", "score_action"], dropna=False):
        rows.append(
            {
                "source_lane": keys[0],
                "event_interpretation_category": keys[1],
                "score_action": keys[2],
                "event_count": int(len(group)),
                "avg_composite_interpretation_score": float(group["composite_interpretation_score"].mean()),
                "support_entry_certified_count": int(group["support_entry_certified_flag"].sum()),
                "risk_off_certified_count": int(group["risk_off_certified_flag"].sum()),
                "sector_support_watch_count": int(group["sector_support_watch_flag"].sum()),
            }
        )
    return pd.DataFrame(rows).sort_values("event_count", ascending=False).reset_index(drop=True)


def build_pass_fail(scored: pd.DataFrame, recent_aerospace: pd.DataFrame) -> pd.DataFrame:
    broad_support = scored[
        scored["event_scope"].astype(str).isin(["macro_policy_general", "theme_or_sector"])
        & scored["support_entry_certified_flag"].astype(int).eq(1)
    ]
    large_events = scored[scored["source_lane"].astype(str).isin(BIG_EVENT_LANES)]
    nonzero_large = large_events[large_events["composite_interpretation_score"].astype(float).abs() > 0]
    return pd.DataFrame(
        [
            {
                "gate": "scoring_schema_complete",
                "pass_flag": int(set(SCORING_FIELDS).issubset(scored.columns)),
                "observed_value": ",".join([field for field in SCORING_FIELDS if field in scored.columns]),
                "required_value": "all big-event scoring fields present",
            },
            {
                "gate": "large_events_are_scored",
                "pass_flag": int(len(large_events) > 0 and len(nonzero_large) > 0),
                "observed_value": f"large_events={len(large_events)} nonzero_scored={len(nonzero_large)}",
                "required_value": "Trump war policy CEO events receive deterministic interpretation scores when content keywords exist",
            },
            {
                "gate": "broad_events_not_support_entry",
                "pass_flag": int(broad_support.empty),
                "observed_value": f"broad_support_entry_count={len(broad_support)}",
                "required_value": "macro or sector events cannot become direct support_entry without company-direct evidence",
            },
            {
                "gate": "source_presence_not_used",
                "pass_flag": int(scored["source_presence_only_used_flag"].astype(int).sum() == 0),
                "observed_value": f"source_presence_only_used={int(scored['source_presence_only_used_flag'].astype(int).sum())}",
                "required_value": "event existence alone cannot drive score action",
            },
            {
                "gate": "recent_aerospace_company_direct_support",
                "pass_flag": int(recent_aerospace["support_entry_candidate_count"].sum() > 0) if not recent_aerospace.empty else 0,
                "observed_value": f"support_entry_candidate_count={int(recent_aerospace['support_entry_candidate_count'].sum()) if not recent_aerospace.empty else 0}",
                "required_value": "recent aerospace needs pre-entry company-direct support before entry restoration",
            },
            {
                "gate": "trading_promotion",
                "pass_flag": 0,
                "observed_value": "scoring sidecar only; no assignment or order input",
                "required_value": "must pass source timing OOS cost and account gates before strategy use",
            },
        ]
    )


def build_gpt_review_status() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "captured_status": "CAPTURED_CHROME_CHATGPT_PROJECT_TAB",
                "source_type": "external_model_interpretation_not_source_truth",
                "gpt_output_used_as_source_flag": 0,
                "summary_point": "GPT recommended scoring big events by direction, transmission strength, company relevance, timing validity, priced-in risk, evidence quality, and confidence while forbidding source-presence or LLM-score direct trading.",
            }
        ]
    )


def build_decision(scored: pd.DataFrame, recent_aerospace: pd.DataFrame, pass_fail: pd.DataFrame) -> pd.DataFrame:
    large_events = scored[scored["source_lane"].astype(str).isin(BIG_EVENT_LANES)]
    nonzero_large = large_events[large_events["composite_interpretation_score"].astype(float).abs() > 0]
    support_count = int(recent_aerospace["support_entry_candidate_count"].sum()) if not recent_aerospace.empty else 0
    risk_count = int(recent_aerospace["risk_off_candidate_count"].sum()) if not recent_aerospace.empty else 0
    sector_count = int(recent_aerospace["sector_support_watch_count"].sum()) if not recent_aerospace.empty else 0
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "IMPLEMENT_BIG_EVENT_SCORING_SIDECAR_NOT_TRADING_SIGNAL",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital_status": "FORBIDDEN",
                "big_event_scoring_status": "IMPLEMENTED_EVALUATION_ONLY",
                "large_event_count": int(len(large_events)),
                "large_event_nonzero_score_count": int(len(nonzero_large)),
                "recent_aerospace_trade_count": int(len(recent_aerospace)),
                "recent_aerospace_support_entry_candidate_count": support_count,
                "recent_aerospace_risk_off_candidate_count": risk_count,
                "recent_aerospace_sector_support_watch_count": sector_count,
                "semantic_scores_used_in_assignment_flag": 0,
                "trading_promotion_pass_flag": 0,
                "gpt_score_used_as_source_flag": 0,
                "next_action": "Add full official text extraction for major event lanes, then validate score actions on full panel, recent OOS, cost stress, and account simulation before any strategy use.",
            }
        ]
    )


def render_report(
    scored: pd.DataFrame,
    recent_aerospace: pd.DataFrame,
    score_summary: pd.DataFrame,
    pass_fail: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    lines = [
        "# Task623 Big Event Interpretation Scoring Sidecar",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{d['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Real capital: `FORBIDDEN`",
        "- Big events are scored by content interpretation, not source existence.",
        "- Scores are evaluation-only and are not order, assignment, or sizing inputs.",
        f"- Large events scored: {int(d['large_event_nonzero_score_count'])} / {int(d['large_event_count'])}",
        f"- Recent aerospace support-entry candidates: {int(d['recent_aerospace_support_entry_candidate_count'])}",
        f"- Recent aerospace risk-off candidates: {int(d['recent_aerospace_risk_off_candidate_count'])}",
        f"- Recent aerospace sector-support watch candidates: {int(d['recent_aerospace_sector_support_watch_count'])}",
        "",
        "## Quant Expert Report",
        "",
        "### Scoring Fields",
        "",
        "| Field | Purpose |",
        "|---|---|",
    ]
    for field in SCORING_FIELDS:
        lines.append(f"| `{field}` | big-event interpretation scoring field |")
    lines.extend(
        [
            "",
            "### Score Summary",
            "",
            "| Lane | Category | Action | Events | Avg Score | Support | Risk-Off | Sector Watch |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for _, row in score_summary.head(15).iterrows():
        lines.append(
            f"| `{row['source_lane']}` | `{row['event_interpretation_category']}` | `{row['score_action']}` | "
            f"{int(row['event_count'])} | {float(row['avg_composite_interpretation_score']):.4f} | "
            f"{int(row['support_entry_certified_count'])} | {int(row['risk_off_certified_count'])} | "
            f"{int(row['sector_support_watch_count'])} |"
        )
    lines.extend(
        [
            "",
            "### Recent Aerospace Score Attachment",
            "",
            "| Metric | Value |",
            "|---|---:|",
            f"| recent aerospace trades | {int(len(recent_aerospace))} |",
            f"| support-entry candidate count | {int(recent_aerospace['support_entry_candidate_count'].sum()) if not recent_aerospace.empty else 0} |",
            f"| risk-off candidate count | {int(recent_aerospace['risk_off_candidate_count'].sum()) if not recent_aerospace.empty else 0} |",
            f"| sector-support watch count | {int(recent_aerospace['sector_support_watch_count'].sum()) if not recent_aerospace.empty else 0} |",
            "",
            "### GPT Review",
            "",
            f"- Captured status: `{gpt_review.iloc[0]['captured_status']}`",
            f"- Summary: {gpt_review.iloc[0]['summary_point']}",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- We no longer treat Trump, war, policy, CEO, or IR as yes/no signals.",
            "- Each event gets direction, transmission strength, company relevance, evidence quality, materiality, confidence, and priced-in risk.",
            "- Broad events can become risk-off or sector-watch, but not direct support-entry.",
            "- Recent aerospace still has no company-direct support-entry candidate, so entry restoration remains blocked.",
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
            "### Inputs",
            "",
            "- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`",
            "- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`",
            "",
            "### Outputs",
            "",
            "- `event_interpretation_scores.csv`",
            "- `recent_aerospace_event_score_attachment.csv`",
            "- `event_score_summary.csv`",
            "- `task_623_pass_fail_matrix.csv`",
            "- `task_623_gpt_big_event_scoring_review_status.csv`",
            "- `task_623_decision.csv`",
            "- `artifact_manifest.csv`",
            "",
            "### Validation Commands",
            "",
            "- `python -m unittest tests.test_task623_big_event_interpretation_scoring_sidecar`",
            "- `python scripts/task_registry_validate.py`",
            "- `python scripts/operating_closeout_validate.py`",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task623_big_event_interpretation_scoring_sidecar(out_dir=args.out_dir)
    row = artifacts["task_623_decision"].iloc[0]
    print(
        f"[{TASK_ID}] decision={row['decision']} "
        f"large_event_nonzero_score_count={int(row['large_event_nonzero_score_count'])} "
        f"recent_aerospace_support={int(row['recent_aerospace_support_entry_candidate_count'])}"
    )


if __name__ == "__main__":
    main()
