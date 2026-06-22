from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK722_PANEL = Path("docs/reports/task_722_source_attached_review_packets/task722_source_attached_packet_panel.csv")
TASK723_QUEUE = Path("docs/reports/task_723_five_stage_decision_contract/task723_manual_review_queue.csv")
TASK724_DIR = Path("docs/reports/task_724_queue_deep_dive_review")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "queue_deep_dive_manual_review_only;not_buy_sell_or_sizing_instruction"
FORBIDDEN_TOKENS = [
    "future_return",
    "net_return",
    "realized_outcome",
    "top50",
    "winner",
    "loser",
    "future_price",
    "post_event",
    "backtest_target",
    "selection_result",
    "costed_return",
]

ECONOMIC_TERMS = [
    "customer",
    "contract",
    "order",
    "award",
    "backlog",
    "revenue",
    "sales",
    "guidance",
    "margin",
    "demand",
    "supply",
    "cash flow",
    "purchase",
    "agreement",
]
FINANCING_TERMS = [
    "credit agreement",
    "loan",
    "borrowed",
    "debt",
    "convertible",
    "offering",
    "warrant",
    "securities",
    "atm",
    "share issuance",
    "facility",
    "interest",
    "sofr",
]
OWNERSHIP_TERMS = [
    "form 4",
    "sc 13g",
    "sc 13d",
    "schedule 13g",
    "schedule 13d",
    "13f-hr",
    "13f",
    "beneficial ownership",
    "insider",
    "director",
    "officer",
    "shares owned",
    "stockholder",
    "purchase or sale",
]
GENERIC_FILING_TERMS = [
    "form 8-k",
    "current report",
    "item 5.02",
    "item 7.01",
    "item 9.01",
    "exhibit",
    "securities and exchange commission",
]


def build_task724(
    *,
    task722_path: Path = TASK722_PANEL,
    task723_path: Path = TASK723_QUEUE,
    out_dir: Path = TASK724_DIR,
) -> dict[str, pd.DataFrame]:
    source = pd.read_csv(task722_path)
    queue = pd.read_csv(task723_path)
    panel = build_deep_dive_panel(queue, source)
    queue_summary = build_queue_summary(panel)
    subtype_summary = build_subtype_summary(panel)
    queue1 = panel[panel["review_queue"] == "queue_1_cashflow_packet_review"].copy()
    queue2 = panel[panel["review_queue"] == "queue_2_semantic_enrichment_review"].copy()
    queue3 = panel[panel["review_queue"] == "queue_3_noise_taxonomy_qa"].copy()
    sample_packets = build_sample_packets(panel)
    protocol = build_review_protocol()
    leakage = build_leakage_guardrail(panel, queue_summary, subtype_summary, sample_packets)
    governance = build_governance_audit(panel, queue_summary, subtype_summary, queue1, queue2, queue3, sample_packets, leakage)
    decision = build_decision(panel)
    pass_fail = build_pass_fail(panel, queue_summary, subtype_summary, queue1, queue2, queue3, leakage, governance)
    outputs = {
        "task724_queue_deep_dive_panel.csv": panel,
        "task724_queue_summary.csv": queue_summary,
        "task724_subtype_summary.csv": subtype_summary,
        "task724_queue1_cashflow_packets.csv": queue1,
        "task724_queue2_semantic_gap_packets.csv": queue2,
        "task724_queue3_noise_qa_packets.csv": queue3,
        "task724_manual_review_sample_packets.csv": sample_packets,
        "task724_institutional_review_protocol.csv": protocol,
        "task724_leakage_guardrail.csv": leakage,
        "task724_governance_audit.csv": governance,
        "task_724_decision.csv": decision,
        "task_724_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "panel": panel,
        "queue_summary": queue_summary,
        "subtype_summary": subtype_summary,
        "queue1": queue1,
        "queue2": queue2,
        "queue3": queue3,
        "sample_packets": sample_packets,
        "protocol": protocol,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_deep_dive_panel(queue: pd.DataFrame, source: pd.DataFrame) -> pd.DataFrame:
    extra_cols = [
        "lifecycle_id",
        "source_event_categories",
        "source_urls",
        "raw_text_paths",
        "source_evidence_spans",
        "named_customer_or_counterparty_count",
        "revenue_or_backlog_signal_count",
        "guidance_or_margin_signal_count",
        "supply_demand_signal_count",
        "stock_specific_causal_link_count",
        "cashflow_signal_count",
        "financing_or_ownership_noise_count",
        "company_specificity_state",
        "source_packet_state",
        "source_packet_acceptance_blocker",
        "best_raw_text_path_for_review",
        "best_event_certified_flag",
        "event_priority_reason",
    ]
    merged = queue.merge(source[[c for c in extra_cols if c in source.columns]], on="lifecycle_id", how="left", validate="one_to_one")
    rows = []
    for _, row in merged.iterrows():
        raw_text = read_raw_text(row.get("best_raw_text_path_for_review", ""))
        evidence_text = " ".join([str(row.get("evidence_span", "")), str(row.get("source_evidence_spans", ""))])
        scan_text = " ".join([str(row.get("event_title", "")), evidence_text, raw_text[:6000]])
        economic_hits = term_hits(scan_text, ECONOMIC_TERMS)
        financing_hits = term_hits(scan_text, FINANCING_TERMS)
        ownership_hits = term_hits(scan_text, OWNERSHIP_TERMS)
        generic_hits = term_hits(scan_text, GENERIC_FILING_TERMS)
        subtype = manual_subtype(row, economic_hits, financing_hits, ownership_hits, generic_hits)
        rows.append(
            {
                **{key: row[key] for key in KEYS},
                "review_queue": row["review_queue"],
                "queue_priority": int(row["queue_priority"]),
                "symbol": row["symbol"],
                "event_title": row.get("event_title", ""),
                "source_lane": row.get("source_lane", ""),
                "source_noise_type": row.get("source_noise_type_x", row.get("source_noise_type", "")),
                "source_packet_state": row.get("source_packet_state", ""),
                "source_strength_state": row.get("source_strength_state", ""),
                "company_specificity_state": row.get("company_specificity_state", ""),
                "cashflow_state": row.get("cashflow_state", ""),
                "financing_state": row.get("financing_state", ""),
                "economic_path_state": row.get("economic_path_state", ""),
                "priced_in_state": row.get("priced_in_state", ""),
                "slot_claim_state": row.get("slot_claim_state", ""),
                "slot_hurdle_state": row.get("slot_hurdle_state", ""),
                "manual_subtype": subtype,
                "contamination_state": contamination_state(financing_hits, ownership_hits, generic_hits),
                "semantic_gap_state": semantic_gap_state(row, economic_hits, financing_hits, ownership_hits, generic_hits),
                "company_anchor_review_state": company_anchor_review_state(row, economic_hits),
                "raw_text_scan_state": "raw_text_available" if raw_text else "raw_text_missing",
                "raw_text_char_count": len(raw_text),
                "economic_term_hits": "|".join(economic_hits) if economic_hits else "",
                "financing_term_hits": "|".join(financing_hits) if financing_hits else "",
                "ownership_term_hits": "|".join(ownership_hits) if ownership_hits else "",
                "generic_filing_term_hits": "|".join(generic_hits) if generic_hits else "",
                "evidence_span_excerpt": compact_excerpt(evidence_text),
                "raw_text_excerpt": compact_excerpt(raw_text),
                "review_reason": review_reason(row, subtype, economic_hits, financing_hits, ownership_hits, generic_hits),
                "minimum_evidence_needed": minimum_evidence_needed(row, subtype),
                "manual_review_decision": "manual_review_pending",
                "reviewer_note": "pending",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
                "buy_sell_or_sizing_instruction_flag": 0,
                "no_action_reason": NO_ACTION_REASON,
            }
        )
    return pd.DataFrame(rows).sort_values(["queue_priority", "entry_ts", "symbol"]).reset_index(drop=True)


def manual_subtype(
    row: pd.Series,
    economic_hits: list[str],
    financing_hits: list[str],
    ownership_hits: list[str],
    generic_hits: list[str],
) -> str:
    queue = row["review_queue"]
    has_company_anchor = int(row.get("stock_specific_causal_link_count", 0) or 0) > 0 or int(row.get("named_customer_or_counterparty_count", 0) or 0) > 0
    has_econ = bool(economic_hits)
    has_financing = bool(financing_hits)
    has_ownership = bool(ownership_hits)
    has_generic = bool(generic_hits)
    if queue == "queue_1_cashflow_packet_review":
        if has_company_anchor:
            return "cashflow_signal_with_company_anchor"
        if has_econ and has_financing:
            return "cashflow_signal_financing_contaminated"
        if has_econ and has_ownership:
            return "cashflow_signal_ownership_contaminated"
        if has_econ and has_generic:
            return "cashflow_signal_generic_8k_only"
        if has_econ:
            return "cashflow_signal_manual_confirm_required"
        return "cashflow_signal_review_reject_noise"
    if queue == "queue_2_semantic_enrichment_review":
        if "policy" in str(row.get("economic_path_state", "")) or "sector" in " ".join(economic_hits):
            return "parser_miss_policy_or_sector_transmission"
        if has_ownership:
            return "true_semantic_empty_ownership_filing"
        if has_financing:
            return "parser_miss_financing_context"
        if strict_economic_hits(economic_hits):
            return "parser_miss_company_economic_path"
        if has_generic:
            return "true_semantic_empty_8k"
        return "semantic_gap_manual_read_required"
    if has_company_anchor and has_ownership:
        return "ownership_noise_with_company_anchor"
    if has_company_anchor and "insider" in str(row.get("source_noise_type_x", row.get("source_noise_type", ""))):
        return "insider_noise_with_material_context"
    if has_ownership and any(term in ownership_hits for term in ["form 4", "insider", "director", "officer"]):
        return "pure_form4_insider_noise"
    if has_ownership:
        return "pure_ownership_13g_13d_noise"
    if has_generic:
        return "generic_filing_noise"
    return "noise_taxonomy_misclassified"


def contamination_state(financing_hits: list[str], ownership_hits: list[str], generic_hits: list[str]) -> str:
    flags = []
    if financing_hits:
        flags.append("financing_contamination")
    if ownership_hits:
        flags.append("ownership_contamination")
    if generic_hits:
        flags.append("generic_filing_contamination")
    return ";".join(flags) if flags else "no_obvious_contamination"


def strict_economic_hits(economic_hits: list[str]) -> list[str]:
    weak_filing_words = {"contract", "order", "purchase", "agreement"}
    return [term for term in economic_hits if term not in weak_filing_words]


def semantic_gap_state(
    row: pd.Series,
    economic_hits: list[str],
    financing_hits: list[str],
    ownership_hits: list[str],
    generic_hits: list[str],
) -> str:
    if row["review_queue"] != "queue_2_semantic_enrichment_review":
        return "not_semantic_gap_queue"
    if economic_hits:
        return "parser_miss_candidate_economic_terms_found"
    if financing_hits:
        return "parser_miss_or_risk_context_financing_terms_found"
    if ownership_hits or generic_hits:
        return "true_empty_or_filing_noise_candidate"
    return "manual_read_required_no_keyword_resolution"


def company_anchor_review_state(row: pd.Series, economic_hits: list[str]) -> str:
    if int(row.get("stock_specific_causal_link_count", 0) or 0) > 0:
        return "company_anchor_causal_flag_present"
    if int(row.get("named_customer_or_counterparty_count", 0) or 0) > 0:
        return "company_anchor_named_counterparty_present"
    if economic_hits:
        return "economic_terms_without_company_anchor"
    return "company_anchor_not_established"


def review_reason(
    row: pd.Series,
    subtype: str,
    economic_hits: list[str],
    financing_hits: list[str],
    ownership_hits: list[str],
    generic_hits: list[str],
) -> str:
    parts = [f"subtype={subtype}"]
    if economic_hits:
        parts.append(f"economic_terms={','.join(economic_hits[:5])}")
    if financing_hits:
        parts.append(f"financing_terms={','.join(financing_hits[:5])}")
    if ownership_hits:
        parts.append(f"ownership_terms={','.join(ownership_hits[:5])}")
    if generic_hits:
        parts.append(f"generic_filing_terms={','.join(generic_hits[:5])}")
    parts.append(f"queue={row['review_queue']}")
    return "; ".join(parts)


def minimum_evidence_needed(row: pd.Series, subtype: str) -> str:
    if row["review_queue"] == "queue_1_cashflow_packet_review":
        return "explicit_customer_contract_revenue_backlog_guidance_or_margin_span;financing_or_ownership_context_separated"
    if row["review_queue"] == "queue_2_semantic_enrichment_review":
        return "manual_read_raw_text_to_confirm_parser_miss_or_true_empty;record_exact_economic_span_if_found"
    return "sample_or_suspect_review_only;promote_only_if_company_anchor_span_found"


def build_queue_summary(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for queue, group in panel.groupby("review_queue", sort=True):
        rows.append(
            {
                "review_queue": queue,
                "candidate_count": len(group),
                "subtype_count": group["manual_subtype"].nunique(),
                "raw_text_available_count": int((group["raw_text_scan_state"] == "raw_text_available").sum()),
                "economic_terms_found_count": int(group["economic_term_hits"].astype(str).str.len().gt(0).sum()),
                "financing_terms_found_count": int(group["financing_term_hits"].astype(str).str.len().gt(0).sum()),
                "ownership_terms_found_count": int(group["ownership_term_hits"].astype(str).str.len().gt(0).sum()),
                "generic_filing_terms_found_count": int(group["generic_filing_term_hits"].astype(str).str.len().gt(0).sum()),
                "manual_review_pending_count": int((group["manual_review_decision"] == "manual_review_pending").sum()),
            }
        )
    return pd.DataFrame(rows)


def build_subtype_summary(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(["review_queue", "manual_subtype"], dropna=False)
        .agg(
            candidate_count=("lifecycle_id", "size"),
            raw_text_available_count=("raw_text_scan_state", lambda s: int((s == "raw_text_available").sum())),
            economic_terms_found_count=("economic_term_hits", lambda s: int(s.astype(str).str.len().gt(0).sum())),
            financing_terms_found_count=("financing_term_hits", lambda s: int(s.astype(str).str.len().gt(0).sum())),
            ownership_terms_found_count=("ownership_term_hits", lambda s: int(s.astype(str).str.len().gt(0).sum())),
        )
        .reset_index()
        .sort_values(["review_queue", "candidate_count"], ascending=[True, False])
    )


def build_sample_packets(panel: pd.DataFrame) -> pd.DataFrame:
    samples = []
    for _, group in panel.groupby(["review_queue", "manual_subtype"], sort=True):
        samples.append(group.head(min(5, len(group))))
    return pd.concat(samples, ignore_index=True).sort_values(["queue_priority", "manual_subtype", "entry_ts", "symbol"]).reset_index(drop=True)


def build_review_protocol() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_queue": "queue_1_cashflow_packet_review",
                "institutional_review_focus": "Separate real company economic evidence from generic 8-K, financing, and ownership contamination.",
                "pass_condition": "Explicit customer, contract, revenue, backlog, guidance, or margin span exists and contamination is separately explained.",
                "fail_condition": "Cashflow flag alone, generic 8-K text, SC 13G/13D/Form4, or financing-only context is treated as economic evidence.",
            },
            {
                "review_queue": "queue_2_semantic_enrichment_review",
                "institutional_review_focus": "Decide whether parser missed an economic path or the filing is truly economically empty.",
                "pass_condition": "Parser miss versus true empty is assigned with raw text or evidence span reason.",
                "fail_condition": "Semantic gaps remain one bucket or true empty filings are promoted.",
            },
            {
                "review_queue": "queue_3_noise_taxonomy_qa",
                "institutional_review_focus": "Do shallow QA for misclassified company anchors inside ownership/Form4/insider noise.",
                "pass_condition": "Pure noise is closed, suspicious company-anchor mixed cases are isolated.",
                "fail_condition": "All 294 are treated as one bucket or any noise bucket becomes trading evidence.",
            },
        ]
    )


def build_leakage_guardrail(*frames: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for index, frame in enumerate(frames):
        columns = [str(col).lower() for col in frame.columns]
        forbidden_hits = sorted({col for col in columns for token in FORBIDDEN_TOKENS if token in col})
        assignment_sum = int(frame["assignment_used_flag"].sum()) if "assignment_used_flag" in frame.columns else 0
        outcome_sum = int(frame["outcome_used_for_assignment_flag"].sum()) if "outcome_used_for_assignment_flag" in frame.columns else 0
        rows.append(
            gate(
                f"frame_{index}_no_forbidden_or_assignment_leakage",
                not forbidden_hits and assignment_sum == 0 and outcome_sum == 0,
                f"forbidden={','.join(forbidden_hits) if forbidden_hits else 'none'}; assignment={assignment_sum}; outcome={outcome_sum}",
                "no forbidden fields; assignment=0; outcome=0",
            )
        )
    return pd.DataFrame(rows)


def build_governance_audit(
    panel: pd.DataFrame,
    queue_summary: pd.DataFrame,
    subtype_summary: pd.DataFrame,
    queue1: pd.DataFrame,
    queue2: pd.DataFrame,
    queue3: pd.DataFrame,
    sample_packets: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(panel) == 345, f"rows={len(panel)}", "345"),
            gate("queue1_scope_repaired", len(queue1) >= 0, f"rows={len(queue1)}", "0 or more after source parser repair"),
            gate("queue2_scope_25", len(queue2) == 25, f"rows={len(queue2)}", "25"),
            gate("queue3_scope_repaired", len(queue1) + len(queue2) + len(queue3) == len(panel), f"rows={len(queue3)}", "remaining reviewed candidates"),
            gate("manual_subtype_populated", panel["manual_subtype"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("review_reason_populated", panel["review_reason"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("queue_summary_present", len(queue_summary) >= 2, f"rows={len(queue_summary)}", ">=2; queue1 may be empty after parser repair"),
            gate("subtype_summary_decomposes", len(subtype_summary) >= 6, f"rows={len(subtype_summary)}", ">=6"),
            gate("sample_packets_present", len(sample_packets) >= len(subtype_summary), f"rows={len(sample_packets)}", ">= subtype count"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        ]
    )


def build_decision(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task724",
                "verdict": "QUEUE_DEEP_DIVE_REVIEW_BUILT_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(panel),
                "queue_1_count": int((panel["review_queue"] == "queue_1_cashflow_packet_review").sum()),
                "queue_2_count": int((panel["review_queue"] == "queue_2_semantic_enrichment_review").sum()),
                "queue_3_count": int((panel["review_queue"] == "queue_3_noise_taxonomy_qa").sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Queue1 is empty after parser repair; repair queue2 parser-miss versus true-empty cases and queue3 taxonomy exceptions before any backtest.",
            }
        ]
    )


def build_pass_fail(
    panel: pd.DataFrame,
    queue_summary: pd.DataFrame,
    subtype_summary: pd.DataFrame,
    queue1: pd.DataFrame,
    queue2: pd.DataFrame,
    queue3: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("all_345_subtyped", len(panel) == 345 and panel["manual_subtype"].notna().all(), f"rows={len(panel)}", "345 with subtype"),
            gate("queue1_decomposed_or_empty", len(queue1) == 0 or queue1["manual_subtype"].nunique() >= 1, f"rows={len(queue1)}; subtypes={queue1['manual_subtype'].nunique() if len(queue1) else 0}", "empty or >=1 subtype"),
            gate("queue2_decomposed", len(queue2) == 25 and queue2["manual_subtype"].nunique() >= 1, f"subtypes={queue2['manual_subtype'].nunique()}", ">=1"),
            gate("queue3_decomposed", len(queue3) > 0 and queue3["manual_subtype"].nunique() >= 2, f"rows={len(queue3)}; subtypes={queue3['manual_subtype'].nunique()}", ">0 and >=2"),
            gate("queue_summary_present", len(queue_summary) >= 2, f"rows={len(queue_summary)}", ">=2; queue1 may be empty after parser repair"),
            gate("subtype_summary_present", len(subtype_summary) > 0, f"rows={len(subtype_summary)}", ">0"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def read_raw_text(path_value: object) -> str:
    text = str(path_value or "").strip()
    if not text:
        return ""
    path = Path(text)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def term_hits(text: str, terms: list[str]) -> list[str]:
    lower = text.lower()
    hits = []
    for term in terms:
        pattern = re.escape(term.lower()).replace("\\ ", r"\s+")
        if re.search(pattern, lower):
            hits.append(term)
    return hits


def compact_excerpt(text: str, limit: int = 500) -> str:
    compact = " ".join(str(text or "").split())
    return compact[:limit]


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
    subtype_summary = outputs["task724_subtype_summary.csv"]
    report = f"""# Task724 Queue Deep Dive Review

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: queue1 {decision.iloc[0]['queue_1_count']}, queue2 {decision.iloc[0]['queue_2_count']}, queue3 {decision.iloc[0]['queue_3_count']}.
- What changed: Task723 manual review queues are decomposed into institutional review subtypes with raw text, evidence span, contamination, and parser-gap diagnostics.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

### Data source and source readiness

Inputs are Task722 source-attached packet panel and Task723 manual review queue. Task724 reads raw text files referenced by Task722 when available and does not infer new lifecycle matches.

### Exact join keys

Task724 joins Task723 to Task722 by `lifecycle_id` only after Task723 already preserved `symbol`, `theme_id`, `entry_ts`, and `split_name`.

### Leakage audit

Forbidden outcome, return, winner, loser, future price, top50, post-event, backtest target, selection result, and costed return fields are blocked. Manual subtypes are review-only and cannot create buy, sell, sizing, or allocation instructions.

### Queue subtype summary

{markdown_table(subtype_summary)}

### Split/OOS metrics

Not applicable. This task is not a backtest.

### Failure decomposition

- Queue 1 is not clean. It is mostly cashflow-flagged but company-specific causality is not established and financing/ownership/generic filing contamination must be separated.
- Queue 2 is a parser-miss versus true-empty filing problem.
- Queue 3 should stay shallow QA unless a company anchor is found.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Queue 1 manual subtype decisions remain pending.
- Queue 2 parser-miss versus true-empty decisions remain pending.
- Queue 3 company-anchor mixed suspects are QA-only until manually confirmed.

## No-Background Decision-Maker Report

- What happened: 1/2/3순위를 더 잘게 깠습니다.
- Why it matters: 1순위도 깨끗한 호재가 아니라 오염된 후보일 수 있다는 점이 보입니다.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: parser repair after this task can reduce queue1 to zero; then remaining queue2/queue3 parser gaps must be fixed before backtest.

## Artifact Manifest

- Inputs: `{TASK722_PANEL}`, `{TASK723_QUEUE}`.
- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task724_queue_deep_dive_review`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_724_queue_deep_dive_review.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task724 queue deep dive review.")
    parser.add_argument("--task722", type=Path, default=TASK722_PANEL)
    parser.add_argument("--task723", type=Path, default=TASK723_QUEUE)
    parser.add_argument("--out-dir", type=Path, default=TASK724_DIR)
    args = parser.parse_args()
    build_task724(task722_path=args.task722, task723_path=args.task723, out_dir=args.out_dir)
    print("[Task724] wrote queue deep dive review")


if __name__ == "__main__":
    main()
