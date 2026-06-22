from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK881 = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep"
TASK1081 = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"
TASK1111 = ROOT / "data/artifacts/task_1111_1120_pre_replay_audit_program"
RAW = ROOT / "data/raw"
OUT_DIR = ROOT / "data/artifacts/task_1121_1130_pit_nonsec_repair"

AUTHORITY = "DIAGNOSTIC_PRE_REPLAY_REPAIR_GATE_ONLY"
VARIANT = "sec_slot3_theme_cap1_v1"
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


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def task1121_pit_schema_contract() -> list[dict[str, object]]:
    fields = [
        ("universe_id", "string", "required", "stable universe identifier"),
        ("symbol", "string", "required", "ticker symbol from candidate universe"),
        ("theme", "string", "required", "theme bucket for research universe"),
        ("membership_event_type", "enum", "required", "inclusion exclusion or correction event"),
        ("effective_start_ts", "timestamp", "required", "membership effective start"),
        ("effective_end_ts", "timestamp_or_blank", "required", "membership effective end or blank active interval"),
        ("published_ts", "timestamp", "required", "source publication timestamp"),
        ("received_ts", "timestamp", "required", "local or provider receipt timestamp"),
        ("available_to_brain_ts", "timestamp", "required", "earliest timestamp usable by brain"),
        ("raw_source_path", "path", "required", "raw source evidence path"),
        ("source_hash", "sha256", "required", "raw source hash"),
        ("source_authority_tier", "enum", "required", "official vendor derived or review_required"),
        ("pit_membership_pass", "0_or_1", "derived", "passes PIT membership invariants"),
        ("selection_use_allowed", "0_or_1", "derived", "allowed for selection after all gates"),
        ("replay_use_allowed", "0_or_1", "derived", "allowed for replay after all gates"),
    ]
    return [
        {
            "task_id": "Task1121",
            "schema_name": "pit_universe_membership_v1",
            "field_name": name,
            "field_type": field_type,
            "required_state": required,
            "meaning": meaning,
            "forbidden_behavior": "infer_from_price_history_or_current_membership_or_symbol_proximity",
            "authority": AUTHORITY,
        }
        for name, field_type, required, meaning in fields
    ]


def task1122_pit_source_catalog(universe_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    source_path = ROOT / "data/raw/theme_universe_10x7.csv"
    source_hash = file_sha256(source_path)
    rows = []
    for idx, row in enumerate(universe_rows, start=1):
        rows.append(
            {
                "task_id": "Task1122",
                "pit_source_id": f"PITSRC1122-{idx:05d}",
                "universe_id": "theme_universe_10x7_reference_only",
                "symbol": row["symbol"],
                "theme": row["theme"],
                "role": row["role"],
                "source_family": "static_research_universe_reference",
                "source_path_or_url": rel(source_path),
                "raw_source_path": rel(source_path),
                "source_hash": source_hash,
                "provider": "repo_static_csv",
                "published_ts": "",
                "received_ts": "",
                "available_to_brain_ts": "",
                "source_authority_tier": "reference_only_not_pit_membership",
                "source_state": "blocked_reference_only",
                "pit_evidence_candidate": "0",
                "pit_membership_source_pass": "0",
                "block_reason": "theme_universe_10x7_has_no_effective_or_available_timestamps",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def pit_pass(row: dict[str, str], decision_asof_ts: str) -> tuple[str, str]:
    required = ["effective_start_ts", "published_ts", "received_ts", "available_to_brain_ts", "raw_source_path", "source_hash"]
    missing = [field for field in required if not row.get(field)]
    if missing:
        return "0", "missing_" + "_".join(missing)
    decision_dt = parse_dt(decision_asof_ts)
    published_dt = parse_dt(row["published_ts"])
    received_dt = parse_dt(row["received_ts"])
    available_dt = parse_dt(row["available_to_brain_ts"])
    start_dt = parse_dt(row["effective_start_ts"])
    end_dt = parse_dt(row.get("effective_end_ts", ""))
    if not decision_dt or not published_dt or not received_dt or not available_dt or not start_dt:
        return "0", "unparseable_required_timestamp"
    if not (published_dt <= received_dt <= available_dt <= decision_dt):
        return "0", "invalid_source_time_order"
    if available_dt > decision_dt:
        return "0", "available_to_brain_after_decision"
    if start_dt > decision_dt:
        return "0", "effective_start_after_decision"
    if end_dt and decision_dt >= end_dt:
        return "0", "effective_end_before_or_at_decision"
    if row.get("source_authority_tier") == "reference_only_not_pit_membership":
        return "0", "reference_only_source_not_pit_membership"
    raw_path = ROOT / row["raw_source_path"]
    if not raw_path.exists():
        return "0", "raw_source_path_missing"
    if file_sha256(raw_path) != row["source_hash"]:
        return "0", "source_hash_mismatch"
    return "1", ""


def task1123_pit_membership_validation(membership_rows: list[dict[str, str]], pit_sources: list[dict[str, object]]) -> list[dict[str, object]]:
    source_by_key = {(str(row["symbol"]), str(row["theme"])): row for row in pit_sources}
    rows = []
    for idx, row in enumerate(membership_rows, start=1):
        source = source_by_key.get((row["symbol"], row["theme"]), {})
        normalized = {
            "task_id": "Task1123",
            "pit_membership_validation_id": f"PITVAL-{idx:07d}",
            "decision_id": row["decision_id"],
            "decision_asof_ts": row["decision_asof_ts"],
            "split_id": row["split_id"],
            "universe_id": row["universe_id"],
            "symbol": row["symbol"],
            "theme": row["theme"],
            "role": row["role"],
            "membership_state": row["membership_state"],
            "prior_pit_universe_state": row["pit_universe_state"],
            "membership_event_type": "unverified_static_inclusion",
            "effective_start_ts": "",
            "effective_end_ts": "",
            "published_ts": str(source.get("published_ts", "")),
            "received_ts": str(source.get("received_ts", "")),
            "available_to_brain_ts": str(source.get("available_to_brain_ts", "")),
            "raw_source_path": str(source.get("raw_source_path", "")),
            "source_hash": str(source.get("source_hash", "")),
            "source_authority_tier": str(source.get("source_authority_tier", "")),
        }
        pass_flag, reason = pit_pass(normalized, row["decision_asof_ts"])
        normalized.update(
            {
                "pit_membership_pass": pass_flag,
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "block_reason": reason or "blocked_until_full_replay_gate",
                "authority": AUTHORITY,
            }
        )
        rows.append(normalized)
    return rows


def task1124_trade_spec_pit_join_audit(features: list[dict[str, str]], pit_validation: list[dict[str, object]]) -> list[dict[str, object]]:
    validation_by_key = {(str(row["symbol"]), str(row["theme"]), str(row["decision_asof_ts"])): row for row in pit_validation}
    rows = []
    for idx, row in enumerate(features, start=1):
        pit = validation_by_key.get((row["symbol"], row["theme"], row["decision_asof_ts"]))
        pit_pass_flag = "1" if pit and pit["pit_membership_pass"] == "1" else "0"
        block_reason = "missing_decision_asof_pit_membership_row" if not pit else str(pit["block_reason"])
        rows.append(
            {
                "task_id": "Task1124",
                "pit_join_audit_id": f"PITJOIN1124-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "adapter_input_id": row["adapter_input_id"],
                "candidate_bundle_id": row["candidate_bundle_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "split_id": row["split_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "sec_asof_source_score": row["sec_asof_source_score"],
                "sec_source_time_pass": row["source_time_pass"],
                "sec_future_source_rows_used": row["future_source_rows_used"],
                "pit_membership_pass": pit_pass_flag,
                "pit_block_reason": "" if pit_pass_flag == "1" else block_reason,
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1125_nonsec_event_schema_contract() -> list[dict[str, object]]:
    fields = [
        ("event_id", "string", "required", "stable event identifier"),
        ("source_family", "string", "required", "raw source family"),
        ("event_category", "string", "required", "macro policy sector event category"),
        ("symbol_tags", "semicolon_string", "required_for_symbol_use", "explicit symbol tags"),
        ("theme_tags", "semicolon_string", "required_for_theme_use", "explicit theme tags"),
        ("event_ts", "timestamp", "required", "event or release timestamp"),
        ("published_ts", "timestamp", "required", "published timestamp"),
        ("received_ts", "timestamp", "required", "received timestamp"),
        ("available_to_brain_ts", "timestamp", "required", "first usable timestamp"),
        ("raw_source_path", "path", "required", "raw source path"),
        ("source_hash", "sha256", "required", "raw source hash"),
        ("time_precision", "enum", "required", "timestamp date-only or missing precision"),
        ("source_time_method", "enum", "required", "exact repaired candidate or missing"),
        ("authority_tier", "enum", "required", "official vendor derived or review_required"),
        ("confidence_state", "enum", "required", "exact repaired candidate or blocked"),
        ("tag_source_method", "enum", "required", "explicit source tag or missing"),
        ("source_gap_flag", "0_or_1", "derived", "1 when source-time or tag evidence is incomplete"),
        ("dynamic_use_allowed", "0_or_1", "derived", "allowed for dynamic shadow use only after invariants pass"),
    ]
    return [
        {
            "task_id": "Task1125",
            "schema_name": "non_sec_asof_event_v1",
            "field_name": name,
            "field_type": field_type,
            "required_state": required,
            "meaning": meaning,
            "forbidden_behavior": "derive_source_time_from_event_date_or_price_or_lifecycle_proximity",
            "authority": AUTHORITY,
        }
        for name, field_type, required, meaning in fields
    ]


def normalize_macro_fred() -> list[dict[str, object]]:
    path = RAW / "macro_fred/task_655/fred_macro_release_repaired_feature_panel.csv"
    source_hash = file_sha256(path)
    rows = []
    for idx, row in enumerate(read_csv(path), start=1):
        rows.append(
            {
                "task_id": "Task1126",
                "event_id": f"MACROFRED-{idx:07d}",
                "source_family": "macro_fred",
                "source_lane": "macro_economic",
                "source_name": row["series_id"],
                "source_url": row["source_url"],
                "event_category": row["category"],
                "symbol_tags": "",
                "theme_tags": "",
                "event_ts": row["release_ts_utc"],
                "published_ts": row["release_ts_utc"],
                "received_ts": "",
                "available_to_brain_ts": row["tradable_after_ts_utc"],
                "raw_source_path": rel(path),
                "source_hash": source_hash,
                "authority_tier": "vendor_derived_macro_candidate",
                "confidence_state": "timestamp_candidate_but_vintage_not_certified",
                "time_precision": "timestamp_candidate_repaired",
                "source_time_method": row["release_timestamp_method"],
                "tag_source_method": "no_symbol_or_theme_tag_macro_context_only",
                "latest_vintage_only_flag": row["latest_vintage_only_flag"],
                "exact_release_calendar_verified_flag": row["exact_release_calendar_verified_flag"],
                "vintage_asof_certified_flag": row["vintage_asof_certified_flag"],
                "source_gap_flag": "1",
                "dynamic_use_allowed": "0",
                "block_reason": "missing_received_ts_explicit_tags_and_vintage_asof_certification",
                "authority": AUTHORITY,
            }
        )
    return rows


def normalize_task636() -> list[dict[str, object]]:
    path = RAW / "task_636_content_source_text/task_636_source_text_checkpoint.csv"
    rows = []
    nonsec_rows = [row for row in read_csv(path) if row.get("source_name") != "sec_company_submissions"]
    for idx, row in enumerate(nonsec_rows, start=1):
        raw_path = ROOT / row["raw_text_path"] if row.get("raw_text_path") else path
        source_hash = row.get("source_text_hash") or (file_sha256(raw_path) if raw_path.exists() else "")
        rows.append(
            {
                "task_id": "Task1126",
                "event_id": f"TASK636-{idx:07d}",
                "source_family": "task_636_content_source_text",
                "source_lane": row["source_lane"],
                "source_name": row["source_name"],
                "source_url": row["source_url"],
                "event_category": row["event_category"],
                "symbol_tags": row["symbol_tags"],
                "theme_tags": row["theme_tags"],
                "event_ts": row["event_date"],
                "published_ts": "",
                "received_ts": "",
                "available_to_brain_ts": "",
                "raw_source_path": row["raw_text_path"],
                "source_hash": source_hash,
                "authority_tier": "raw_text_checkpoint_candidate",
                "confidence_state": "raw_hash_candidate_but_source_time_missing",
                "time_precision": "date_only_not_source_time",
                "source_time_method": "event_date_not_promoted_to_published_ts",
                "tag_source_method": "explicit_task636_tags",
                "latest_vintage_only_flag": "",
                "exact_release_calendar_verified_flag": "",
                "vintage_asof_certified_flag": "",
                "source_gap_flag": "1",
                "dynamic_use_allowed": "0",
                "block_reason": "missing_published_received_available_timestamps",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1127_nonsec_event_validation(events: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(events, start=1):
        missing = []
        for field in ["raw_source_path", "source_hash", "published_ts", "received_ts", "available_to_brain_ts"]:
            if not row.get(field):
                missing.append(field)
        if not row.get("symbol_tags") and not row.get("theme_tags"):
            missing.append("explicit_symbol_or_theme_tags")
        if row.get("vintage_asof_certified_flag") == "0":
            missing.append("vintage_asof_certified_flag")
        pass_flag = "0" if missing else "1"
        rows.append(
            {
                "task_id": "Task1127",
                "nonsec_validation_id": f"NONSECVAL-{idx:07d}",
                "event_id": row["event_id"],
                "source_family": row["source_family"],
                "event_category": row["event_category"],
                "symbol_tags": row["symbol_tags"],
                "theme_tags": row["theme_tags"],
                "published_ts": row["published_ts"],
                "received_ts": row["received_ts"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "raw_source_path": row["raw_source_path"],
                "source_hash_present": "1" if row.get("source_hash") else "0",
                "nonsec_source_time_pass": pass_flag,
                "dynamic_use_allowed": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "block_reason": "" if pass_flag == "1" else "missing_" + "_".join(missing),
                "authority": AUTHORITY,
            }
        )
    return rows


def task1128_entry_exposure_boundary(reentry_rows: list[dict[str, str]], exposure_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    fresh = []
    for idx, row in enumerate(reentry_rows, start=1):
        is_fresh_candidate = row["is_reentry"] == "0" and row["stale_reentry_flag"] == "0"
        fresh.append(
            {
                "task_id": "Task1128",
                "fresh_entry_boundary_id": f"FRESHBOUND-{idx:05d}",
                "policy_variant_id": row["policy_variant_id"],
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "thesis_fingerprint": row["thesis_fingerprint"],
                "is_reentry": row["is_reentry"],
                "stale_reentry_flag": row["stale_reentry_flag"],
                "fresh_entry_candidate_flag": "1" if is_fresh_candidate else "0",
                "entry_judgment_state": "fresh_initial_entry_candidate" if is_fresh_candidate else "stale_reentry_not_fresh_judgment",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    exposure = []
    for idx, row in enumerate(exposure_rows, start=1):
        exposure.append(
            {
                "task_id": "Task1128",
                "exposure_boundary_id": f"EXPOSUREBOUND-{idx:05d}",
                "policy_variant_id": row["policy_variant_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "thesis_fingerprint": row["thesis_fingerprint"],
                "episode_trade_count": row["episode_trade_count"],
                "stale_reentry_count": row["stale_reentry_count"],
                "continuous_thesis_exposure_flag": row["continuous_thesis_exposure_flag"],
                "exposure_policy_state": "requires_structural_hold_preregistration",
                "entry_counting_allowed": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return fresh, exposure


def task1129_1130_closeout(
    pit_validation: list[dict[str, object]],
    pit_join: list[dict[str, object]],
    nonsec_validation: list[dict[str, object]],
    fresh_boundary: list[dict[str, object]],
    exposure_boundary: list[dict[str, object]],
) -> dict[str, object]:
    pit_pass_rows = sum(1 for row in pit_validation if row["pit_membership_pass"] == "1")
    pit_join_pass = sum(1 for row in pit_join if row["pit_membership_pass"] == "1")
    dynamic_allowed = sum(1 for row in nonsec_validation if row["dynamic_use_allowed"] == "1")
    stale_blocked = sum(1 for row in fresh_boundary if row["stale_reentry_flag"] == "1")
    verdict = "go_for_policy_preregistration_only" if pit_join_pass > 0 and dynamic_allowed > 0 else "blocked_continue_source_repair"
    return {
        "task_id": "Task1121-1130",
        "verdict": verdict,
        "pit_membership_rows": len(pit_validation),
        "pit_pass_rows": pit_pass_rows,
        "pit_blocked_rows": len(pit_validation) - pit_pass_rows,
        "sec_feature_rows_audited": len(pit_join),
        "sec_feature_pit_pass_rows": pit_join_pass,
        "sec_feature_pit_blocked_rows": len(pit_join) - pit_join_pass,
        "nonsec_event_rows": len(nonsec_validation),
        "nonsec_dynamic_use_rows": dynamic_allowed,
        "nonsec_blocked_rows": len(nonsec_validation) - dynamic_allowed,
        "fresh_entry_candidate_rows": sum(1 for row in fresh_boundary if row["fresh_entry_candidate_flag"] == "1"),
        "stale_reentry_blocked_rows": stale_blocked,
        "continuous_exposure_episode_rows": len(exposure_boundary),
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "continue_pit_membership_source_acquisition_and_nonsec_timestamp_normalization_before_policy_preregistration",
        "authority": AUTHORITY,
    }


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    universe = read_csv(ROOT / "data/raw/theme_universe_10x7.csv")
    membership_rows = read_csv(TASK881 / "universe_membership_panel.csv")
    features = read_csv(TASK1081 / "task1082_sec_asof_adapter_feature_panel.csv")
    reentries = read_csv(TASK1111 / "task1115_reentry_freshness_ledger.csv")
    exposures = read_csv(TASK1111 / "task1116_continuous_thesis_exposure_ledger.csv")

    task1121 = task1121_pit_schema_contract()
    task1122 = task1122_pit_source_catalog(universe)
    task1123 = task1123_pit_membership_validation(membership_rows, task1122)
    task1124 = task1124_trade_spec_pit_join_audit(features, task1123)
    task1125 = task1125_nonsec_event_schema_contract()
    task1126 = normalize_macro_fred() + normalize_task636()
    task1127 = task1127_nonsec_event_validation(task1126)
    task1128_fresh, task1128_exposure = task1128_entry_exposure_boundary(reentries, exposures)
    closeout = task1129_1130_closeout(task1123, task1124, task1127, task1128_fresh, task1128_exposure)

    write_csv(OUT_DIR / "task1121_pit_membership_schema_contract.csv", task1121)
    write_csv(OUT_DIR / "task1122_pit_source_catalog.csv", task1122)
    write_csv(OUT_DIR / "task1123_pit_membership_validation_panel.csv", task1123)
    write_csv(OUT_DIR / "task1124_trade_spec_pit_join_audit.csv", task1124)
    write_csv(OUT_DIR / "task1125_nonsec_event_schema_contract.csv", task1125)
    write_csv(OUT_DIR / "task1126_nonsec_normalized_event_candidates.csv", task1126)
    write_csv(OUT_DIR / "task1127_nonsec_event_validation_panel.csv", task1127)
    write_csv(OUT_DIR / "task1128_fresh_entry_candidate_ledger.csv", task1128_fresh)
    write_csv(OUT_DIR / "task1128_continuous_exposure_episode_ledger.csv", task1128_exposure)
    write_csv(OUT_DIR / "task1129_integrated_pre_replay_gate.csv", [closeout])
    write_csv(OUT_DIR / "task1130_pit_nonsec_repair_closeout.csv", [closeout])
    (OUT_DIR / "task1130_pit_nonsec_repair_closeout.json").write_text(json.dumps(closeout, indent=2), encoding="utf-8")
    return closeout


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1121_1130_PIT_NONSEC_REPAIR_OK] "
        f"verdict={summary['verdict']} pit_pass={summary['pit_pass_rows']}/{summary['pit_membership_rows']} "
        f"nonsec_dynamic={summary['nonsec_dynamic_use_rows']}/{summary['nonsec_event_rows']} replay={summary['replay_executed']}"
    )


if __name__ == "__main__":
    main()
