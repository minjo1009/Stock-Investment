from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task609"
REPORT_DIR = Path("docs/reports/task_609_realtime_intelligence_trading_layer")


def build_task609_realtime_intelligence_trading_layer(
    *,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    source_contract = build_source_contract()
    event_schema = build_event_schema()
    gate_policy = build_gate_policy()
    failure_linkage = build_task608_failure_linkage()
    implementation_plan = build_implementation_plan()
    decision = build_decision(source_contract, event_schema, gate_policy, implementation_plan)

    out_dir.mkdir(parents=True, exist_ok=True)
    source_contract.to_csv(out_dir / "intelligence_source_contract.csv", index=False)
    event_schema.to_csv(out_dir / "intelligence_event_schema.csv", index=False)
    gate_policy.to_csv(out_dir / "intelligence_trading_gate_policy.csv", index=False)
    failure_linkage.to_csv(out_dir / "task608_failure_intelligence_linkage.csv", index=False)
    implementation_plan.to_csv(out_dir / "task_609_implementation_plan.csv", index=False)
    decision.to_csv(out_dir / "task_609_decision.csv", index=False)
    (out_dir / "task_609_realtime_intelligence_trading_layer.md").write_text(
        render_report(
            source_contract=source_contract,
            event_schema=event_schema,
            gate_policy=gate_policy,
            failure_linkage=failure_linkage,
            implementation_plan=implementation_plan,
            decision=decision,
        ),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "intelligence_source_contract": source_contract,
        "intelligence_event_schema": event_schema,
        "intelligence_trading_gate_policy": gate_policy,
        "task608_failure_intelligence_linkage": failure_linkage,
        "task_609_implementation_plan": implementation_plan,
        "task_609_decision": decision,
    }


def build_source_contract() -> pd.DataFrame:
    rows = [
        {
            "source_type": "regulatory_filing",
            "owner_team": "Data & Market Microstructure",
            "minimum_raw_fields": "source_id; issuer; published_at_utc; captured_at_utc; raw_path; url_or_accession",
            "allowed_use": "high_confidence_context; hard_negative_gate_when_exactly_linked",
            "forbidden_use": "infer_missing_filing_as_good_news",
            "priority": "P0",
            "source_readiness": "CONTRACT_ONLY_SOURCE_NOT_CONNECTED",
        },
        {
            "source_type": "official_company_release",
            "owner_team": "Data & Market Microstructure",
            "minimum_raw_fields": "source_id; issuer; published_at_utc; captured_at_utc; raw_path; url",
            "allowed_use": "catalyst_confirmation; contradiction_check",
            "forbidden_use": "headline_only_trade",
            "priority": "P0",
            "source_readiness": "CONTRACT_ONLY_SOURCE_NOT_CONNECTED",
        },
        {
            "source_type": "key_person_statement",
            "owner_team": "Regime Research",
            "minimum_raw_fields": "speaker; role; venue; published_at_utc; captured_at_utc; transcript_or_quote_path",
            "allowed_use": "macro_theme_risk; policy_or_management_tone_context",
            "forbidden_use": "unverified_quote_trade",
            "priority": "P1",
            "source_readiness": "CONTRACT_ONLY_SOURCE_NOT_CONNECTED",
        },
        {
            "source_type": "news_wire_or_verified_media",
            "owner_team": "Intraday Continuation Research",
            "minimum_raw_fields": "publisher; headline; published_at_utc; captured_at_utc; raw_path; url",
            "allowed_use": "fresh_catalyst_filter; news_fade_detection",
            "forbidden_use": "single_unconfirmed_negative_direct_exit",
            "priority": "P1",
            "source_readiness": "CONTRACT_ONLY_SOURCE_NOT_CONNECTED",
        },
        {
            "source_type": "institution_research_report",
            "owner_team": "Regime Research",
            "minimum_raw_fields": "institution; report_title; published_at_utc; captured_at_utc; raw_path; access_scope",
            "allowed_use": "theme_quality_score; estimate_revision_context",
            "forbidden_use": "copyright_text_replication; unlicensed_redistribution",
            "priority": "P2",
            "source_readiness": "CONTRACT_ONLY_SOURCE_NOT_CONNECTED",
        },
    ]
    return pd.DataFrame(rows)


def build_event_schema() -> pd.DataFrame:
    fields = [
        ("intelligence_event_id", "string", "Exact stable event id. Required for joins."),
        ("source_type", "enum", "One of the approved source contract types."),
        ("source_id", "string", "Provider id, accession id, url hash, or internal capture id."),
        ("symbol", "string", "Ticker when directly linked. Empty only for market or theme events."),
        ("theme_id", "string", "Theme or sector basket id when symbol is indirect."),
        ("speaker_or_institution", "string", "Named speaker, company, agency, or institution."),
        ("published_at_utc", "timestamp", "Source-published timestamp. Never approximated."),
        ("captured_at_utc", "timestamp", "System receive timestamp for replay."),
        ("event_type", "enum", "earnings; guidance; contract; policy; downgrade; upgrade; investigation; macro; theme_rotation; other"),
        ("stance", "enum", "positive; neutral; negative; mixed; unknown"),
        ("novelty_score", "float", "0 to 1 score for new information versus already-known context."),
        ("relevance_score", "float", "0 to 1 score for symbol or theme relevance."),
        ("confidence_score", "float", "0 to 1 source and extraction confidence."),
        ("tradable_window_start_utc", "timestamp", "Earliest time this event may affect a paper decision."),
        ("tradable_window_end_utc", "timestamp", "Latest allowed evaluation window."),
        ("raw_path", "path", "Stored raw artifact path under data/raw when available."),
        ("evidence_hash", "sha256", "Hash of raw or normalized evidence."),
        ("processing_model", "string", "Parser or LLM version used for extraction."),
        ("human_review_required_flag", "int", "1 when event can block, shrink, or exit-review a trade."),
        ("no_trade_if_unverified_flag", "int", "1 when missing verification must block direct use."),
        ("label_leakage_guard", "string", "Outcomes and future returns cannot enter event assignment."),
    ]
    return pd.DataFrame(
        [{"field_name": name, "field_type": kind, "purpose": purpose, "required_flag": 1} for name, kind, purpose in fields]
    )


def build_gate_policy() -> pd.DataFrame:
    rows = [
        {
            "gate_name": "verified_negative_fresh_event",
            "condition": "confidence_score>=0.80 and relevance_score>=0.70 and stance=negative and captured_before_decision=1",
            "paper_trading_action": "block_new_entry_or_size_down",
            "live_capital_action": "FORBIDDEN",
            "llm_direct_trade_allowed_flag": 0,
            "owner_team": "Execution & Risk",
        },
        {
            "gate_name": "fresh_positive_catalyst_with_confirmation",
            "condition": "confidence_score>=0.80 and novelty_score>=0.60 and price_continuation_confirmed=1",
            "paper_trading_action": "allow_standard_entry_after_existing_price_gate",
            "live_capital_action": "FORBIDDEN",
            "llm_direct_trade_allowed_flag": 0,
            "owner_team": "Intraday Continuation Research",
        },
        {
            "gate_name": "contradictory_or_low_confidence_event",
            "condition": "confidence_score<0.80 or source_conflict_flag=1",
            "paper_trading_action": "no_new_entry_until_review",
            "live_capital_action": "FORBIDDEN",
            "llm_direct_trade_allowed_flag": 0,
            "owner_team": "Research Governance",
        },
        {
            "gate_name": "theme_rotation_warning",
            "condition": "theme_or_sector_event_negative=1 and theme_relevance_score>=0.70",
            "paper_trading_action": "require_extra_confirmation_or_reduce_candidate_rank",
            "live_capital_action": "FORBIDDEN",
            "llm_direct_trade_allowed_flag": 0,
            "owner_team": "Regime Research",
        },
        {
            "gate_name": "stale_catalyst_or_news_fade",
            "condition": "breakout_age_high=1 and no_fresh_positive_event=1 and opening_fade_state=1",
            "paper_trading_action": "delay_entry_or_exit_review_only",
            "live_capital_action": "FORBIDDEN",
            "llm_direct_trade_allowed_flag": 0,
            "owner_team": "Backtest & Simulation Infra",
        },
    ]
    return pd.DataFrame(rows)


def build_task608_failure_linkage() -> pd.DataFrame:
    rows = [
        {
            "task608_failure_type": "opening_trap_vwap_loss",
            "count_from_task608k": 7,
            "likely_missing_information": "news_fade_or_unconfirmed_opening_catalyst",
            "intelligence_test": "Was the opening move backed by fresh verified news before entry?",
            "proposed_first_action": "30_60m_wait_for_confirmation",
        },
        {
            "task608_failure_type": "opening_trap_range_rejection",
            "count_from_task608k": 6,
            "likely_missing_information": "headline_exhaustion_or_fast_reversal_after_event",
            "intelligence_test": "Did source quality weaken while price rejected the opening range?",
            "proposed_first_action": "120m_review_before_full_size",
        },
        {
            "task608_failure_type": "late_followthrough_failure",
            "count_from_task608k": 7,
            "likely_missing_information": "stale_catalyst_or_late_report_chase",
            "intelligence_test": "Was the breakout based on old information already priced in?",
            "proposed_first_action": "exit_trailing_review_not_entry_reduce",
        },
        {
            "task608_failure_type": "failed_continuation_demand_decay",
            "count_from_task608k": 5,
            "likely_missing_information": "lack_of_incremental_buyer_reason",
            "intelligence_test": "Did volume decay coincide with no new verified catalyst?",
            "proposed_first_action": "require_continuation_confirmation",
        },
        {
            "task608_failure_type": "market_or_theme_drag",
            "count_from_task608k": 2,
            "likely_missing_information": "sector_rotation_or_macro_speaker_risk",
            "intelligence_test": "Did sector ETF, policy, macro, or leader narrative turn against the setup?",
            "proposed_first_action": "theme_gate_rank_down",
        },
    ]
    return pd.DataFrame(rows)


def build_implementation_plan() -> pd.DataFrame:
    rows = [
        {
            "step_id": "Task609A",
            "priority": "P0",
            "owner_team": "Data & Market Microstructure",
            "work_item": "Create raw capture folders and exact timestamp/source-id contract for intelligence events.",
            "acceptance_check": "Every captured event has source_id, published_at_utc, captured_at_utc, raw_path, evidence_hash.",
        },
        {
            "step_id": "Task609B",
            "priority": "P0",
            "owner_team": "Research Governance",
            "work_item": "Add no-direct-trade rule for LLM and text events.",
            "acceptance_check": "llm_direct_trade_allowed_flag is 0 for every trading gate.",
        },
        {
            "step_id": "Task610",
            "priority": "P1",
            "owner_team": "Backtest & Simulation Infra",
            "work_item": "Replay historical Task608 failures against captured or manually audited intelligence windows.",
            "acceptance_check": "No event is joined by symbol/date proximity alone; exact event ids and timestamps are present.",
        },
        {
            "step_id": "Task611",
            "priority": "P1",
            "owner_team": "Intraday Continuation Research",
            "work_item": "Paper-only entry gate test: block, wait, size-down, or review based on verified events.",
            "acceptance_check": "Gate improves failure concentration without cutting clean winners after cost stress.",
        },
        {
            "step_id": "Task612",
            "priority": "P2",
            "owner_team": "Frontend/UI",
            "work_item": "Show simple trade explanation: price setup, news reason, risk reason, missing evidence.",
            "acceptance_check": "Every paper trade card can show why entered, why blocked, or why watched.",
        },
    ]
    return pd.DataFrame(rows)


def build_decision(
    source_contract: pd.DataFrame,
    event_schema: pd.DataFrame,
    gate_policy: pd.DataFrame,
    implementation_plan: pd.DataFrame,
) -> pd.DataFrame:
    p0_count = int(implementation_plan["priority"].astype(str).eq("P0").sum())
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": "BUILD_INTELLIGENCE_LAYER_BEFORE_REFINEMENT",
                "pass_flag": 1,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "source_contract_count": int(len(source_contract)),
                "schema_field_count": int(len(event_schema)),
                "trading_gate_count": int(len(gate_policy)),
                "p0_next_step_count": p0_count,
                "llm_direct_trade_allowed_flag": int(gate_policy["llm_direct_trade_allowed_flag"].max()),
                "real_capital_status": "FORBIDDEN",
                "next_task": "Task609A/Task609B then Task610 historical intelligence replay",
            }
        ]
    )


def render_report(
    *,
    source_contract: pd.DataFrame,
    event_schema: pd.DataFrame,
    gate_policy: pd.DataFrame,
    failure_linkage: pd.DataFrame,
    implementation_plan: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    decision_row = decision.iloc[0]
    lines = [
        "# Task609 Realtime Intelligence Trading Layer",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision_row['decision']}`",
        "- Strategy acceptance status: `NOT_ACCEPTED`",
        "- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`",
        f"- Key metrics: {len(source_contract)} source contracts, {len(event_schema)} event fields, {len(gate_policy)} paper-trading gates",
        "- What changed: news, key-person statements, filings, company releases, and institution reports are defined as evidence-gated inputs.",
        "- Next action: build Task609A/Task609B capture and no-direct-trade controls, then run Task610 historical replay against Task608 failures.",
        "",
        "## Quant Expert Report",
        "",
        "### Data Source And Source Readiness",
        "",
        "- Current state: contract only. No new live source is certified by this task.",
        "- Source readiness: `CONTRACT_ONLY_SOURCE_NOT_CONNECTED` for every listed source type.",
        "- LLM role: extraction/review helper only. LLM output is not a source of truth and cannot trade directly.",
        "",
        "### Exact Join Keys",
        "",
        "- Required join keys: `intelligence_event_id`, `source_id`, `published_at_utc`, `captured_at_utc`, `symbol`, `theme_id`, `evidence_hash`.",
        "- Forbidden joins: symbol/date/price/time proximity fallback.",
        "- Missing evidence: reported as missing, never converted into positive or negative signal.",
        "",
        "### Leakage Audit",
        "",
        "- Future returns, final trade outcome, and Task608 failure labels cannot enter intelligence event assignment.",
        "- Events can affect a replay decision only after `captured_at_utc` and inside the declared tradable window.",
        "- Institution reports must not be redistributed; only metadata, derived labels, and allowed summaries may be stored.",
        "",
        "### Split/OOS Metrics",
        "",
        "- Not applicable yet. This task defines the layer. Task610 must test historical replay before any strategy claim.",
        "",
        "### Failure Decomposition",
        "",
        "- Task608K's 35 failures are now linked to missing information hypotheses.",
        "- Opening traps map to fresh-catalyst and fade checks.",
        "- Late followthrough maps to stale-catalyst and exit/trailing review.",
        "- Market/theme drag maps to macro, sector, and leader narrative checks.",
        "",
        "### Cost/Slippage Stress",
        "",
        "- Not applicable until Task611 paper gate simulations change entry, size, wait, or exit timing.",
        "",
        "### Remaining Blockers",
        "",
        "- Real-time source credentials and raw archive are not connected.",
        "- Historical event windows are not replayed yet.",
        "- Strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "- Chart alone tells us what happened, but not why.",
        "- This task adds the missing why-layer: news, public statements, filings, company releases, and institution reports.",
        "- The system must not buy or sell just because an LLM says so.",
        "- First use this layer to block bad entries, wait for confirmation, reduce candidate rank, and explain trade decisions.",
        "- This does not make the strategy accepted yet.",
        "",
        "## Artifact Manifest",
        "",
        "### Inputs",
        "",
        "- Existing Task608 failure taxonomy and project governance rules.",
        "- No external live news feed is consumed in this task.",
        "",
        "### Outputs",
        "",
        "- `intelligence_source_contract.csv`",
        "- `intelligence_event_schema.csv`",
        "- `intelligence_trading_gate_policy.csv`",
        "- `task608_failure_intelligence_linkage.csv`",
        "- `task_609_implementation_plan.csv`",
        "- `task_609_decision.csv`",
        "- `artifact_manifest.csv`",
        "",
        "### Row Counts",
        "",
        f"- source_contract_rows: {len(source_contract)}",
        f"- event_schema_rows: {len(event_schema)}",
        f"- trading_gate_rows: {len(gate_policy)}",
        f"- task608_failure_linkage_rows: {len(failure_linkage)}",
        f"- implementation_plan_rows: {len(implementation_plan)}",
        "",
        "### Validation Commands",
        "",
        "- `python -m unittest tests.test_task609_realtime_intelligence_trading_layer`",
        "- `python scripts/task_registry_validate.py`",
        "- `python scripts/operating_closeout_validate.py`",
        "",
        "### Source Hashes",
        "",
        "- See `artifact_manifest.csv` after generation.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task609_realtime_intelligence_trading_layer(out_dir=args.out_dir)
    decision = artifacts["task_609_decision"].iloc[0]
    print(f"[{TASK_ID}] decision={decision['decision']} out_dir={args.out_dir}")


if __name__ == "__main__":
    main()
