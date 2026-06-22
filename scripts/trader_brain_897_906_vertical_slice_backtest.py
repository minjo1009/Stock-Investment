from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_897_906_vertical_slice_backtest"
L1_ENRICHED = ROOT / "data/artifacts/task_895_l1_source_attachment/l1_source_evidence_seed_with_attachments.csv"
ATTACHMENT_LEDGER = ROOT / "data/artifacts/task_895_l1_source_attachment/l1_source_attachment_ledger.csv"
SOURCE_QUEUE = ROOT / "data/artifacts/task_895_l1_source_attachment/raw_source_attachment_acquisition_queue.csv"
EVENT_DATASET = ROOT / "docs/reports/task_372_historical_source_backfill/task_372_historical_source_event_dataset.csv"
DECISION_CALENDAR = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep/historical_decision_calendar.csv"
DAILY_MANIFEST = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay/daily_canonical_manifest.csv"

INITIAL_CAPITAL = 1000.0
BENCHMARK = "QQQ"
MIN_ACCEPTANCE = 0.80
MIN_RAW_LINKAGE_FOR_NON_PROVISIONAL_GRAPH = 0.95

FORBIDDEN_OUTPUT_FIELDS = {
    "future_return",
    "realized_return",
    "pnl",
    "rank",
    "score",
    "position_size",
}

PRIMITIVE_FIELDS = [
    "primitive_fact_id",
    "l1_state_id",
    "evidence_id",
    "attachment_bundle_id",
    "symbol",
    "theme",
    "available_to_brain_ts",
    "as_of_ts",
    "source_span_ref",
    "source_span_excerpt",
    "primitive_type",
    "primitive_polarity",
    "deterministic_rule_id",
    "reproducibility_hash",
    "uncertainty",
    "raw_source_gap_flag",
    "acceptance_state",
    "does_not_mean",
]

SOURCE_CONTRACT_FIELDS = [
    "theme",
    "symbol",
    "source_family",
    "source_time_field",
    "publication_time_field",
    "ingestion_time_field",
    "effective_time_field",
    "revision_policy",
    "source_priority",
    "minimum_required_fields",
    "admission_rule",
    "gap_policy",
]

RAW_REALITY_FIELDS = [
    "theme",
    "symbol",
    "coverage_state",
    "primitive_count_before_raw_source",
    "raw_source_uri_attached",
    "raw_source_hash_attached",
    "raw_source_linkage_state",
    "primitive_recheck_state",
    "blocks_task898_non_provisional",
    "does_not_mean",
]

MEANING_FIELDS = [
    "economic_meaning_id",
    "primitive_fact_id",
    "evidence_id",
    "symbol",
    "theme",
    "as_of_ts",
    "economic_channel",
    "meaning_bias",
    "uncertainty",
    "raw_source_gap_flag",
    "raw_source_linkage_state",
    "meaning_authority",
    "confidence_cap",
    "does_not_mean",
]

RELATION_FIELDS = [
    "relation_snapshot_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "available_meaning_count",
    "constructive_count",
    "confirmation_count",
    "risk_blocker_count",
    "net_relation_balance",
    "relation_state",
    "relation_authority",
    "source_meaning_ids",
    "edge_asof_ts",
    "does_not_mean",
]

CANDIDATE_FIELDS = [
    "candidate_bundle_id",
    "relation_snapshot_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "candidate_thesis_type",
    "available_meaning_count",
    "net_relation_balance",
    "raw_source_gap_flag",
    "candidate_authority",
    "adapter_eligible",
    "does_not_mean",
]

DRY_DECISION_FIELDS = [
    "trader_decision_id",
    "candidate_bundle_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "theme",
    "decision_state",
    "decision_reason",
    "raw_source_gap_flag",
    "decision_authority",
    "trade_spec_allowed",
    "diagnostic_replay_allowed",
    "does_not_mean",
]

TRADE_SPEC_FIELDS = [
    "trade_spec_id",
    "trader_decision_id",
    "candidate_bundle_id",
    "decision_id",
    "decision_asof_ts",
    "split_id",
    "symbol",
    "side",
    "tradable_after_date",
    "exit_policy",
    "allocation_policy",
    "trade_spec_authority",
    "blocked_for_real_backtest_acceptance_reason",
]

REPLAY_TRADE_FIELDS = [
    "trade_spec_id",
    "trader_decision_id",
    "candidate_bundle_id",
    "decision_id",
    "split_id",
    "symbol",
    "side",
    "entry_date",
    "entry_adj_close",
    "exit_date",
    "exit_adj_close",
    "allocated_capital",
    "period_return",
    "diagnostic_pnl",
    "authority",
]

REPLAY_PERIOD_FIELDS = [
    "decision_id",
    "split_id",
    "entry_date",
    "exit_date",
    "active_trade_specs",
    "brain_slice_period_return",
    "brain_slice_equity",
    "qqq_period_return",
    "qqq_equity",
]

SPLIT_SUMMARY_FIELDS = [
    "split_id",
    "period_count",
    "active_period_count",
    "brain_slice_end_equity",
    "qqq_end_equity",
    "brain_slice_split_return_pct_approx",
    "qqq_split_return_pct_approx",
    "authority",
]

SOURCE_ADMISSION_FIELDS = [
    "l1_state_id",
    "evidence_id",
    "symbol",
    "theme",
    "available_to_brain_ts",
    "source_family",
    "raw_external_document_state",
    "attachment_authority",
    "local_attachment_state",
    "admission_state",
    "rejection_reason",
    "can_enter_l2",
]

FRONT_GATE_FIELDS = ["gate", "value", "threshold", "status", "action"]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def stable_hash(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_ts(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def source_event_id(evidence_id: str) -> str:
    prefix = "Task893|"
    return evidence_id[len(prefix):] if evidence_id.startswith(prefix) else evidence_id


def l1_admission_result(row: dict[str, str]) -> tuple[str, str, int]:
    if row["raw_external_document_state"] != "attached":
        return "rejected_for_l2_admission", "raw_external_document_not_attached", 0
    if row["source_family"] == "internal_source_event_capture":
        return "rejected_for_l2_admission", "internal_lifecycle_event_not_raw_external_source", 0
    if row["attachment_authority"] == "LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE":
        return "rejected_for_l2_admission", "local_lineage_only_not_external_source", 0
    return "admitted_to_l2", "", 1


def build_source_admission_audit(l1_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    audit_rows: list[dict[str, object]] = []
    for row in l1_rows:
        state, reason, can_enter = l1_admission_result(row)
        audit_rows.append(
            {
                "l1_state_id": row["l1_state_id"],
                "evidence_id": row["evidence_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "source_family": row["source_family"],
                "raw_external_document_state": row["raw_external_document_state"],
                "attachment_authority": row["attachment_authority"],
                "local_attachment_state": row["local_attachment_state"],
                "admission_state": state,
                "rejection_reason": reason,
                "can_enter_l2": can_enter,
            }
        )
    return audit_rows


def write_empty_brain_outputs(out_dir: Path) -> None:
    write_csv(out_dir / "task897_primitive_fact_seed_panel.csv", [], PRIMITIVE_FIELDS)
    write_csv(out_dir / "task898_economic_meaning_seed_panel.csv", [], MEANING_FIELDS)
    write_csv(out_dir / "task899_relation_snapshot_panel.csv", [], RELATION_FIELDS)
    write_csv(out_dir / "task900_candidate_thesis_packets.csv", [], CANDIDATE_FIELDS)
    write_csv(out_dir / "task901_dry_trader_decisions.csv", [], DRY_DECISION_FIELDS)
    write_csv(out_dir / "task906_diagnostic_trade_specs.csv", [], TRADE_SPEC_FIELDS)
    write_csv(out_dir / "task906_diagnostic_replay_trades.csv", [], REPLAY_TRADE_FIELDS)
    write_csv(out_dir / "task906_diagnostic_replay_periods.csv", [], REPLAY_PERIOD_FIELDS)
    write_csv(out_dir / "task906_split_summary.csv", [], SPLIT_SUMMARY_FIELDS)


def event_type_to_primitive(event_type: str) -> str:
    return {
        "SETUP_DETECTED": "setup_observed",
        "INVALIDATION": "invalidation_observed",
        "PROBE_ENTRY": "probe_observed",
        "ADD_ATTEMPT": "add_attempt_observed",
        "SIZE_INCREASE": "size_increase_observed",
    }.get(event_type, "event_observed")


def primitive_polarity(event_type: str, state_label: str, transition_reason: str) -> str:
    if event_type == "INVALIDATION" or "exit" in transition_reason:
        return "risk_or_invalidation"
    if event_type in {"PROBE_ENTRY", "ADD_ATTEMPT", "SIZE_INCREASE"}:
        return "constructive_continuation"
    if event_type == "SETUP_DETECTED" and state_label in {"NORMAL", "SETUP", "PROBE"}:
        return "constructive_setup"
    if event_type == "SETUP_DETECTED":
        return "setup_with_context_risk"
    return "unknown"


def uncertainty(raw_external_state: str, local_state: str, lineage_quality: str) -> str:
    if raw_external_state != "attached":
        return "high_raw_source_gap"
    if local_state != "local_lineage_bundle_attached":
        return "high_local_lineage_gap"
    if lineage_quality == "source_truth":
        return "medium"
    return "high"


def economic_channel(theme: str, event_type: str, transition_reason: str) -> str:
    if "dislocation" in transition_reason:
        return "market_structure_or_risk_dislocation"
    if "ai_semiconductors" == theme:
        return "ai_compute_capex_supply_chain"
    if "cloud_ai_platforms" == theme:
        return "ai_cloud_demand_and_capex"
    if "ev_autonomy_mobility" == theme:
        return "ev_autonomy_demand_and_regulation"
    if event_type == "INVALIDATION":
        return "thesis_invalidation_or_crowding_risk"
    return "company_specific_information_state"


def meaning_bias(polarity: str) -> str:
    if polarity in {"constructive_continuation", "constructive_setup"}:
        return "constructive_but_provisional"
    if polarity == "setup_with_context_risk":
        return "mixed_watch_only"
    if polarity == "risk_or_invalidation":
        return "risk_or_reduce_context"
    return "unknown_context"


def relation_type(bias: str) -> str:
    if bias == "constructive_but_provisional":
        return "reinforces_constructive_thesis"
    if bias == "mixed_watch_only":
        return "context_requires_confirmation"
    if bias == "risk_or_reduce_context":
        return "contradicts_or_blocks_thesis"
    return "unknown_relation"


def relation_weight(rel_type: str) -> int:
    if rel_type == "reinforces_constructive_thesis":
        return 1
    if rel_type == "contradicts_or_blocks_thesis":
        return -1
    return 0


def read_daily_prices(symbol: str, manifest_by_symbol: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    path = ROOT / manifest_by_symbol[symbol]["path"]
    return rows(path)


def next_price_on_or_after(prices: list[dict[str, str]], date_value: str) -> dict[str, str] | None:
    for row in prices:
        if row["timestamp"] >= date_value:
            return row
    return None


def price_before_or_on(prices: list[dict[str, str]], date_value: str) -> dict[str, str] | None:
    previous = None
    for row in prices:
        if row["timestamp"] > date_value:
            return previous
        previous = row
    return previous


def split_for_date(date_value: str) -> str:
    if date_value <= "2024-12-31":
        return "development_2021_2024"
    if date_value <= "2025-12-31":
        return "oos_2025"
    return "oos_2026q1"


def build_primitive_facts(l1_rows: list[dict[str, str]], ledger_by_evidence: dict[str, dict[str, str]], event_by_id: dict[str, dict[str, str]]) -> list[dict[str, object]]:
    facts: list[dict[str, object]] = []
    for idx, l1 in enumerate(l1_rows, start=1):
        event_id = source_event_id(l1["evidence_id"])
        event = event_by_id[event_id]
        ledger = ledger_by_evidence[l1["evidence_id"]]
        transition = ledger["transition_reason"]
        event_type = event["event_type"]
        primitive_type = event_type_to_primitive(event_type)
        polarity = primitive_polarity(event_type, event["state_label"], transition)
        rule_id = f"primitive_rule_v1::{event_type}::{event['state_label']}::{transition}"
        source_span = (
            f"event_type={event_type};state_label={event['state_label']};"
            f"participation={event['participation_quality_label']};transition={transition}"
        )
        fact_id = f"PF897-{idx:05d}"
        fact_payload = {
            "evidence_id": l1["evidence_id"],
            "source_event_id": event_id,
            "source_span": source_span,
            "rule_id": rule_id,
        }
        facts.append(
            {
                "primitive_fact_id": fact_id,
                "l1_state_id": l1["l1_state_id"],
                "evidence_id": l1["evidence_id"],
                "attachment_bundle_id": l1["attachment_bundle_id"],
                "symbol": l1["symbol"],
                "theme": l1["theme"],
                "available_to_brain_ts": l1["available_to_brain_ts"],
                "as_of_ts": l1["available_to_brain_ts"],
                "source_span_ref": stable_hash(source_span),
                "source_span_excerpt": source_span,
                "primitive_type": primitive_type,
                "primitive_polarity": polarity,
                "deterministic_rule_id": rule_id,
                "reproducibility_hash": stable_hash(fact_payload),
                "uncertainty": uncertainty(l1["raw_external_document_state"], l1["local_attachment_state"], ledger["lineage_quality"]),
                "raw_source_gap_flag": "raw_external_document_missing",
                "acceptance_state": "accepted_provisional_internal_scope",
                "does_not_mean": "economic meaning, relation edge, candidate, trade, score, rank, or strategy acceptance",
            }
        )
    return facts


def build_source_contract(queue_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    contract: list[dict[str, object]] = []
    for row in queue_rows:
        families = row["required_source_families"].split(";")
        for family in families:
            contract.append(
                {
                    "theme": row["theme"],
                    "symbol": row["symbol"],
                    "source_family": family,
                    "source_time_field": "source_time",
                    "publication_time_field": "publish_time",
                    "ingestion_time_field": "ingest_time",
                    "effective_time_field": "effective_time",
                    "revision_policy": "store_each_revision_with_revision_id_and_original_publish_time",
                    "source_priority": "official_or_primary_first_then_reputable_secondary",
                    "minimum_required_fields": row["minimum_required_fields"],
                    "admission_rule": "no_synthetic_rows_no_price_outcome_inference",
                    "gap_policy": "missing_source_is_gap_not_negative",
                }
            )
    return contract


def build_raw_reality(queue_rows: list[dict[str, str]], facts: list[dict[str, object]]) -> list[dict[str, object]]:
    fact_count_by_symbol: dict[str, int] = {}
    for fact in facts:
        fact_count_by_symbol[str(fact["symbol"])] = fact_count_by_symbol.get(str(fact["symbol"]), 0) + 1
    rows_out: list[dict[str, object]] = []
    for row in queue_rows:
        rows_out.append(
            {
                "theme": row["theme"],
                "symbol": row["symbol"],
                "coverage_state": row["coverage_state"],
                "primitive_count_before_raw_source": fact_count_by_symbol.get(row["symbol"], 0),
                "raw_source_uri_attached": "",
                "raw_source_hash_attached": "",
                "raw_source_linkage_state": "missing",
                "primitive_recheck_state": "provisional_internal_scope_only" if fact_count_by_symbol.get(row["symbol"], 0) else "no_primitive_seed",
                "blocks_task898_non_provisional": int(fact_count_by_symbol.get(row["symbol"], 0) > 0),
                "does_not_mean": "negative evidence, source absence as bearish signal, or strategy rejection",
            }
        )
    return rows_out


def build_meanings(facts: list[dict[str, object]], raw_reality_by_symbol: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    meanings: list[dict[str, object]] = []
    for idx, fact in enumerate(facts, start=1):
        raw_state = raw_reality_by_symbol[str(fact["symbol"])]["raw_source_linkage_state"]
        channel = economic_channel(str(fact["theme"]), str(fact["primitive_type"]), str(fact["source_span_excerpt"]))
        bias = meaning_bias(str(fact["primitive_polarity"]))
        meanings.append(
            {
                "economic_meaning_id": f"EM898-{idx:05d}",
                "primitive_fact_id": fact["primitive_fact_id"],
                "evidence_id": fact["evidence_id"],
                "symbol": fact["symbol"],
                "theme": fact["theme"],
                "as_of_ts": fact["as_of_ts"],
                "economic_channel": channel,
                "meaning_bias": bias,
                "uncertainty": fact["uncertainty"],
                "raw_source_gap_flag": fact["raw_source_gap_flag"],
                "raw_source_linkage_state": raw_state,
                "meaning_authority": "provisional_internal_scope_only",
                "confidence_cap": "low_until_raw_external_source_attached" if raw_state == "missing" else "medium",
                "does_not_mean": "buy, sell, position sizing, score, rank, or backtest acceptance",
            }
        )
    return meanings


def build_relation_snapshots(meanings: list[dict[str, object]], decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    meanings_by_symbol: dict[str, list[dict[str, object]]] = {}
    for meaning in meanings:
        meanings_by_symbol.setdefault(str(meaning["symbol"]), []).append(meaning)
    relations: list[dict[str, object]] = []
    idx = 1
    for decision in decisions:
        decision_ts = parse_ts(decision["decision_asof_ts"])
        for symbol, symbol_meanings in sorted(meanings_by_symbol.items()):
            available = [m for m in symbol_meanings if parse_ts(str(m["as_of_ts"])) <= decision_ts]
            if not available:
                continue
            counts = {"reinforces_constructive_thesis": 0, "context_requires_confirmation": 0, "contradicts_or_blocks_thesis": 0}
            meaning_ids: list[str] = []
            for meaning in available:
                rel = relation_type(str(meaning["meaning_bias"]))
                if rel in counts:
                    counts[rel] += 1
                meaning_ids.append(str(meaning["economic_meaning_id"]))
            net = counts["reinforces_constructive_thesis"] - counts["contradicts_or_blocks_thesis"]
            if net > 0:
                relation_state = "provisional_constructive"
            elif net < 0:
                relation_state = "provisional_risk_blocked"
            else:
                relation_state = "provisional_mixed_watch"
            relations.append(
                {
                    "relation_snapshot_id": f"RS899-{idx:05d}",
                    "decision_id": decision["decision_id"],
                    "decision_asof_ts": decision["decision_asof_ts"],
                    "split_id": decision["split_id"],
                    "symbol": symbol,
                    "theme": available[-1]["theme"],
                    "available_meaning_count": len(available),
                    "constructive_count": counts["reinforces_constructive_thesis"],
                    "confirmation_count": counts["context_requires_confirmation"],
                    "risk_blocker_count": counts["contradicts_or_blocks_thesis"],
                    "net_relation_balance": net,
                    "relation_state": relation_state,
                    "relation_authority": "provisional_below_raw_source_linkage_threshold",
                    "source_meaning_ids": ";".join(meaning_ids[-20:]),
                    "edge_asof_ts": decision["decision_asof_ts"],
                    "does_not_mean": "candidate approval, trade instruction, score, rank, or accepted graph",
                }
            )
            idx += 1
    return relations


def build_candidate_packets(relations: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for idx, rel in enumerate(relations, start=1):
        state = str(rel["relation_state"])
        if state == "provisional_constructive":
            thesis = "review_only_constructive_continuation_thesis"
        elif state == "provisional_mixed_watch":
            thesis = "review_only_watch_for_confirmation"
        else:
            thesis = "review_only_risk_or_invalidation_packet"
        candidates.append(
            {
                "candidate_bundle_id": f"CB900-{idx:05d}",
                "relation_snapshot_id": rel["relation_snapshot_id"],
                "decision_id": rel["decision_id"],
                "decision_asof_ts": rel["decision_asof_ts"],
                "split_id": rel["split_id"],
                "symbol": rel["symbol"],
                "theme": rel["theme"],
                "candidate_thesis_type": thesis,
                "available_meaning_count": rel["available_meaning_count"],
                "net_relation_balance": rel["net_relation_balance"],
                "raw_source_gap_flag": "raw_external_document_missing",
                "candidate_authority": "review_only_provisional",
                "adapter_eligible": 0,
                "does_not_mean": "side, entry, exit, position_size, trade spec, score, rank, or strategy acceptance",
            }
        )
    return candidates


def build_dry_decisions(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    decisions: list[dict[str, object]] = []
    for idx, candidate in enumerate(candidates, start=1):
        balance = int(candidate["net_relation_balance"])
        if candidate["candidate_thesis_type"] == "review_only_constructive_continuation_thesis" and balance >= 2:
            action = "review_only_activate_candidate"
        elif candidate["candidate_thesis_type"] == "review_only_constructive_continuation_thesis":
            action = "watch"
        elif candidate["candidate_thesis_type"] == "review_only_watch_for_confirmation":
            action = "watch"
        else:
            action = "skip_or_reduce_review"
        decisions.append(
            {
                "trader_decision_id": f"TD901-{idx:05d}",
                "candidate_bundle_id": candidate["candidate_bundle_id"],
                "decision_id": candidate["decision_id"],
                "decision_asof_ts": candidate["decision_asof_ts"],
                "split_id": candidate["split_id"],
                "symbol": candidate["symbol"],
                "theme": candidate["theme"],
                "decision_state": action,
                "decision_reason": candidate["candidate_thesis_type"],
                "raw_source_gap_flag": candidate["raw_source_gap_flag"],
                "decision_authority": "dry_review_only_provisional",
                "trade_spec_allowed": 0,
                "diagnostic_replay_allowed": 1 if action == "review_only_activate_candidate" else 0,
                "does_not_mean": "real trade, broker instruction, strategy acceptance, or real capital permission",
            }
        )
    return decisions


def build_diagnostic_trade_specs(decisions: list[dict[str, object]], decision_calendar: list[dict[str, str]]) -> list[dict[str, object]]:
    next_date_by_decision = {row["decision_id"]: row["entry_not_before_ts"] for row in decision_calendar}
    specs: list[dict[str, object]] = []
    for idx, decision in enumerate((d for d in decisions if int(d["diagnostic_replay_allowed"]) == 1), start=1):
        entry_date = next_date_by_decision[str(decision["decision_id"])]
        specs.append(
            {
                "trade_spec_id": f"TS906-{idx:05d}",
                "trader_decision_id": decision["trader_decision_id"],
                "candidate_bundle_id": decision["candidate_bundle_id"],
                "decision_id": decision["decision_id"],
                "decision_asof_ts": decision["decision_asof_ts"],
                "split_id": decision["split_id"],
                "symbol": decision["symbol"],
                "side": "long",
                "tradable_after_date": entry_date,
                "exit_policy": "hold_until_next_monthly_decision_or_2026_03_31",
                "allocation_policy": "equal_weight_active_diagnostic_slice",
                "trade_spec_authority": "DIAGNOSTIC_PROVISIONAL_BRAIN_SLICE_ONLY",
                "blocked_for_real_backtest_acceptance_reason": "raw_external_source_missing_and_review_only_decision",
            }
        )
    return specs


def run_replay(specs: list[dict[str, object]], decisions: list[dict[str, str]], manifest_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    manifest_by_symbol = {row["symbol"]: row for row in manifest_rows}
    price_cache: dict[str, list[dict[str, str]]] = {}

    def prices(symbol: str) -> list[dict[str, str]]:
        if symbol not in price_cache:
            price_cache[symbol] = read_daily_prices(symbol, manifest_by_symbol)
        return price_cache[symbol]

    decision_by_id = {row["decision_id"]: row for row in decisions}
    specs_by_decision: dict[str, list[dict[str, object]]] = {}
    for spec in specs:
        specs_by_decision.setdefault(str(spec["decision_id"]), []).append(spec)

    equity = INITIAL_CAPITAL
    qqq_equity = INITIAL_CAPITAL
    replay_rows: list[dict[str, object]] = []
    period_rows: list[dict[str, object]] = []
    qqq_prices = prices(BENCHMARK)
    for decision in decisions:
        if decision["session_date"] > "2026-03-31":
            continue
        active = specs_by_decision.get(decision["decision_id"], [])
        entry_date = decision["entry_not_before_ts"]
        if not entry_date or entry_date > "2026-03-31":
            continue
        exit_date = "2026-03-31"
        next_decision_idx = next((i for i, row in enumerate(decisions) if row["decision_id"] == decision["decision_id"]), None)
        if next_decision_idx is not None and next_decision_idx + 2 < len(decisions):
            exit_date = min("2026-03-31", decisions[next_decision_idx + 2]["session_date"])
        q_entry = next_price_on_or_after(qqq_prices, entry_date)
        q_exit = price_before_or_on(qqq_prices, exit_date)
        q_return = 0.0
        if q_entry and q_exit:
            q_return = float(q_exit["adj_close"]) / float(q_entry["adj_close"]) - 1.0
            qqq_equity *= 1.0 + q_return
        period_return = 0.0
        if active:
            symbol_returns: list[float] = []
            allocation = equity / len(active)
            for spec in active:
                sym_prices = prices(str(spec["symbol"]))
                entry = next_price_on_or_after(sym_prices, entry_date)
                exit_row = price_before_or_on(sym_prices, exit_date)
                if not entry or not exit_row:
                    continue
                ret = float(exit_row["adj_close"]) / float(entry["adj_close"]) - 1.0
                symbol_returns.append(ret)
                replay_rows.append(
                    {
                        "trade_spec_id": spec["trade_spec_id"],
                        "trader_decision_id": spec["trader_decision_id"],
                        "candidate_bundle_id": spec["candidate_bundle_id"],
                        "decision_id": spec["decision_id"],
                        "split_id": spec["split_id"],
                        "symbol": spec["symbol"],
                        "side": spec["side"],
                        "entry_date": entry["timestamp"],
                        "entry_adj_close": entry["adj_close"],
                        "exit_date": exit_row["timestamp"],
                        "exit_adj_close": exit_row["adj_close"],
                        "allocated_capital": round(allocation, 6),
                        "period_return": round(ret, 8),
                        "diagnostic_pnl": round(allocation * ret, 6),
                        "authority": "DIAGNOSTIC_PROVISIONAL_BRAIN_SLICE_ONLY",
                    }
                )
            if symbol_returns:
                period_return = sum(symbol_returns) / len(symbol_returns)
                equity *= 1.0 + period_return
        period_rows.append(
            {
                "decision_id": decision["decision_id"],
                "split_id": decision["split_id"],
                "entry_date": entry_date,
                "exit_date": exit_date,
                "active_trade_specs": len(active),
                "brain_slice_period_return": round(period_return, 8),
                "brain_slice_equity": round(equity, 6),
                "qqq_period_return": round(q_return, 8),
                "qqq_equity": round(qqq_equity, 6),
            }
        )
    summary = {
        "initial_capital": INITIAL_CAPITAL,
        "final_brain_slice_equity": round(equity, 6),
        "final_qqq_equity": round(qqq_equity, 6),
        "brain_slice_total_return_pct": round((equity / INITIAL_CAPITAL - 1.0) * 100.0, 4),
        "qqq_total_return_pct": round((qqq_equity / INITIAL_CAPITAL - 1.0) * 100.0, 4),
        "executed_diagnostic_trade_rows": len(replay_rows),
        "active_periods": sum(1 for row in period_rows if int(row["active_trade_specs"]) > 0),
    }
    return replay_rows, period_rows, summary


def summarize_by_split(period_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in period_rows:
        grouped.setdefault(str(row["split_id"]), []).append(row)
    out: list[dict[str, object]] = []
    for split_id, items in grouped.items():
        active = [row for row in items if int(row["active_trade_specs"]) > 0]
        start_brain = INITIAL_CAPITAL if split_id == "development_2021_2024" else float(items[0]["brain_slice_equity"])
        end_brain = float(items[-1]["brain_slice_equity"])
        start_qqq = INITIAL_CAPITAL if split_id == "development_2021_2024" else float(items[0]["qqq_equity"])
        end_qqq = float(items[-1]["qqq_equity"])
        out.append(
            {
                "split_id": split_id,
                "period_count": len(items),
                "active_period_count": len(active),
                "brain_slice_end_equity": round(end_brain, 6),
                "qqq_end_equity": round(end_qqq, 6),
                "brain_slice_split_return_pct_approx": round((end_brain / start_brain - 1.0) * 100.0, 4) if start_brain else 0,
                "qqq_split_return_pct_approx": round((end_qqq / start_qqq - 1.0) * 100.0, 4) if start_qqq else 0,
                "authority": "DIAGNOSTIC_SPLIT_SUMMARY_ONLY",
            }
        )
    return out


def run(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    l1_rows_all = rows(L1_ENRICHED)
    l1_rows = [row for row in l1_rows_all if row["in_10x7_universe"] == "1"]
    ledger_rows = rows(ATTACHMENT_LEDGER)
    queue_rows = rows(SOURCE_QUEUE)
    event_rows = rows(EVENT_DATASET)
    decisions = rows(DECISION_CALENDAR)
    manifest_rows = rows(DAILY_MANIFEST)
    ledger_by_evidence = {row["evidence_id"]: row for row in ledger_rows}
    event_by_id = {row["source_event_id"]: row for row in event_rows}

    admission_audit = build_source_admission_audit(l1_rows)
    admitted_l1_rows = [
        row
        for row in l1_rows
        if l1_admission_result(row)[2] == 1
    ]
    source_contract = build_source_contract(queue_rows)
    raw_reality = build_raw_reality(queue_rows, [])
    front_gate_rows = [
        {
            "gate": "raw_external_source_attached_for_l2",
            "value": len(admitted_l1_rows),
            "threshold": ">=1 admitted row and 95pct linkage for non-provisional graph",
            "status": "pass" if admitted_l1_rows else "fail",
            "action": "allow_l2_builder" if admitted_l1_rows else "block_l2_l3_l4_l5_and_replay",
        },
        {
            "gate": "internal_lifecycle_event_not_source_truth",
            "value": sum(1 for row in admission_audit if row["source_family"] == "internal_source_event_capture"),
            "threshold": "0 internal lifecycle rows admitted",
            "status": "pass",
            "action": "treat_as_lineage_context_only",
        },
        {
            "gate": "previous_replay_result_validity",
            "value": "1282.788864_vs_1847.026842_prior_output",
            "threshold": "valid_l1_l2_source_admission",
            "status": "invalidated",
            "action": "do_not_use_prior_replay_as_brain_strategy_evidence",
        },
    ]
    write_csv(out_dir / "task897_source_admission_audit.csv", admission_audit, SOURCE_ADMISSION_FIELDS)
    write_csv(out_dir / "task897_906_front_gate_status.csv", front_gate_rows, FRONT_GATE_FIELDS)
    write_csv(out_dir / "task902_source_time_provider_contract.csv", source_contract, SOURCE_CONTRACT_FIELDS)
    write_csv(out_dir / "task903_raw_source_reality_check.csv", raw_reality, RAW_REALITY_FIELDS)

    if not admitted_l1_rows:
        write_empty_brain_outputs(out_dir)
        stop_gate_rows = [
            {
                "gate": "source_admission_for_l2",
                "value": 0,
                "threshold": ">=1 raw external source-attached L1 row",
                "status": "fail_front_gate_no_go",
            },
            {
                "gate": "raw_source_linkage_at_least_95pct_for_non_provisional_graph",
                "value": 0.0,
                "threshold": MIN_RAW_LINKAGE_FOR_NON_PROVISIONAL_GRAPH,
                "status": "fail_no_go",
            },
            {
                "gate": "diagnostic_replay_allowed",
                "value": 0,
                "threshold": "l2_l3_l4_l5_nonempty_after_source_admission",
                "status": "not_run_front_gate_no_go",
            },
            {
                "gate": "real_strategy_acceptance",
                "value": "NOT_ACCEPTED",
                "threshold": "acceptance_contract",
                "status": "not_accepted",
            },
        ]
        write_csv(out_dir / "task897_906_stop_gate_status.csv", stop_gate_rows, ["gate", "value", "threshold", "status"])
        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task_id": "Task897-906",
            "authority": "FRONT_GATE_NO_GO_SOURCE_ADMISSION_ONLY",
            "front_gate_status": "no_go_missing_raw_external_source",
            "l1_seed_rows_considered": len(l1_rows),
            "l1_seed_rows": len(l1_rows),
            "l2_admitted_seed_rows": 0,
            "l2_rejected_seed_rows": len(admission_audit),
            "primitive_fact_rows": 0,
            "primitive_acceptance_rate": 0.0,
            "source_contract_rows": len(source_contract),
            "raw_source_linkage_rate": 0.0,
            "economic_meaning_rows": 0,
            "relation_snapshot_rows": 0,
            "candidate_packet_rows": 0,
            "dry_decision_rows": 0,
            "diagnostic_trade_spec_rows": 0,
            "initial_capital": INITIAL_CAPITAL,
            "final_brain_slice_equity": INITIAL_CAPITAL,
            "final_qqq_equity": INITIAL_CAPITAL,
            "brain_slice_total_return_pct": 0.0,
            "qqq_total_return_pct": 0.0,
            "executed_diagnostic_trade_rows": 0,
            "active_periods": 0,
            "replay_status": "not_run_front_gate_no_go",
            "invalidated_previous_replay_result": True,
            "previous_replay_invalid_reason": "internal_lifecycle_events_were_not_admissible_raw_source_evidence",
            "result_interpretation": "upstream source admission failed; no valid brain-slice backtest result",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
        (out_dir / "task897_906_vertical_slice_backtest_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
        return summary

    primitive_facts = build_primitive_facts(admitted_l1_rows, ledger_by_evidence, event_by_id)
    source_contract = build_source_contract(queue_rows)
    raw_reality = build_raw_reality(queue_rows, primitive_facts)
    raw_reality_by_symbol = {str(row["symbol"]): row for row in raw_reality}
    meanings = build_meanings(primitive_facts, raw_reality_by_symbol)
    relations = build_relation_snapshots(meanings, decisions)
    candidates = build_candidate_packets(relations)
    dry_decisions = build_dry_decisions(candidates)
    trade_specs = build_diagnostic_trade_specs(dry_decisions, decisions)
    replay_trades, replay_periods, replay_summary = run_replay(trade_specs, decisions, manifest_rows)
    split_summary = summarize_by_split(replay_periods)

    primitive_acceptance = sum(1 for row in primitive_facts if row["acceptance_state"] == "accepted_provisional_internal_scope") / len(primitive_facts)
    raw_linkage = sum(1 for row in raw_reality if row["raw_source_linkage_state"] == "attached") / len(raw_reality)
    stop_gate_rows = [
        {"gate": "primitive_acceptance_at_least_80pct", "value": round(primitive_acceptance, 4), "threshold": MIN_ACCEPTANCE, "status": "pass" if primitive_acceptance >= MIN_ACCEPTANCE else "fail"},
        {"gate": "raw_source_linkage_at_least_95pct_for_non_provisional_graph", "value": round(raw_linkage, 4), "threshold": MIN_RAW_LINKAGE_FOR_NON_PROVISIONAL_GRAPH, "status": "fail_provisional_only"},
        {"gate": "uncertainty_propagation_present", "value": len({row["uncertainty"] for row in meanings}), "threshold": 1, "status": "pass"},
        {"gate": "real_strategy_acceptance", "value": "NOT_ACCEPTED", "threshold": "acceptance_contract", "status": "not_accepted"},
    ]

    write_csv(out_dir / "task897_primitive_fact_seed_panel.csv", primitive_facts, PRIMITIVE_FIELDS)
    write_csv(out_dir / "task902_source_time_provider_contract.csv", source_contract, SOURCE_CONTRACT_FIELDS)
    write_csv(out_dir / "task903_raw_source_reality_check.csv", raw_reality, RAW_REALITY_FIELDS)
    write_csv(out_dir / "task898_economic_meaning_seed_panel.csv", meanings, MEANING_FIELDS)
    write_csv(out_dir / "task899_relation_snapshot_panel.csv", relations, RELATION_FIELDS)
    write_csv(out_dir / "task900_candidate_thesis_packets.csv", candidates, CANDIDATE_FIELDS)
    write_csv(out_dir / "task901_dry_trader_decisions.csv", dry_decisions, DRY_DECISION_FIELDS)
    write_csv(out_dir / "task906_diagnostic_trade_specs.csv", trade_specs, TRADE_SPEC_FIELDS)
    write_csv(out_dir / "task906_diagnostic_replay_trades.csv", replay_trades, REPLAY_TRADE_FIELDS)
    write_csv(out_dir / "task906_diagnostic_replay_periods.csv", replay_periods, REPLAY_PERIOD_FIELDS)
    write_csv(out_dir / "task906_split_summary.csv", split_summary, SPLIT_SUMMARY_FIELDS)
    write_csv(out_dir / "task897_906_stop_gate_status.csv", stop_gate_rows, ["gate", "value", "threshold", "status"])

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": "Task897-906",
        "authority": "DIAGNOSTIC_PROVISIONAL_BRAIN_SLICE_ONLY",
        "l1_seed_rows": len(l1_rows),
        "primitive_fact_rows": len(primitive_facts),
        "primitive_acceptance_rate": round(primitive_acceptance, 4),
        "source_contract_rows": len(source_contract),
        "raw_source_linkage_rate": round(raw_linkage, 4),
        "economic_meaning_rows": len(meanings),
        "relation_snapshot_rows": len(relations),
        "candidate_packet_rows": len(candidates),
        "dry_decision_rows": len(dry_decisions),
        "diagnostic_trade_spec_rows": len(trade_specs),
        **replay_summary,
        "result_interpretation": "diagnostic provisional brain-slice replay, not accepted strategy",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "task897_906_vertical_slice_backtest_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    summary = run(args.out_dir)
    print(
        "[TRADER_BRAIN_897_906_VERTICAL_SLICE_BACKTEST_OK] "
        f"primitive={summary['primitive_fact_rows']} meanings={summary['economic_meaning_rows']} "
        f"relations={summary['relation_snapshot_rows']} candidates={summary['candidate_packet_rows']} "
        f"trades={summary['executed_diagnostic_trade_rows']} "
        f"brain={summary['final_brain_slice_equity']} qqq={summary['final_qqq_equity']}"
    )


if __name__ == "__main__":
    main()
