from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SEC_ART = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"
UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
OUT_DIR = ROOT / "data/artifacts/task_1111_1120_pre_replay_audit_program"

VARIANT = "sec_slot3_theme_cap1_v1"
AUTHORITY = "DIAGNOSTIC_PRE_REPLAY_AUDIT_ONLY"
FORBIDDEN_INPUTS = "future_return realized_return pnl post_entry_price_change outcome_rank exit_price"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value[:10])


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def thesis_fingerprint(row: dict[str, str]) -> str:
    parts = [
        row.get("symbol", ""),
        row.get("theme", ""),
        row.get("candidate_thesis_type", ""),
        row.get("relation_state", ""),
        row.get("available_fact_families", ""),
        row.get("relation_edges", ""),
        row.get("sec_asof_source_score", ""),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:16]


def task1111_pit_universe_source_catalog(universe: list[dict[str, str]]) -> list[dict[str, object]]:
    source_hash = file_sha256(UNIVERSE_PATH)
    pit_columns = {"as_of_date", "start_date", "end_date", "effective_date", "created_at", "source_timestamp"}
    columns = set(universe[0].keys()) if universe else set()
    has_pit = bool(pit_columns & columns)
    rows = []
    for idx, row in enumerate(universe, start=1):
        rows.append(
            {
                "task_id": "Task1111",
                "universe_row_id": f"PITCAT-{idx:05d}",
                "universe_source_id": f"PITSRC-{idx:05d}",
                "source_family": "theme_universe_10x7_fixed_research_universe",
                "theme": row["theme"],
                "symbol": row["symbol"],
                "role": row["role"],
                "source_path_or_url": rel(UNIVERSE_PATH),
                "raw_source_path": rel(UNIVERSE_PATH),
                "source_path": rel(UNIVERSE_PATH),
                "source_sha256": source_hash,
                "source_hash": source_hash,
                "provider": "repo_static_csv",
                "captured_at_ts": "",
                "published_ts": "",
                "received_ts": "",
                "source_type": "static_theme_universe_file",
                "source_columns": ";".join(universe[0].keys()),
                "has_pit_membership_timestamp": "1" if has_pit else "0",
                "membership_available_to_brain_ts": "",
                "license_state": "repo_internal_unknown_external_license",
                "raw_source_state": "static_file_present_but_not_pit_membership_evidence",
                "pit_admission_state": "pit_membership_source_ready" if has_pit else "blocked_missing_pit_membership_source",
                "blocker_reason": "" if has_pit else "static_theme_universe_file_is_not_pit_membership_evidence",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1112_pit_membership_panel(universe_catalog: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(universe_catalog, start=1):
        rows.append(
            {
                "task_id": "Task1112",
                "membership_id": f"PITMEM-{idx:05d}",
                "membership_event_id": f"PITEVT-{idx:05d}",
                "universe_id": "theme_universe_10x7",
                "symbol": row["symbol"],
                "theme": row["theme"],
                "role": row["role"],
                "membership_event_type": "unverified_static_inclusion",
                "inclusion_reason": row["role"],
                "exclusion_reason": "",
                "effective_from": "",
                "effective_to": "",
                "effective_start_ts": "",
                "effective_end_ts": "",
                "published_ts": "",
                "received_ts": "",
                "membership_available_to_brain_ts": "",
                "available_to_brain_ts": "",
                "universe_source_id": row["universe_source_id"],
                "source_hash": row["source_hash"],
                "raw_source_path": row["raw_source_path"],
                "evidence_state": "missing_pit_membership_source",
                "pit_membership_state": "unverified_static_membership",
                "pit_membership_pass": "0",
                "membership_use_allowed": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "blocked_reason": "missing_point_in_time_universe_membership",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1113_trade_spec_pit_join_audit(
    features: list[dict[str, str]],
    membership: list[dict[str, object]],
) -> list[dict[str, object]]:
    membership_by_key = {(str(row["symbol"]), str(row["theme"])): row for row in membership}
    rows = []
    for idx, row in enumerate(features, start=1):
        mem = membership_by_key.get((row["symbol"], row["theme"]))
        pass_flag = "1" if mem and mem["pit_membership_pass"] == "1" else "0"
        rows.append(
            {
                "task_id": "Task1113",
                "pit_join_audit_id": f"PITJOIN-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "adapter_input_id": row["adapter_input_id"],
                "candidate_bundle_id": row["candidate_bundle_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "tradable_after_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "split_id": row["split_id"],
                "universe_id": "theme_universe_10x7",
                "symbol": row["symbol"],
                "theme": row["theme"],
                "sec_asof_source_score": row["sec_asof_source_score"],
                "source_time_pass": row["source_time_pass"],
                "future_source_rows_used": row["future_source_rows_used"],
                "membership_state": "" if not mem else mem["pit_membership_state"],
                "membership_available_to_brain_ts": "" if not mem else mem["membership_available_to_brain_ts"],
                "membership_effective_start_ts": "" if not mem else mem["effective_start_ts"],
                "membership_effective_end_ts": "" if not mem else mem["effective_end_ts"],
                "pit_membership_pass": pass_flag,
                "pit_universe_pass": pass_flag,
                "pit_join_state": "pit_join_verified" if pass_flag == "1" else "blocked_unverified_membership",
                "selected_under_pit": "0",
                "pit_selection_allowed": "0",
                "pit_replay_allowed": "0",
                "blocked_reason": "" if pass_flag == "1" else "missing_point_in_time_universe_membership",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1114_pit_block_ledger(join_audit: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate((r for r in join_audit if r["pit_membership_pass"] == "0"), start=1):
        rows.append(
            {
                "task_id": "Task1114",
                "pit_block_id": f"PITBLOCK-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "blocked_reason": "missing_point_in_time_universe_membership",
                "would_block_selection": "1",
                "would_block_replay": "1",
                "source_time_pass": row["source_time_pass"],
                "pit_membership_pass": row["pit_membership_pass"],
                "authority": AUTHORITY,
            }
        )
    return rows


def task1115_reentry_freshness_ledger(
    selections: list[dict[str, str]],
    trades: list[dict[str, str]],
) -> list[dict[str, object]]:
    exit_by_trade_spec = {row["trade_spec_id"]: row.get("exit_date", "") for row in trades}
    selected = [row for row in selections if row["policy_variant_id"] == VARIANT and row["decision_state"] == "selected"]
    selected.sort(key=lambda row: (row["symbol"], row["entry_date"], row["trade_spec_id"]))
    prior_by_symbol: dict[str, dict[str, object]] = {}
    rows = []
    for idx, row in enumerate(selected, start=1):
        prior = prior_by_symbol.get(row["symbol"])
        fp = thesis_fingerprint(row)
        latest_ts = row.get("latest_available_to_brain_ts", "")
        prior_latest = str(prior["latest_available_to_brain_ts"]) if prior else ""
        same_score = bool(prior and row["sec_asof_source_score"] == prior["sec_asof_source_score"])
        same_thesis = bool(prior and fp == prior["thesis_fingerprint"])
        current_dt = parse_dt(latest_ts)
        prior_dt = parse_dt(prior_latest)
        new_evidence = bool(prior is None or (current_dt and prior_dt and current_dt > prior_dt))
        entry = parse_date(row["entry_date"])
        prior_entry = parse_date(str(prior["entry_date"])) if prior else None
        gap_days = "" if not entry or not prior_entry else str((entry - prior_entry).days)
        stale = bool(prior and same_score and (not new_evidence or same_thesis))
        reentry_state = "first_entry"
        if prior:
            reentry_state = "stale_same_score_reentry" if stale else "refreshed_reentry"
        out = {
            "task_id": "Task1115",
            "reentry_audit_id": f"REENTRY-{idx:05d}",
            "policy_variant_id": VARIANT,
            "symbol": row["symbol"],
            "theme": row["theme"],
            "trade_spec_id": row["trade_spec_id"],
            "decision_asof_ts": row["decision_asof_ts"],
            "entry_date": row["entry_date"],
            "exit_date": exit_by_trade_spec.get(row["trade_spec_id"], ""),
            "sec_asof_source_score": row["sec_asof_source_score"],
            "latest_available_to_brain_ts": latest_ts,
            "thesis_fingerprint": fp,
            "prior_trade_spec_id": "" if not prior else prior["trade_spec_id"],
            "prior_entry_date": "" if not prior else prior["entry_date"],
            "prior_exit_date": "" if not prior else prior["exit_date"],
            "prior_sec_asof_source_score": "" if not prior else prior["sec_asof_source_score"],
            "prior_latest_available_to_brain_ts": prior_latest,
            "prior_thesis_fingerprint": "" if not prior else prior["thesis_fingerprint"],
            "reentry_sequence_n": 1 if not prior else int(prior["reentry_sequence_n"]) + 1,
            "reentry_gap_days": gap_days,
            "is_reentry": "1" if prior else "0",
            "same_score_reentry_flag": "1" if same_score else "0",
            "same_thesis_reentry_flag": "1" if same_thesis else "0",
            "new_sec_evidence_since_prior_entry": "1" if new_evidence else "0",
            "stale_reentry_flag": "1" if stale else "0",
            "reentry_state": reentry_state,
            "reentry_selection_use_allowed": "0",
            "stale_reason": "" if not stale else "same_score_without_newer_sec_evidence_or_same_thesis",
            "authority": AUTHORITY,
        }
        rows.append(out)
        prior_by_symbol[row["symbol"]] = out
    return rows


def task1116_continuous_thesis_exposure_ledger(
    reentries: list[dict[str, object]],
    trades: list[dict[str, str]],
) -> list[dict[str, object]]:
    cash_by_trade_spec = {row["trade_spec_id"]: float(row.get("entry_cash_spent") or 0.0) for row in trades}
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in reentries:
        groups[(str(row["symbol"]), str(row["theme"]), str(row["thesis_fingerprint"]))].append(row)

    rows = []
    for idx, ((symbol, theme, fp), items) in enumerate(sorted(groups.items()), start=1):
        items.sort(key=lambda row: (str(row["entry_date"]), str(row["trade_spec_id"])))
        start = str(items[0]["entry_date"])
        end = str(items[-1]["exit_date"] or items[-1]["entry_date"])
        start_date = parse_date(start)
        end_date = parse_date(end)
        days = "" if not start_date or not end_date else str((end_date - start_date).days)
        stale_count = sum(1 for row in items if row["stale_reentry_flag"] == "1")
        same_score_count = sum(1 for row in items if row["same_score_reentry_flag"] == "1")
        same_thesis_count = sum(1 for row in items if row["same_thesis_reentry_flag"] == "1")
        gaps = [int(str(row["reentry_gap_days"])) for row in items if str(row["reentry_gap_days"]).isdigit()]
        rows.append(
            {
                "task_id": "Task1116",
                "policy_variant_id": VARIANT,
                "exposure_episode_id": f"EXPOSURE-{idx:05d}",
                "symbol": symbol,
                "theme": theme,
                "thesis_fingerprint": fp,
                "episode_start_entry_date": start,
                "episode_end_exit_date": end,
                "episode_trade_count": len(items),
                "episode_calendar_days": days,
                "total_entry_cash_spent": f"{sum(cash_by_trade_spec.get(str(row['trade_spec_id']), 0.0) for row in items):.6f}",
                "same_score_trade_count": same_score_count,
                "same_thesis_trade_count": same_thesis_count,
                "stale_reentry_count": stale_count,
                "new_evidence_event_count": sum(1 for row in items if row["new_sec_evidence_since_prior_entry"] == "1"),
                "max_reentry_gap_days": "" if not gaps else max(gaps),
                "continuous_thesis_exposure_flag": "1" if len(items) > 1 and stale_count > 0 else "0",
                "exposure_type": "structural_hold_candidate" if len(items) > 1 and stale_count > 0 else "single_or_refreshed_entry",
                "audit_note": "repeated_same_thesis_entries_must_be_modeled_as_exposure_not_new_independent_trades"
                if len(items) > 1 and stale_count > 0
                else "no_continuous_stale_chain_detected",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1117_structural_hold_policy_preregistration() -> list[dict[str, object]]:
    common = {
        "task_id": "Task1117",
        "preregistered_before_replay_flag": "1",
        "policy_variant_id": VARIANT,
        "symbol_scope": "all_theme_universe_symbols_after_pit_membership_pass",
        "theme_scope": "10_theme_7_symbol_universe_after_pit_membership_pass",
        "thesis_fingerprint_rule": "symbol_theme_candidate_thesis_relation_fact_family_score_hash",
        "min_source_time_pass_required": "1",
        "min_available_meaning_count": "1",
        "min_relation_edge_count": "1",
        "allowed_candidate_thesis_type": "source_backed_fundamental_context_packet",
        "max_missing_core_count": "1",
        "max_source_gap_count": "4",
        "non_sec_source_required_flag": "1",
        "pit_universe_required_flag": "1",
        "forbidden_inputs": FORBIDDEN_INPUTS,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "authority": AUTHORITY,
    }
    policies = [
        {
            "policy_id": "cooldown_no_new_evidence_v1",
            "structural_hold_rule_id": "HOLDRULE-001",
            "entry_rule": "entry_allowed_only_if_pit_and_non_sec_time_pass_and_thesis_is_fresh",
            "hold_rule": "no_implicit_hold_extension_from_same_static_score",
            "exit_rule": "scheduled_exit_or_source_backed_invalidation",
            "reentry_suppression_rule": "same_symbol_same_thesis_requires_newer_source_or_63_calendar_day_cooldown",
            "evaluation_use_mode": "future_controlled_replay_candidate_after_pit_and_dynamic_source_repair",
        },
        {
            "policy_id": "continuous_structural_winner_hold_v1",
            "structural_hold_rule_id": "HOLDRULE-002",
            "entry_rule": "single_initial_entry_when_thesis_first_becomes_source_backed",
            "hold_rule": "convert_repeated_same_thesis_entries_into_one_continuous_exposure_episode",
            "exit_rule": "pre_registered_invalidation_contradiction_or_risk_stop",
            "reentry_suppression_rule": "no_reentry_counting_inside_same_exposure_episode",
            "evaluation_use_mode": "separate_structural_hold_model_not_comparable_to_repeated_buy_policy",
        },
        {
            "policy_id": "baseline_repeated_buy_current_v1",
            "structural_hold_rule_id": "HOLDRULE-003",
            "entry_rule": "current_sec_score_slot_selection_for_diagnostic_control_only",
            "hold_rule": "scheduled_30_day_holding_window",
            "exit_rule": "scheduled_exit",
            "reentry_suppression_rule": "none_current_behavior_control",
            "evaluation_use_mode": "control_only_not_promotable_until_pit_and_dynamic_sources_pass",
        },
    ]
    return [{**common, **policy} for policy in policies]


def inventory_family(path: Path, family_id: str, family_type: str) -> dict[str, object]:
    files = [item for item in path.rglob("*") if item.is_file()] if path.exists() else []
    sample = files[0] if files else None
    has_source_time_columns = "0"
    time_sample = sample
    csv_time_columns = {
        "published_at",
        "published_ts",
        "release_date",
        "release_ts_utc",
        "tradable_after_ts",
        "tradable_after_ts_utc",
        "realtime_start",
        "available_to_brain_ts",
        "source_timestamp",
    }
    for candidate in files:
        if candidate.suffix.lower() != ".csv":
            continue
        try:
            with candidate.open(newline="", encoding="utf-8-sig") as handle:
                fieldnames = csv.DictReader(handle).fieldnames or []
        except UnicodeDecodeError:
            continue
        if csv_time_columns & set(fieldnames):
            has_source_time_columns = "1"
            time_sample = candidate
            break
    if time_sample:
        sample = time_sample
    return {
        "task_id": "Task1118",
                "source_family_id": family_id,
                "evidence_id": f"NONSEC-{family_id}",
                "source_family": family_id,
                "source_family_type": family_type,
                "source_lane": family_type,
                "source_name": family_id,
                "source_url": "",
                "raw_path": rel(path),
                "local_path": rel(path),
                "file_count": len(files),
                "sample_file": "" if not sample else rel(sample),
                "raw_text_path": "" if not sample else rel(sample),
                "sample_sha256": "" if not sample else file_sha256(sample),
                "source_hash": "" if not sample else file_sha256(sample),
                "published_ts": "",
                "received_ts": "",
                "available_to_brain_ts": "",
                "event_ts": "",
                "observation_date": "",
                "period_start": "",
                "period_end": "",
                "symbol_tags": "",
                "theme_tags": "",
                "policy_tags": "",
                "event_category": family_type,
                "issuer": "",
                "authority_tier": "review_required",
                "official_source_flag": "0",
                "source_time_method": "not_normalized_single_row_hash_time_join",
                "exact_time_verified_flag": "0",
                "vintage_asof_certified_flag": "0",
                "has_raw_hash": "1" if sample else "0",
                "raw_hash_present_flag": "1" if sample else "0",
                "has_published_ts": has_source_time_columns,
                "has_available_to_brain_ts": has_source_time_columns,
                "source_gap_flag": "1",
                "block_reason": "missing_single_row_raw_hash_and_published_received_available_timestamps",
                "source_time_state": "timestamped_candidate_review_required" if has_source_time_columns == "1" else "blocked_missing_normalized_source_time",
                "dynamic_use_allowed": "0",
                "selection_use_allowed": "0",
        "replay_use_allowed": "0",
        "authority": AUTHORITY,
    }


def task1118_non_sec_source_time_panel() -> list[dict[str, object]]:
    families = [
        ("fed_fomc_task612", "macro_policy", ROOT / "data/raw/fed_fomc_task612"),
        ("macro_fred", "macro_economic", ROOT / "data/raw/macro_fred"),
        ("fama_french", "factor_context", ROOT / "data/raw/fama_french"),
        ("research_l1_l4_context_curriculum", "institutional_curriculum", ROOT / "data/raw/research/l1_l4_context_curriculum"),
        ("task_625_big_event_source_text", "event_text", ROOT / "data/raw/task_625_big_event_source_text"),
        ("task_636_content_source_text", "content_text", ROOT / "data/raw/task_636_content_source_text"),
        ("intelligence_task614", "political_geopolitical", ROOT / "data/raw/intelligence_task614"),
    ]
    return [inventory_family(path, family_id, family_type) for family_id, family_type, path in families]


def task1119_dynamic_event_shadow_ranking(reentries: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(reentries, start=1):
        rows.append(
            {
                "task_id": "Task1119",
                "shadow_ranking_id": f"SHADOWDYN-{idx:05d}",
                "policy_variant_id": VARIANT,
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "sec_asof_source_score": row["sec_asof_source_score"],
                "thesis_fingerprint": row["thesis_fingerprint"],
                "dynamic_event_available": "0",
                "dynamic_event_count_asof": "0",
                "dynamic_event_score_delta": "0",
                "shadow_rank_delta": "0",
                "shadow_rank_state": "blocked_missing_non_sec_source_time",
                "shadow_ranking_use_allowed": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "blocked_reason": "missing_non_sec_raw_timestamped_event",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1120_closeout(
    universe_catalog: list[dict[str, object]],
    membership: list[dict[str, object]],
    join_audit: list[dict[str, object]],
    pit_blocks: list[dict[str, object]],
    reentries: list[dict[str, object]],
    exposures: list[dict[str, object]],
    non_sec: list[dict[str, object]],
    shadow: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "task_id": "Task1111-1120",
        "verdict": "pre_replay_audit_blocks_next_replay_until_pit_and_dynamic_sources_are_repaired",
        "audited_variant": VARIANT,
        "pit_universe_rows": len(universe_catalog),
        "pit_membership_verified_rows": sum(1 for row in membership if row["pit_membership_pass"] == "1"),
        "trade_specs_audited": len(join_audit),
        "trade_specs_blocked_by_pit": len(pit_blocks),
        "selected_reentry_rows": len(reentries),
        "stale_same_score_reentries": sum(1 for row in reentries if row["stale_reentry_flag"] == "1"),
        "continuous_exposure_chains": sum(1 for row in exposures if row["continuous_thesis_exposure_flag"] == "1"),
        "non_sec_families_inventoried": len(non_sec),
        "non_sec_families_dynamic_allowed": sum(1 for row in non_sec if row["dynamic_use_allowed"] == "1"),
        "dynamic_shadow_rows": len(shadow),
        "dynamic_shadow_rows_blocked": sum(1 for row in shadow if row["shadow_ranking_use_allowed"] == "0"),
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "repair_pit_universe_source_dates_and_build_normalized_non_sec_asof_event_panel_before_any_new_replay",
        "authority": AUTHORITY,
    }


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = read_csv(UNIVERSE_PATH)
    features = read_csv(SEC_ART / "task1082_sec_asof_adapter_feature_panel.csv")
    selections = read_csv(SEC_ART / "task1083_sec_asof_selection_ledger.csv")
    trades = [row for row in read_csv(SEC_ART / "task1084_sec_asof_replay_trades.csv") if row["policy_variant_id"] == VARIANT]

    task1111 = task1111_pit_universe_source_catalog(universe)
    task1112 = task1112_pit_membership_panel(task1111)
    task1113 = task1113_trade_spec_pit_join_audit(features, task1112)
    task1114 = task1114_pit_block_ledger(task1113)
    task1115 = task1115_reentry_freshness_ledger(selections, trades)
    task1116 = task1116_continuous_thesis_exposure_ledger(task1115, trades)
    task1117 = task1117_structural_hold_policy_preregistration()
    task1118 = task1118_non_sec_source_time_panel()
    task1119 = task1119_dynamic_event_shadow_ranking(task1115)
    task1120 = task1120_closeout(task1111, task1112, task1113, task1114, task1115, task1116, task1118, task1119)

    write_csv(OUT_DIR / "task1111_pit_universe_source_catalog.csv", task1111)
    write_csv(OUT_DIR / "task1112_pit_membership_panel.csv", task1112)
    write_csv(OUT_DIR / "task1113_trade_spec_pit_join_audit.csv", task1113)
    write_csv(OUT_DIR / "task1114_pit_block_ledger.csv", task1114)
    write_csv(OUT_DIR / "task1115_reentry_freshness_ledger.csv", task1115)
    write_csv(OUT_DIR / "task1116_continuous_thesis_exposure_ledger.csv", task1116)
    write_csv(OUT_DIR / "task1117_structural_hold_policy_preregistration.csv", task1117)
    write_csv(OUT_DIR / "task1118_non_sec_source_time_panel.csv", task1118)
    write_csv(OUT_DIR / "task1119_dynamic_event_shadow_ranking.csv", task1119)
    write_csv(OUT_DIR / "task1120_external_audit_closeout.csv", [task1120])
    (OUT_DIR / "task1120_external_audit_closeout.json").write_text(json.dumps(task1120, indent=2), encoding="utf-8")
    return task1120


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1111_1120_PRE_REPLAY_AUDIT_OK] "
        f"verdict={summary['verdict']} pit_blocked={summary['trade_specs_blocked_by_pit']}/"
        f"{summary['trade_specs_audited']} stale_reentries={summary['stale_same_score_reentries']} "
        f"replay_executed={summary['replay_executed']}"
    )


if __name__ == "__main__":
    main()
