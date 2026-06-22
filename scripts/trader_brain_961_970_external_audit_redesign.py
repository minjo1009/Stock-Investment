from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREV_DIR = ROOT / "data/artifacts/task_941_950_slot_capped_selection_replay"
LAYER_DIR = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"
OUT_DIR = ROOT / "data/artifacts/task_961_970_external_audit_redesign"

FEATURE_PATH = PREV_DIR / "task941_selection_feature_panel.csv"
BASELINE_TRADES_PATH = PREV_DIR / "task943_slot_capped_replay_trades.csv"
BASELINE_SUMMARY_PATH = PREV_DIR / "task946_slot_capped_summary.csv"
L1_PATH = LAYER_DIR / "task917_multifamily_l1_evidence.csv"
CANDIDATE_PATH = LAYER_DIR / "task919_l4_candidate_bundles_contradiction.csv"
RELATION_PATH = LAYER_DIR / "task919_relation_edges_9primitive.csv"

AUTHORITY = "REVIEW_ONLY_EXTERNAL_AUDIT_REDESIGN"
ALLOWED_HARD_BLOCK_REASONS = {
    "future_evidence",
    "missing_required_lineage",
    "source_backed_invalidation",
}
FORBIDDEN_OUTCOME_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank"
STANDALONE_NON_BLOCK_FLAGS = {
    "source_gap_heavy",
    "stale_source",
    "duplicate_thesis",
    "thin_packet",
    "low_independent_evidence",
}
STRUCTURAL_THEMES = {
    "aerospace_defense_space",
    "ai_semiconductors",
    "cloud_ai_platforms",
    "cybersecurity",
    "industrial_automation_robotics",
    "power_grid_electrification",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ids(value: str) -> list[str]:
    return [item for item in str(value).split(";") if item]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def days_between(start_ts: str, end_ts: str) -> int:
    return max((parse_ts(end_ts) - parse_ts(start_ts)).days, 0)


def supporting_context(
    feature: dict[str, str],
    candidates: dict[str, dict[str, str]],
    evidences: dict[str, dict[str, str]],
    relations: dict[str, dict[str, str]],
) -> dict[str, object]:
    candidate = candidates[feature["candidate_bundle_id"]]
    supporting_evidence_ids = ids(candidate["supporting_evidence_ids"])
    evidence_rows = [evidences[eid] for eid in supporting_evidence_ids if eid in evidences]
    family_set = sorted({row["source_family"] for row in evidence_rows})
    source_hashes = sorted({row["raw_source_hash"] for row in evidence_rows})
    source_names = sorted({row["source_name"] for row in evidence_rows})
    available_dates = [row["available_to_brain_ts"] for row in evidence_rows]
    newest_available = max(available_dates) if available_dates else ""
    oldest_available = min(available_dates) if available_dates else ""
    newest_age = days_between(newest_available, feature["decision_asof_ts"]) if newest_available else 99999
    oldest_age = days_between(oldest_available, feature["decision_asof_ts"]) if oldest_available else 99999
    leakage_state = (
        "pass"
        if not newest_available or parse_ts(newest_available) <= parse_ts(feature["decision_asof_ts"])
        else "future_evidence"
    )
    relation_ids = (
        ids(candidate["supporting_relation_ids"])
        + ids(candidate["contradicting_relation_ids"])
        + ids(candidate["invalidation_relation_ids"])
        + ids(candidate["source_gap_relation_ids"])
    )
    primitive_set = sorted({relations[rid]["relation_primitive"] for rid in relation_ids if rid in relations})
    cluster_key = "|".join(
        [
            feature["theme"],
            feature["symbol"],
            candidate["candidate_thesis_type"],
            "+".join(family_set),
            "+".join(primitive_set),
        ]
    )
    return {
        "candidate": candidate,
        "family_set": family_set,
        "source_hashes": source_hashes,
        "source_names": source_names,
        "newest_available_to_brain_ts": newest_available,
        "oldest_available_to_brain_ts": oldest_available,
        "newest_source_age_days": newest_age,
        "oldest_source_age_days": oldest_age,
        "leakage_state": leakage_state,
        "primitive_set": primitive_set,
        "cluster_key": cluster_key,
        "supporting_evidence_count": len(evidence_rows),
        "independent_evidence_family_count": len(family_set),
        "independent_raw_hash_count": len(source_hashes),
        "independent_source_name_count": len(source_names),
    }


def weakness_flags(feature: dict[str, str], context: dict[str, object], prior_duplicate_count: int) -> list[str]:
    flags: list[str] = []
    candidate = context["candidate"]
    if candidate["candidate_thesis_type"] == "thin_or_gap_context_packet":
        flags.append("thin_packet")
    if int(feature["unresolved_source_gap_count"]) >= 2:
        flags.append("source_gap_heavy")
    if int(context["independent_evidence_family_count"]) < 2:
        flags.append("low_independent_evidence")
    if int(context["newest_source_age_days"]) > 540:
        flags.append("stale_source")
    if prior_duplicate_count > 0:
        flags.append("duplicate_thesis")
    return flags


def semantic_class(flag: str, feature: dict[str, str]) -> str:
    if flag == "source_gap_heavy":
        return "data_limitation"
    if flag == "duplicate_thesis":
        return "conviction_repeat" if feature["theme"] in STRUCTURAL_THEMES else "unknown"
    if flag == "stale_source":
        return "structural_thesis" if feature["theme"] in STRUCTURAL_THEMES else "timing_issue"
    if flag in {"thin_packet", "low_independent_evidence"}:
        return "data_limitation"
    return "unknown"


def duplicate_meaning(feature: dict[str, str], context: dict[str, object], prior_count: int) -> str:
    if prior_count == 0:
        return "first_observation"
    candidate = context["candidate"]
    has_contradiction = candidate["contradiction_state"] != "no_direct_contradiction"
    if feature["theme"] in STRUCTURAL_THEMES and not has_contradiction and int(feature["positive_relation_count"]) > 0:
        return "conviction_repeat"
    if prior_count >= 5 and has_contradiction:
        return "crowding_risk"
    if int(feature["positive_relation_count"]) == 0:
        return "redundant_same_trade"
    return "unknown"


def source_gap_materiality(feature: dict[str, str]) -> str:
    count = int(feature["unresolved_source_gap_count"])
    if count >= 3:
        return "high"
    if count >= 1:
        return "medium"
    return "none"


def duration_class(feature: dict[str, str], context: dict[str, object]) -> str:
    age = int(context["newest_source_age_days"])
    families = set(context["family_set"])
    catalyst_like = bool(families & {"earnings_guidance", "macro_policy_official", "sector_specialist_official_docs"})
    if catalyst_like and age > 540:
        return "expired_catalyst"
    if catalyst_like and age > 270:
        return "aging_catalyst_needs_refresh"
    if feature["theme"] in STRUCTURAL_THEMES and age > 540:
        return "long_duration_structural_thesis"
    if age <= 540:
        return "evergreen_quality"
    return "unknown"


def expert_lens(feature: dict[str, str]) -> tuple[str, str, str]:
    theme = feature["theme"]
    mapping = {
        "aerospace_defense_space": ("space_defense", "defense_budget_policy_and_launch_cadence", "timing"),
        "ai_semiconductors": ("semiconductor_ai", "capex_cycle_export_control_and_supply_chain", "timing"),
        "cloud_ai_platforms": ("ai_infrastructure", "hyperscaler_capex_and_ai_platform_adoption", "timing"),
        "cybersecurity": ("software_security", "enterprise_security_budget_and_regulatory_pressure", "confidence"),
        "data_devops_software": ("software", "developer_tool_spend_and_cloud_optimization", "confidence"),
        "power_grid_electrification": ("energy_power", "power_demand_grid_bottleneck_and_policy_support", "timing"),
        "ev_autonomy_mobility": ("mobility_policy", "rates_subsidy_and_autonomy_adoption", "timing"),
        "biotech_glp1_healthcare": ("healthcare_policy", "clinical_regulatory_and_reimbursement_timing", "timing"),
        "crypto_fintech": ("macro_regulatory", "liquidity_rates_and_crypto_regulation", "direction_and_timing"),
        "industrial_automation_robotics": ("industrial_economy", "capex_cycle_labor_shortage_and_automation", "timing"),
    }
    return mapping.get(theme, ("generalist", "unknown_macro_theme_condition", "unknown"))


def action_from_row(
    feature: dict[str, str],
    context: dict[str, object],
    flags: list[str],
    duplicate_class: str,
    thesis_duration: str,
) -> tuple[str, str]:
    candidate = context["candidate"]
    if context["leakage_state"] == "future_evidence":
        return "hard_block", "future_evidence"
    if not feature["trade_spec_id"] or not feature["candidate_bundle_id"] or not feature["adapter_input_id"]:
        return "hard_block", "missing_required_lineage"
    if candidate["invalidation_relation_ids"]:
        return "hard_block", "source_backed_invalidation"
    if thesis_duration in {"expired_catalyst", "aging_catalyst_needs_refresh"}:
        return "wait", "catalyst_refresh_needed"
    if duplicate_class == "crowding_risk":
        return "reduce_priority", "duplicate_crowding_risk_review"
    if duplicate_class == "redundant_same_trade":
        return "substitute", "redundant_same_trade_review"
    if duplicate_class == "conviction_repeat" and thesis_duration == "long_duration_structural_thesis":
        return "enter", "structural_conviction_repeat_with_source_limitation_review"
    if "source_gap_heavy" in flags or "thin_packet" in flags:
        return "monitor", "source_limitation_review"
    if duplicate_class == "conviction_repeat" or thesis_duration == "long_duration_structural_thesis":
        return "enter", "structural_or_repeated_conviction_review"
    return "monitor", "needs_trader_review"


def shadow_rank_score(
    feature: dict[str, str],
    context: dict[str, object],
    duplicate_class: str,
    thesis_duration: str,
    action: str,
) -> int:
    score = int(feature["thesis_priority"]) + int(feature["positive_relation_count"])
    score += int(context["independent_evidence_family_count"])
    if duplicate_class == "conviction_repeat":
        score += 2
    if thesis_duration == "long_duration_structural_thesis":
        score += 2
    if thesis_duration == "evergreen_quality":
        score += 1
    if action == "wait":
        score -= 2
    if action == "substitute":
        score -= 1
    if int(feature["unresolved_source_gap_count"]) >= 3:
        score -= 1
    return score


def build() -> dict[str, object]:
    features = read_csv(FEATURE_PATH)
    candidates = {row["candidate_bundle_id"]: row for row in read_csv(CANDIDATE_PATH)}
    evidences = {row["evidence_id"]: row for row in read_csv(L1_PATH)}
    relations = {row["relation_edge_id"]: row for row in read_csv(RELATION_PATH)}
    baseline_trades = [
        row for row in read_csv(BASELINE_TRADES_PATH)
        if row["slot_cap"] == "10"
    ]
    baseline_by_id = {row["trade_spec_id"]: row for row in baseline_trades}
    baseline_summary = next(row for row in read_csv(BASELINE_SUMMARY_PATH) if row["slot_cap"] == "10")

    sorted_features = sorted(features, key=lambda row: (row["decision_asof_ts"], row["entry_date"], row["trade_spec_id"]))
    prior_cluster_counts: dict[str, int] = defaultdict(int)
    context_by_id: dict[str, dict[str, object]] = {}
    flags_by_id: dict[str, list[str]] = {}
    duplicate_by_id: dict[str, int] = {}

    for feature in sorted_features:
        context = supporting_context(feature, candidates, evidences, relations)
        cluster_key = str(context["cluster_key"])
        prior_count = prior_cluster_counts[cluster_key]
        duplicate_by_id[feature["trade_spec_id"]] = prior_count
        context_by_id[feature["trade_spec_id"]] = context
        flags_by_id[feature["trade_spec_id"]] = weakness_flags(feature, context, prior_count)
        prior_cluster_counts[cluster_key] += 1

    task961_rows = []
    task962_rows = []
    task963_rows = []
    task964_rows = []
    task965_rows = []
    task966_rows = []
    task967_rows = []
    task968_reason_rows = []
    task969_rows = []

    feature_by_id = {row["trade_spec_id"]: row for row in sorted_features}
    for feature in sorted_features:
        trade_spec_id = feature["trade_spec_id"]
        context = context_by_id[trade_spec_id]
        flags = flags_by_id[trade_spec_id]
        prior_count = duplicate_by_id[trade_spec_id]
        dup_meaning = duplicate_meaning(feature, context, prior_count)
        thesis_duration = duration_class(feature, context)
        action, action_reason = action_from_row(feature, context, flags, dup_meaning, thesis_duration)
        score = shadow_rank_score(feature, context, dup_meaning, thesis_duration, action)
        lens_owner, policy_condition, effect_type = expert_lens(feature)
        materiality = source_gap_materiality(feature)
        candidate = context["candidate"]

        for flag in flags or ["no_weakness_flag"]:
            meaning = semantic_class(flag, feature) if flag != "no_weakness_flag" else "unknown"
            task962_rows.append(
                {
                    "trade_spec_id": trade_spec_id,
                    "decision_asof_ts": feature["decision_asof_ts"],
                    "entry_date": feature["entry_date"],
                    "symbol": feature["symbol"],
                    "theme": feature["theme"],
                    "weakness_flag": flag,
                    "weakness_semantic_class": meaning,
                    "use_mode": "diagnostic_only",
                    "standalone_hard_block_allowed": "0",
                    "external_audit_question": "is_this_flag_risk_data_limitation_structural_conviction_timing_or_unknown",
                    "does_not_use": FORBIDDEN_OUTCOME_INPUTS,
                    "authority": AUTHORITY,
                }
            )

        task963_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "decision_asof_ts": feature["decision_asof_ts"],
                "entry_date": feature["entry_date"],
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "thesis_cluster_key": context["cluster_key"],
                "prior_duplicate_count": prior_count,
                "duplicate_meaning": dup_meaning,
                "prior_only_sort_key": f"{feature['decision_asof_ts']}|{feature['entry_date']}|{trade_spec_id}",
                "standalone_hard_block_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        task964_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "source_gap_reason": candidate["unresolved_source_gaps"],
                "source_gap_materiality": materiality,
                "required_missing_artifact": candidate["unresolved_source_gaps"],
                "blocks_confidence": "1" if materiality in {"medium", "high"} else "0",
                "blocks_trade": "0",
                "standalone_hard_block_allowed": "0",
                "authority": AUTHORITY,
            }
        )
        task965_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "newest_available_to_brain_ts": context["newest_available_to_brain_ts"],
                "newest_source_age_days": context["newest_source_age_days"],
                "thesis_duration_class": thesis_duration,
                "stale_is_standalone_hard_block": "0",
                "authority": AUTHORITY,
            }
        )
        task966_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "expert_lens_owner": lens_owner,
                "policy_macro_condition": policy_condition,
                "timing_effect": effect_type,
                "direction_effect": "not_direct_buy_sell",
                "source_required_for_confidence": candidate["unresolved_source_gaps"],
                "authority": AUTHORITY,
            }
        )
        task967_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "decision_asof_ts": feature["decision_asof_ts"],
                "entry_date": feature["entry_date"],
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "trader_action": action,
                "action_reason": action_reason,
                "hard_block_reason": action_reason if action == "hard_block" else "",
                "allowed_hard_block_reasons": ";".join(sorted(ALLOWED_HARD_BLOCK_REASONS)),
                "weakness_flags": ";".join(flags),
                "duplicate_meaning": dup_meaning,
                "thesis_duration_class": thesis_duration,
                "authority": AUTHORITY,
            }
        )
        task968_reason_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "entry_date": feature["entry_date"],
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "primary_marginal_reason": action_reason,
                "trader_action": action,
                "is_hard_block": "1" if action == "hard_block" else "0",
                "authority": AUTHORITY,
            }
        )
        task969_rows.append(
            {
                "trade_spec_id": trade_spec_id,
                "decision_asof_ts": feature["decision_asof_ts"],
                "entry_date": feature["entry_date"],
                "split_id": feature["split_id"],
                "symbol": feature["symbol"],
                "theme": feature["theme"],
                "thesis_cluster_key": context["cluster_key"],
                "shadow_rank_score": score,
                "trader_action": action,
                "action_reason": action_reason,
                "duplicate_meaning": dup_meaning,
                "thesis_duration_class": thesis_duration,
                "source_gap_materiality": materiality,
                "does_not_use": FORBIDDEN_OUTCOME_INPUTS,
                "changes_executed_trade": "0",
                "authority": AUTHORITY,
            }
        )

    for trade in baseline_trades:
        feature = feature_by_id[trade["trade_spec_id"]]
        flags = flags_by_id[trade["trade_spec_id"]]
        pnl = float(trade["pnl"])
        task961_rows.append(
            {
                "trade_spec_id": trade["trade_spec_id"],
                "symbol": trade["symbol"],
                "theme": trade["theme"],
                "entry_date": trade["entry_date"],
                "exit_date": trade["exit_date"],
                "winner_loser_bucket": "winner" if pnl > 0 else "loser_or_flat",
                "weakness_flags": ";".join(flags),
                "economic_meaning_class": ";".join(sorted({semantic_class(flag, feature) for flag in flags})) or "unknown",
                "evaluation_only_pnl": f"{pnl:.6f}",
                "evaluation_only_return_pct": trade["return_pct"],
                "pnl_use_mode": "evaluation_only_never_selection_input",
                "authority": AUTHORITY,
            }
        )

    by_entry: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in task969_rows:
        by_entry[str(row["entry_date"])].append(row)
    task968_cohort_rows = []
    task969_compare_rows = []
    selected_shadow_ids: set[str] = set()
    for entry_date, group in sorted(by_entry.items()):
        hard_blocks = [row for row in group if row["trader_action"] == "hard_block"]
        rankable = [row for row in group if row["trader_action"] != "hard_block"]
        ranked = sorted(
            rankable,
            key=lambda row: (-int(row["shadow_rank_score"]), str(row["theme"]), str(row["symbol"]), str(row["trade_spec_id"])),
        )
        shadow_selected = ranked[:10]
        for rank, row in enumerate(ranked, start=1):
            row["shadow_rank_within_entry_date"] = rank
            row["shadow_slot10_selected"] = "1" if rank <= 10 else "0"
            if rank <= 10:
                selected_shadow_ids.add(str(row["trade_spec_id"]))
        for row in hard_blocks:
            row["shadow_rank_within_entry_date"] = ""
            row["shadow_slot10_selected"] = "0"
        task968_cohort_rows.append(
            {
                "entry_date": entry_date,
                "candidate_count_before": len(group),
                "hard_blocked_count": len(hard_blocks),
                "ranked_count": len(ranked),
                "shadow_selected_count": len(shadow_selected),
                "hard_block_rate_pct": f"{(len(hard_blocks) / len(group) * 100.0) if group else 0.0:.6f}",
                "replay_executed": "0",
                "authority": AUTHORITY,
            }
        )

    baseline_selected_ids = set(baseline_by_id)
    task969_compare_rows.append(
        {
            "comparison_id": "shadow_vs_task941_slot10",
            "baseline_slot10_selected_count": len(baseline_selected_ids),
            "shadow_slot10_selected_count": len(selected_shadow_ids),
            "overlap_count": len(baseline_selected_ids & selected_shadow_ids),
            "shadow_only_count": len(selected_shadow_ids - baseline_selected_ids),
            "baseline_only_count": len(baseline_selected_ids - selected_shadow_ids),
            "baseline_final_equity_reference": baseline_summary["strategy_final_equity"],
            "baseline_cagr_reference": baseline_summary["strategy_cagr_pct"],
            "baseline_mdd_reference": baseline_summary["strategy_max_drawdown_pct"],
            "replay_executed": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    )

    closeout = {
        "task_id": "Task961-970-redesign",
        "verdict": "external_audit_redesign_complete_no_replay",
        "input_trade_specs": len(features),
        "baseline_slot10_trades_evaluated": len(baseline_trades),
        "shadow_selected_count": len(selected_shadow_ids),
        "replay_executed": "0",
        "next_replay_allowed": "0",
        "next_required_action": "review_shadow_ranking_and_pre_register_one_controlled_policy_before_replay",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }

    source_manifest = [
        {"source_name": "task941_feature_panel", "path": FEATURE_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(FEATURE_PATH), "authority": AUTHORITY},
        {"source_name": "task941_baseline_trades", "path": BASELINE_TRADES_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_TRADES_PATH), "authority": AUTHORITY},
        {"source_name": "task941_baseline_summary", "path": BASELINE_SUMMARY_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(BASELINE_SUMMARY_PATH), "authority": AUTHORITY},
        {"source_name": "task917_l1_evidence", "path": L1_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(L1_PATH), "authority": AUTHORITY},
        {"source_name": "task919_candidate_bundles", "path": CANDIDATE_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(CANDIDATE_PATH), "authority": AUTHORITY},
        {"source_name": "task919_relation_edges", "path": RELATION_PATH.relative_to(ROOT).as_posix(), "sha256": sha256(RELATION_PATH), "authority": AUTHORITY},
    ]

    write_csv(OUT_DIR / "task961_baseline_winner_loser_semantic_audit.csv", task961_rows, [
        "trade_spec_id", "symbol", "theme", "entry_date", "exit_date", "winner_loser_bucket",
        "weakness_flags", "economic_meaning_class", "evaluation_only_pnl",
        "evaluation_only_return_pct", "pnl_use_mode", "authority",
    ])
    write_csv(OUT_DIR / "task962_weakness_semantic_reclassification.csv", task962_rows, [
        "trade_spec_id", "decision_asof_ts", "entry_date", "symbol", "theme", "weakness_flag",
        "weakness_semantic_class", "use_mode", "standalone_hard_block_allowed",
        "external_audit_question", "does_not_use", "authority",
    ])
    write_csv(OUT_DIR / "task963_asof_duplicate_thesis_meaning_ledger.csv", task963_rows, [
        "trade_spec_id", "decision_asof_ts", "entry_date", "symbol", "theme", "thesis_cluster_key",
        "prior_duplicate_count", "duplicate_meaning", "prior_only_sort_key",
        "standalone_hard_block_allowed", "authority",
    ])
    write_csv(OUT_DIR / "task964_source_gap_limitation_ledger.csv", task964_rows, [
        "trade_spec_id", "symbol", "theme", "source_gap_reason", "source_gap_materiality",
        "required_missing_artifact", "blocks_confidence", "blocks_trade",
        "standalone_hard_block_allowed", "authority",
    ])
    write_csv(OUT_DIR / "task965_stale_thesis_duration_audit.csv", task965_rows, [
        "trade_spec_id", "symbol", "theme", "newest_available_to_brain_ts",
        "newest_source_age_days", "thesis_duration_class", "stale_is_standalone_hard_block",
        "authority",
    ])
    write_csv(OUT_DIR / "task966_theme_macro_policy_timing_interpreter.csv", task966_rows, [
        "trade_spec_id", "symbol", "theme", "expert_lens_owner", "policy_macro_condition",
        "timing_effect", "direction_effect", "source_required_for_confidence", "authority",
    ])
    write_csv(OUT_DIR / "task967_trader_action_taxonomy.csv", task967_rows, [
        "trade_spec_id", "decision_asof_ts", "entry_date", "symbol", "theme", "trader_action",
        "action_reason", "hard_block_reason", "allowed_hard_block_reasons", "weakness_flags",
        "duplicate_meaning", "thesis_duration_class", "authority",
    ])
    write_csv(OUT_DIR / "task968_cohort_attrition_ledger.csv", task968_cohort_rows, [
        "entry_date", "candidate_count_before", "hard_blocked_count", "ranked_count",
        "shadow_selected_count", "hard_block_rate_pct", "replay_executed", "authority",
    ])
    write_csv(OUT_DIR / "task968_reason_marginal_attribution.csv", task968_reason_rows, [
        "trade_spec_id", "entry_date", "symbol", "theme", "primary_marginal_reason",
        "trader_action", "is_hard_block", "authority",
    ])
    write_csv(OUT_DIR / "task969_shadow_trader_ranking.csv", task969_rows, [
        "trade_spec_id", "decision_asof_ts", "entry_date", "split_id", "symbol", "theme",
        "thesis_cluster_key", "shadow_rank_score", "shadow_rank_within_entry_date",
        "shadow_slot10_selected", "trader_action", "action_reason", "duplicate_meaning",
        "thesis_duration_class", "source_gap_materiality", "does_not_use",
        "changes_executed_trade", "authority",
    ])
    write_csv(OUT_DIR / "task969_shadow_vs_baseline_comparison.csv", task969_compare_rows, [
        "comparison_id", "baseline_slot10_selected_count", "shadow_slot10_selected_count",
        "overlap_count", "shadow_only_count", "baseline_only_count",
        "baseline_final_equity_reference", "baseline_cagr_reference", "baseline_mdd_reference",
        "replay_executed", "strategy_acceptance", "deployment_readiness", "real_capital",
        "authority",
    ])
    write_csv(OUT_DIR / "task970_external_audit_closeout.csv", [closeout], list(closeout.keys()))
    write_csv(OUT_DIR / "task970_source_manifest.csv", source_manifest, ["source_name", "path", "sha256", "authority"])

    summary = {
        **closeout,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_gap_heavy_is_standalone_block": "0",
        "duplicate_is_standalone_block": "0",
        "stale_is_standalone_block": "0",
        "thin_packet_is_standalone_block": "0",
        "low_independent_evidence_is_standalone_block": "0",
    }
    write_csv(OUT_DIR / "task961_970_external_audit_redesign_summary.csv", [summary], list(summary.keys()))
    (OUT_DIR / "task961_970_external_audit_redesign_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_961_970_EXTERNAL_AUDIT_REDESIGN_OK] "
        f"input={summary['input_trade_specs']} shadow_selected={summary['shadow_selected_count']} replay={summary['replay_executed']}"
    )


if __name__ == "__main__":
    main()
