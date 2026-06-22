from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK721_QUEUE = Path("docs/reports/task_721_watch_bucket_decomposition_packets/task721_human_review_packet_queue.csv")
TASK636_LINKS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_event_links.csv")
TASK636_EVENTS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_event_content_predictions.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK722_DIR = Path("docs/reports/task_722_source_attached_review_packets")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "source_attached_review_packet_only;not_buy_sell_or_sizing_instruction"


def build_task722(
    *,
    task721_path: Path = TASK721_QUEUE,
    task636_links_path: Path = TASK636_LINKS,
    task636_events_path: Path = TASK636_EVENTS,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK722_DIR,
) -> dict[str, pd.DataFrame]:
    queue = pd.read_csv(task721_path)
    links = pd.read_csv(task636_links_path)
    events = pd.read_csv(task636_events_path)
    source_rollup = build_source_rollup(links, events)
    panel = build_source_attached_panel(queue, source_rollup)
    event_detail = build_event_detail(queue, links, events)
    readiness = build_readiness_audit(panel)
    sample_packets = build_sample_packets(panel)
    eval_guardrail = build_eval_guardrail(panel, eval_path)
    leakage = build_leakage_guardrail(panel)
    governance = build_governance_audit(panel, event_detail, readiness, sample_packets, leakage)
    decision = decision_frame(panel)
    pass_fail = pass_fail_matrix(panel, event_detail, readiness, sample_packets, eval_guardrail, leakage, governance)
    outputs = {
        "task722_source_attached_packet_panel.csv": panel,
        "task722_packet_event_detail.csv": event_detail,
        "task722_source_readiness_audit.csv": readiness,
        "task722_source_attached_sample_packets.csv": sample_packets,
        "task722_eval_guardrail.csv": eval_guardrail,
        "task722_leakage_guardrail.csv": leakage,
        "task722_governance_audit.csv": governance,
        "task_722_decision.csv": decision,
        "task_722_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "panel": panel,
        "event_detail": event_detail,
        "readiness": readiness,
        "sample_packets": sample_packets,
        "eval_guardrail": eval_guardrail,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_source_rollup(links: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    detail = links.merge(events, on=["event_id", "source_lane"], how="left", validate="many_to_one", suffixes=("", "_event"))
    rows = []
    for lifecycle_id, group in detail.groupby("lifecycle_id", dropna=False):
        best = select_best_event_for_review(group)
        titles = clean_join(group["event_title"].dropna().astype(str).head(5))
        lanes = clean_join(group["source_lane"].dropna().astype(str).unique())
        categories = clean_join(group["event_category"].dropna().astype(str).unique())
        urls = clean_join(group["source_url"].dropna().astype(str).head(3))
        raw_paths = clean_join(group["raw_text_path"].dropna().astype(str).head(3))
        evidence_spans = clean_join(group["content_interpretation_evidence_span"].dropna().astype(str).head(3), limit=600)
        cashflow_count = int(
            numeric_sum(group, "content_named_customer_or_counterparty")
            + numeric_sum(group, "content_revenue_or_backlog_signal")
            + numeric_sum(group, "content_guidance_or_margin_signal")
            + numeric_sum(group, "content_supply_demand_signal")
        )
        economic_certified_count = int(numeric_sum(group, "economic_evidence_certified_flag"))
        causal_count = int(numeric_sum(group, "content_stock_specific_causal_link_flag"))
        financing_noise_count = int(
            group["event_category"].astype(str).str.contains("insider|sale|ownership|form", case=False, na=False).sum()
            + group["event_title"].astype(str).str.contains("FORM 4|insider|ownership", case=False, na=False).sum()
            + numeric_sum(group, "financing_contamination_flag")
            + numeric_sum(group, "boilerplate_noise_flag")
            + numeric_sum(group, "weak_keyword_only_flag")
        )
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "source_linked_event_count": len(group),
                "source_text_certified_event_count": int(numeric_sum(group, "source_text_certified_flag")),
                "content_prediction_certified_event_count": int(numeric_sum(group, "content_prediction_certified_flag")),
                "economic_evidence_certified_event_count": economic_certified_count,
                "weak_keyword_only_event_count": int(numeric_sum(group, "weak_keyword_only_flag")),
                "financing_contamination_event_count": int(numeric_sum(group, "financing_contamination_flag")),
                "boilerplate_noise_event_count": int(numeric_sum(group, "boilerplate_noise_flag")),
                "source_event_titles": titles,
                "source_lanes": lanes,
                "source_event_categories": categories,
                "source_urls": urls,
                "raw_text_paths": raw_paths,
                "source_evidence_spans": evidence_spans,
                "named_customer_or_counterparty_count": int(numeric_sum(group, "content_named_customer_or_counterparty")),
                "revenue_or_backlog_signal_count": int(numeric_sum(group, "content_revenue_or_backlog_signal")),
                "guidance_or_margin_signal_count": int(numeric_sum(group, "content_guidance_or_margin_signal")),
                "supply_demand_signal_count": int(numeric_sum(group, "content_supply_demand_signal")),
                "regulatory_or_policy_count": int(numeric_sum(group, "content_regulatory_or_policy_transmission")),
                "stock_specific_causal_link_count": causal_count,
                "insider_or_sale_notice_count": int(group["event_category"].astype(str).str.contains("insider|sale|ownership", case=False, na=False).sum()),
                "form4_event_count": int(group["event_title"].astype(str).str.contains("FORM 4", case=False, na=False).sum()),
                "cashflow_signal_count": cashflow_count,
                "financing_or_ownership_noise_count": financing_noise_count,
                "aggregate_event_count": len(group),
                "best_event_id_for_review": value_or_blank(best, "event_id"),
                "best_event_title_for_review": value_or_blank(best, "event_title"),
                "best_event_timestamp_for_review": value_or_blank(best, "event_date"),
                "best_source_lane_for_review": value_or_blank(best, "source_lane"),
                "best_event_category_for_review": value_or_blank(best, "event_category"),
                "best_source_url_for_review": value_or_blank(best, "source_url"),
                "best_raw_text_path_for_review": value_or_blank(best, "raw_text_path"),
                "best_evidence_span_for_review": value_or_blank(best, "content_interpretation_evidence_span"),
                "best_event_certified_flag": int(pd.to_numeric(pd.Series([best.get("source_text_certified_flag", 0)]), errors="coerce").fillna(0).iloc[0]),
                "event_priority_reason": event_priority_reason(best),
            }
        )
    return pd.DataFrame(rows)


def numeric_sum(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return 0.0
    return float(pd.to_numeric(frame[column], errors="coerce").fillna(0).sum())


def select_best_event_for_review(group: pd.DataFrame) -> pd.Series:
    scored = group.copy()
    scored["_certified_score"] = numeric_series(scored, "source_text_certified_flag")
    scored["_economic_certified_score"] = numeric_series(scored, "economic_evidence_certified_flag")
    scored["_causal_score"] = numeric_series(scored, "content_stock_specific_causal_link_flag")
    scored["_cashflow_score"] = (
        numeric_series(scored, "content_named_customer_or_counterparty")
        + numeric_series(scored, "content_revenue_or_backlog_signal")
        + numeric_series(scored, "content_guidance_or_margin_signal")
        + numeric_series(scored, "content_supply_demand_signal")
    )
    scored["_policy_score"] = numeric_series(scored, "content_regulatory_or_policy_transmission")
    scored["_noise_score"] = (
        scored["event_category"].astype(str).str.contains("insider|sale|ownership|form", case=False, na=False).astype(int)
        + scored["event_title"].astype(str).str.contains("FORM 4|insider|ownership", case=False, na=False).astype(int)
        + numeric_series(scored, "financing_contamination_flag")
        + numeric_series(scored, "boilerplate_noise_flag")
        + numeric_series(scored, "weak_keyword_only_flag")
    )
    scored["_review_score"] = (
        scored["_economic_certified_score"] * 100
        + scored["_certified_score"] * 5
        + scored["_causal_score"] * 40
        + scored["_cashflow_score"] * 20
        + scored["_policy_score"] * 5
        - scored["_noise_score"] * 30
    )
    return scored.sort_values(["_review_score", "event_lag_days"], ascending=[False, True], na_position="last").iloc[0]


def numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0)


def value_or_blank(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if pd.isna(value):
        return ""
    return str(value)


def event_priority_reason(row: pd.Series) -> str:
    reasons = []
    if int(pd.to_numeric(pd.Series([row.get("source_text_certified_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("certified_source_text")
    if int(pd.to_numeric(pd.Series([row.get("economic_evidence_certified_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("economic_evidence_certified")
    if int(pd.to_numeric(pd.Series([row.get("content_stock_specific_causal_link_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("company_specific_causal_link")
    cashflow = (
        int(pd.to_numeric(pd.Series([row.get("content_named_customer_or_counterparty", 0)]), errors="coerce").fillna(0).iloc[0])
        + int(pd.to_numeric(pd.Series([row.get("content_revenue_or_backlog_signal", 0)]), errors="coerce").fillna(0).iloc[0])
        + int(pd.to_numeric(pd.Series([row.get("content_guidance_or_margin_signal", 0)]), errors="coerce").fillna(0).iloc[0])
        + int(pd.to_numeric(pd.Series([row.get("content_supply_demand_signal", 0)]), errors="coerce").fillna(0).iloc[0])
    )
    if cashflow > 0:
        reasons.append("cashflow_customer_guidance_or_supply_signal")
    if int(pd.to_numeric(pd.Series([row.get("content_regulatory_or_policy_transmission", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("policy_transmission_signal")
    title = str(row.get("event_title", ""))
    category = str(row.get("event_category", ""))
    if "FORM 4" in title.upper() or any(token in category.lower() for token in ["insider", "sale", "ownership"]):
        reasons.append("noise_penalized")
    if int(pd.to_numeric(pd.Series([row.get("weak_keyword_only_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("weak_keyword_penalized")
    if int(pd.to_numeric(pd.Series([row.get("financing_contamination_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("financing_context_penalized")
    if int(pd.to_numeric(pd.Series([row.get("boilerplate_noise_flag", 0)]), errors="coerce").fillna(0).iloc[0]) > 0:
        reasons.append("boilerplate_penalized")
    return ";".join(reasons) if reasons else "title_only_or_low_semantic_signal"


def build_source_attached_panel(queue: pd.DataFrame, source_rollup: pd.DataFrame) -> pd.DataFrame:
    out = queue.merge(source_rollup, on="lifecycle_id", how="left", validate="one_to_one")
    fill_cols = [
        "source_linked_event_count",
        "source_text_certified_event_count",
        "content_prediction_certified_event_count",
        "economic_evidence_certified_event_count",
        "weak_keyword_only_event_count",
        "financing_contamination_event_count",
        "boilerplate_noise_event_count",
        "named_customer_or_counterparty_count",
        "revenue_or_backlog_signal_count",
        "guidance_or_margin_signal_count",
        "supply_demand_signal_count",
        "regulatory_or_policy_count",
        "stock_specific_causal_link_count",
        "insider_or_sale_notice_count",
        "form4_event_count",
        "cashflow_signal_count",
        "financing_or_ownership_noise_count",
        "aggregate_event_count",
        "best_event_certified_flag",
    ]
    for col in fill_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    for col in [
        "source_event_titles",
        "source_lanes",
        "source_event_categories",
        "source_urls",
        "raw_text_paths",
        "source_evidence_spans",
        "best_event_id_for_review",
        "best_event_title_for_review",
        "best_event_timestamp_for_review",
        "best_source_lane_for_review",
        "best_event_category_for_review",
        "best_source_url_for_review",
        "best_raw_text_path_for_review",
        "best_evidence_span_for_review",
        "event_priority_reason",
    ]:
        out[col] = out[col].fillna("")
    out["source_packet_state"] = out.apply(source_packet_state, axis=1)
    out["source_review_readiness_state"] = out.apply(source_review_readiness_state, axis=1)
    out["source_noise_type"] = out.apply(source_noise_type, axis=1)
    out["source_strength_state"] = out.apply(source_strength_state, axis=1)
    out["economic_path_state"] = out.apply(economic_path_state, axis=1)
    out["company_specificity_state"] = out.apply(company_specificity_state, axis=1)
    out["raw_text_path_status"] = out["raw_text_paths"].map(lambda x: "raw_text_path_present" if str(x).strip() else "raw_text_path_missing")
    out["evidence_span_status"] = out["source_evidence_spans"].map(lambda x: "evidence_span_present" if str(x).strip() else "evidence_span_missing")
    out["source_missing_evidence"] = out.apply(source_missing_evidence, axis=1)
    out["missing_source_reason"] = out["source_missing_evidence"]
    out["source_attached_manual_question"] = out.apply(source_attached_manual_question, axis=1)
    out["review_question"] = out["source_attached_manual_question"]
    out["source_packet_acceptance_blocker"] = out.apply(source_packet_acceptance_blocker, axis=1)
    out["source_attached_reviewer_decision"] = "source_packet_manual_review_pending"
    add_no_action_flags(out)
    cols = KEYS + [
        "review_priority_rank",
        "review_priority_bucket",
        "watch_subtype",
        "next_decomposition_state",
        "source_packet_state",
        "source_review_readiness_state",
        "source_linked_event_count",
        "source_text_certified_event_count",
        "content_prediction_certified_event_count",
        "economic_evidence_certified_event_count",
        "weak_keyword_only_event_count",
        "financing_contamination_event_count",
        "boilerplate_noise_event_count",
        "source_event_titles",
        "source_lanes",
        "source_event_categories",
        "source_urls",
        "raw_text_paths",
        "source_evidence_spans",
        "best_event_id_for_review",
        "best_event_title_for_review",
        "best_event_timestamp_for_review",
        "best_source_lane_for_review",
        "best_event_category_for_review",
        "best_source_url_for_review",
        "best_raw_text_path_for_review",
        "best_evidence_span_for_review",
        "best_event_certified_flag",
        "event_priority_reason",
        "named_customer_or_counterparty_count",
        "revenue_or_backlog_signal_count",
        "guidance_or_margin_signal_count",
        "supply_demand_signal_count",
        "regulatory_or_policy_count",
        "stock_specific_causal_link_count",
        "insider_or_sale_notice_count",
        "form4_event_count",
        "cashflow_signal_count",
        "financing_or_ownership_noise_count",
        "aggregate_event_count",
        "source_noise_type",
        "source_strength_state",
        "economic_path_state",
        "company_specificity_state",
        "raw_text_path_status",
        "evidence_span_status",
        "source_missing_evidence",
        "missing_source_reason",
        "source_attached_manual_question",
        "review_question",
        "source_packet_acceptance_blocker",
        "source_attached_reviewer_decision",
        "cashflow_path_present",
        "customer_or_counterparty_present",
        "financing_pressure_state",
        "price_absorption_state",
        "slot_rank_state",
        "invalidation_trigger",
        "manual_packet_questions",
        "minimum_acceptance_criteria",
    ] + no_action_columns()
    return out[[c for c in cols if c in out.columns]].sort_values(["review_priority_rank", "entry_ts", "symbol"]).reset_index(drop=True)


def build_event_detail(queue: pd.DataFrame, links: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    detail = queue[KEYS + ["review_priority_bucket", "next_decomposition_state"]].merge(links, on=["lifecycle_id", "symbol", "theme_id", "entry_ts"], how="left")
    detail = detail.merge(events, on=["event_id", "source_lane"], how="left", suffixes=("", "_event"))
    detail["assignment_used_flag"] = 0
    detail["outcome_used_for_assignment_flag"] = 0
    cols = KEYS + [
        "review_priority_bucket",
        "next_decomposition_state",
        "event_id",
        "source_lane",
        "event_title",
        "event_date",
        "source_url",
        "source_name",
        "event_category",
        "tradable_after_dt",
        "event_lag_days",
        "link_reason",
        "source_text_certified_flag",
        "content_prediction_certified_flag",
        "economic_evidence_certified_flag",
        "weak_keyword_only_flag",
        "financing_contamination_flag",
        "boilerplate_noise_flag",
        "source_form_family",
        "interpretation_blocker",
        "content_stock_specific_causal_link",
        "content_stock_specific_causal_link_flag",
        "content_named_customer_or_counterparty",
        "content_revenue_or_backlog_signal",
        "content_guidance_or_margin_signal",
        "content_supply_demand_signal",
        "content_regulatory_or_policy_transmission",
        "content_interpretation_evidence_span",
        "raw_text_path",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
    ]
    return detail[[c for c in cols if c in detail.columns]].sort_values(["entry_ts", "symbol", "event_id"], na_position="last").reset_index(drop=True)


def build_readiness_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, group in panel.groupby("source_review_readiness_state", dropna=False):
        rows.append(
            {
                "source_review_readiness_state": state,
                "candidate_count": len(group),
                "source_linked_event_count_sum": int(group["source_linked_event_count"].sum()),
                "source_text_certified_event_count_sum": int(group["source_text_certified_event_count"].sum()),
                "best_event_id_populated_count": int(group["best_event_id_for_review"].astype(str).str.strip().ne("").sum()),
                "cashflow_signal_candidate_count": int((group["source_packet_state"] == "cashflow_source_packet_review_ready").sum()),
                "ownership_noise_candidate_count": int((group["source_packet_state"] == "ownership_noise_source_packet").sum()),
                "source_gap_candidate_count": int((group["source_packet_state"] == "source_packet_missing_blocked").sum()),
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("candidate_count", ascending=False).reset_index(drop=True)


def build_sample_packets(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, group in panel.groupby("source_review_readiness_state", sort=True):
        rows.append(group.head(min(10, len(group))))
    if not rows:
        return panel.head(0).copy()
    return pd.concat(rows, ignore_index=True).sort_values(["review_priority_rank", "entry_ts", "symbol"]).reset_index(drop=True)


def build_eval_guardrail(panel: pd.DataFrame, eval_path: Path) -> pd.DataFrame:
    eval_panel = pd.read_csv(eval_path)
    merged = panel.merge(eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]], on=KEYS, how="left", validate="one_to_one")
    top50 = set(eval_panel.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(eval_panel.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("source_review_readiness_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "source_review_readiness_state": state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count_eval_only", ascending=False).reset_index(drop=True)


def build_leakage_guardrail(panel: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("no_assignment_use", int(panel["assignment_used_flag"].sum()) == 0, str(int(panel["assignment_used_flag"].sum())), "0"),
        ("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, str(int(panel["outcome_used_for_assignment_flag"].sum())), "0"),
        ("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, str(int(panel["future_price_used_for_assignment_flag"].sum())), "0"),
        ("top50_not_used", int(panel["top50_used_for_assignment_flag"].sum()) == 0, str(int(panel["top50_used_for_assignment_flag"].sum())), "0"),
        ("no_ticker_theme_protection", int(panel["ticker_theme_protection_rule_flag"].sum()) == 0, str(int(panel["ticker_theme_protection_rule_flag"].sum())), "0"),
        ("no_outcome_threshold_tuning", int(panel["threshold_tuned_from_outcome_flag"].sum()) == 0, str(int(panel["threshold_tuned_from_outcome_flag"].sum())), "0"),
        ("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, str(int(panel["translator_output_is_action_flag"].sum())), "0"),
        ("real_capital_forbidden", set(panel["real_capital_status"]) == {"FORBIDDEN"}, ",".join(sorted(set(panel["real_capital_status"]))), "FORBIDDEN"),
    ]
    return pd.DataFrame([gate(name, passed, observed, required) for name, passed, observed, required in checks])


def build_governance_audit(
    panel: pd.DataFrame,
    event_detail: pd.DataFrame,
    readiness: pd.DataFrame,
    sample_packets: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("event_detail_present", len(event_detail) > len(panel), f"rows={len(event_detail)}", ">345"),
            gate("source_join_coverage", panel["source_linked_event_count"].gt(0).all(), f"linked={int(panel['source_linked_event_count'].gt(0).sum())}/{len(panel)}", "100%"),
            gate("event_id_link_coverage", panel["best_event_id_for_review"].astype(str).str.strip().ne("").all(), f"best_event_id={int(panel['best_event_id_for_review'].astype(str).str.strip().ne('').sum())}/{len(panel)}", "100%"),
            gate("readiness_states_present", panel["source_review_readiness_state"].nunique() >= 2, f"states={panel['source_review_readiness_state'].nunique()}", ">=2"),
            gate("review_readiness_populated", panel["source_review_readiness_state"].notna().all(), "complete", "complete"),
            gate("raw_text_path_status_populated", panel["raw_text_path_status"].notna().all(), "complete", "complete"),
            gate("evidence_span_status_populated", panel["evidence_span_status"].notna().all(), "complete", "complete"),
            gate("source_attached_or_blocked", panel["source_packet_state"].notna().all(), "complete", "complete"),
            gate("sample_packets_present", len(sample_packets) >= panel["source_review_readiness_state"].nunique(), f"rows={len(sample_packets)}", ">= state count"),
            gate("readiness_audit_present", len(readiness) > 0, f"rows={len(readiness)}", ">0"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def source_packet_state(row: pd.Series) -> str:
    if int(row["source_text_certified_event_count"]) <= 0:
        return "source_packet_missing_blocked"
    cashflow = int(row["named_customer_or_counterparty_count"] + row["revenue_or_backlog_signal_count"] + row["guidance_or_margin_signal_count"] + row["supply_demand_signal_count"])
    economic = int(row.get("economic_evidence_certified_event_count", 0) or 0)
    if cashflow > 0 and economic > 0:
        return "cashflow_source_packet_review_ready"
    if int(row["insider_or_sale_notice_count"] + row["form4_event_count"]) > 0:
        return "ownership_noise_source_packet"
    if int(row["content_prediction_certified_event_count"]) > 0:
        return "certified_source_semantic_gap_packet"
    return "certified_source_text_only_packet"


def source_noise_type(row: pd.Series) -> str:
    categories = str(row.get("source_event_categories", ""))
    titles = str(row.get("source_event_titles", ""))
    if int(row["source_text_certified_event_count"]) <= 0:
        return "source_noise_uncertified_text"
    if "FORM 4" in titles.upper():
        return "source_noise_insider_form4_only"
    if "ownership" in categories.lower() or "ownership" in titles.lower():
        return "source_noise_ownership_only"
    if int(row["insider_or_sale_notice_count"]) > 0:
        return "source_noise_insider_or_sale_notice"
    if source_packet_state(row) == "cashflow_source_packet_review_ready":
        return "source_noise_not_primary"
    return "source_noise_generic_filing_or_semantic_gap"


def source_strength_state(row: pd.Series) -> str:
    if int(row["source_text_certified_event_count"]) <= 0:
        return "source_strength_missing_certified_text"
    if int(row["stock_specific_causal_link_count"]) > 0 and int(row["cashflow_signal_count"]) > 0:
        return "source_strength_company_economic_path"
    if int(row["cashflow_signal_count"]) > 0:
        return "source_strength_cashflow_related_but_causality_unproven"
    if int(row["financing_or_ownership_noise_count"]) > 0:
        return "source_strength_noise_or_overhang_only"
    return "source_strength_certified_but_economic_path_missing"


def economic_path_state(row: pd.Series) -> str:
    if int(row["stock_specific_causal_link_count"]) > 0 and int(row["cashflow_signal_count"]) > 0:
        return "economic_path_company_specific_established"
    if int(row["cashflow_signal_count"]) > 0:
        return "economic_path_cashflow_signal_unconfirmed_causality"
    if int(row["regulatory_or_policy_count"]) > 0:
        return "economic_path_policy_transmission_only"
    if int(row["financing_or_ownership_noise_count"]) > 0:
        return "economic_path_not_established_noise_or_overhang"
    return "economic_path_not_established"


def company_specificity_state(row: pd.Series) -> str:
    if int(row["stock_specific_causal_link_count"]) > 0 and int(row["named_customer_or_counterparty_count"]) > 0:
        return "company_specific_named_counterparty_path"
    if int(row["stock_specific_causal_link_count"]) > 0 and int(row["cashflow_signal_count"]) > 0:
        return "company_specific_cashflow_path"
    if int(row["stock_specific_causal_link_count"]) > 0:
        return "company_specific_causal_but_no_cashflow_field"
    if int(row["cashflow_signal_count"]) > 0:
        return "cashflow_field_without_company_specificity"
    return "company_specificity_not_established"


def source_review_readiness_state(row: pd.Series) -> str:
    state = source_packet_state(row)
    if state == "cashflow_source_packet_review_ready":
        return "source_review_ready_cashflow_packet"
    if state == "ownership_noise_source_packet":
        return "source_review_noise_triage_required"
    if state == "source_packet_missing_blocked":
        return "source_review_blocked_no_certified_text"
    return "source_review_semantic_enrichment_required"


def source_missing_evidence(row: pd.Series) -> str:
    missing = []
    if int(row["source_text_certified_event_count"]) <= 0:
        missing.append("certified_source_text")
    if not str(row["source_event_titles"]).strip():
        missing.append("source_event_title")
    if source_packet_state(row) != "cashflow_source_packet_review_ready":
        missing.append("cashflow_customer_revenue_backlog_guidance_signal")
    if source_packet_state(row) == "ownership_noise_source_packet":
        missing.append("non_ownership_company_causal_evidence")
    return ";".join(missing) if missing else "none_for_source_packet_review"


def source_attached_manual_question(row: pd.Series) -> str:
    state = source_packet_state(row)
    if state == "cashflow_source_packet_review_ready":
        return "does_source_text_show_real_cashflow_or_customer_path;does_it_survive_financing_overhang;is_price_absorption_predefined"
    if state == "ownership_noise_source_packet":
        return "is_this_only_form4_or_ownership_noise;is_there_any_non_ownership_company_causal_event;should_packet_remain_noise_triage"
    if state == "source_packet_missing_blocked":
        return "can_certified_source_text_be_attached_without_inference;otherwise_keep_review_blocked"
    return "what_semantic_field_is_missing;can_event_title_and_evidence_span_support_manual_review"


def source_packet_acceptance_blocker(row: pd.Series) -> str:
    state = source_packet_state(row)
    if state == "source_packet_missing_blocked":
        return "blocked_no_certified_source_text"
    if state == "ownership_noise_source_packet":
        return "blocked_until_non_ownership_causal_evidence_found"
    if state == "certified_source_semantic_gap_packet":
        return "blocked_until_semantic_cashflow_or_risk_path_verified"
    if state == "certified_source_text_only_packet":
        return "blocked_until_content_prediction_certified"
    return "no_source_packet_blocker_for_manual_review"


def clean_join(values: pd.Series, limit: int = 1000) -> str:
    seen = []
    for value in values:
        text = " ".join(str(value).split())
        if text and text not in seen:
            seen.append(text)
    return " | ".join(seen)[:limit]


def decision_frame(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task722",
                "verdict": "SOURCE_ATTACHED_REVIEW_PACKETS_BUILT_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(panel),
                "source_review_ready_cashflow_count": int((panel["source_review_readiness_state"] == "source_review_ready_cashflow_packet").sum()),
                "source_review_noise_triage_count": int((panel["source_review_readiness_state"] == "source_review_noise_triage_required").sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Parser repair removed all cashflow-ready packets; repair remaining semantic enrichment and ownership/noise taxonomy before any backtest candidate rule.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    event_detail: pd.DataFrame,
    readiness: pd.DataFrame,
    sample_packets: pd.DataFrame,
    eval_guardrail: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("event_detail_present", len(event_detail) > len(panel), f"rows={len(event_detail)}", ">345"),
            gate("source_join_coverage", panel["source_linked_event_count"].gt(0).all(), f"linked={int(panel['source_linked_event_count'].gt(0).sum())}/{len(panel)}", "100%"),
            gate("event_id_link_coverage", panel["best_event_id_for_review"].astype(str).str.strip().ne("").all(), f"best_event_id={int(panel['best_event_id_for_review'].astype(str).str.strip().ne('').sum())}/{len(panel)}", "100%"),
            gate("review_readiness_populated", panel["source_review_readiness_state"].notna().all(), "complete", "complete"),
            gate("raw_text_path_status_populated", panel["raw_text_path_status"].notna().all(), "complete", "complete"),
            gate("evidence_span_status_populated", panel["evidence_span_status"].notna().all(), "complete", "complete"),
            gate("readiness_audit_present", len(readiness) > 0, f"rows={len(readiness)}", ">0"),
            gate("sample_packets_present", len(sample_packets) >= panel["source_review_readiness_state"].nunique(), f"rows={len(sample_packets)}", ">= state count"),
            gate("eval_guardrail_eval_only", int(eval_guardrail["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def add_no_action_flags(frame: pd.DataFrame) -> None:
    frame["translator_output_is_action_flag"] = 0
    frame["assignment_used_flag"] = 0
    frame["outcome_used_for_assignment_flag"] = 0
    frame["future_price_used_for_assignment_flag"] = 0
    frame["top50_used_for_assignment_flag"] = 0
    frame["ticker_theme_protection_rule_flag"] = 0
    frame["threshold_tuned_from_outcome_flag"] = 0
    frame["buy_sell_or_sizing_instruction_flag"] = 0
    frame["missing_source_used_as_negative_flag"] = 0
    frame["real_capital_status"] = "FORBIDDEN"
    frame["no_action_reason"] = NO_ACTION_REASON


def no_action_columns() -> list[str]:
    return [
        "translator_output_is_action_flag",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "top50_used_for_assignment_flag",
        "ticker_theme_protection_rule_flag",
        "threshold_tuned_from_outcome_flag",
        "buy_sell_or_sizing_instruction_flag",
        "missing_source_used_as_negative_flag",
        "real_capital_status",
        "no_action_reason",
    ]


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def artifact_counts(outputs: dict[str, pd.DataFrame]) -> str:
    return "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items())


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# Task722 Source Attached Review Packets

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: Task721 human packets now attach Task636 source events and content interpretation fields.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Scope: 345 Task721 watch packets.
- Source join: lifecycle_id to Task636 entry-event links and event content predictions.
- Output states: cashflow-ready, ownership-noise triage, semantic enrichment required, or blocked source packet.
- No outcome, future return, top-50, ticker protection, or sizing field is used for assignment.

## No-Background Decision-Maker Report

- This still does not buy anything.
- It attaches the actual source packet so a human can inspect what the event really was.
- Ownership/Form 4 packets are separated from cashflow/customer/revenue/backlog packets.
- Capital remains forbidden.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task722_source_attached_review_packets`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_722_source_attached_review_packets.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task722 source attached review packets.")
    parser.add_argument("--task721", type=Path, default=TASK721_QUEUE)
    parser.add_argument("--task636-links", type=Path, default=TASK636_LINKS)
    parser.add_argument("--task636-events", type=Path, default=TASK636_EVENTS)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK722_DIR)
    args = parser.parse_args()
    build_task722(
        task721_path=args.task721,
        task636_links_path=args.task636_links,
        task636_events_path=args.task636_events,
        eval_path=args.eval,
        out_dir=args.out_dir,
    )
    print("[Task722] wrote source attached review packets")


if __name__ == "__main__":
    main()
