from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW = ROOT / "data/raw"
TASK881 = ROOT / "data/artifacts/task_881_890_historical_brain_backtest_prep"
TASK1081 = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"
TASK1111 = ROOT / "data/artifacts/task_1111_1120_pre_replay_audit_program"
TASK1121 = ROOT / "data/artifacts/task_1121_1130_pit_nonsec_repair"
TASK614 = ROOT / "data/artifacts/task_614_p0_intelligence_source_attachment"
OUT_DIR = ROOT / "data/artifacts/task_1131_1140_evidence_fill"

AUTHORITY = "DIAGNOSTIC_EVIDENCE_FILL_ONLY"
HISTORICAL_END_TS = "2026-03-31T23:59:59+00:00"
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


def mtime_utc(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.fromisoformat(value[:10] + "T00:00:00+00:00")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def max_ts(*values: str) -> str:
    parsed = [parse_dt(value) for value in values if value]
    parsed = [value for value in parsed if value is not None]
    if not parsed:
        return ""
    return max(parsed).isoformat()


def task1131_pit_source_candidate_inventory() -> list[dict[str, object]]:
    candidates = [
        ("static_10x7_theme_universe", RAW / "theme_universe_10x7.csv", "reference_only_not_pit_membership"),
        ("alpaca_active_us_equity_universe", RAW / "alpaca_active_us_equity_universe.csv", "current_tradability_not_historical_theme_membership"),
        ("task881_decision_symbol_spine", TASK881 / "universe_membership_panel.csv", "audit_spine_not_membership_source"),
        ("task894_missing_source_queue", ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed/missing_source_acquisition_queue.csv", "acquisition_queue_not_membership_source"),
        ("task895_raw_attachment_queue", ROOT / "data/artifacts/task_895_l1_source_attachment/raw_source_attachment_acquisition_queue.csv", "source_attachment_queue_not_membership_source"),
    ]
    rows = []
    for idx, (name, path, state) in enumerate(candidates, start=1):
        exists = path.exists()
        rows.append(
            {
                "task_id": "Task1131",
                "pit_candidate_id": f"PITCAND1131-{idx:03d}",
                "candidate_name": name,
                "raw_source_path": rel(path) if exists else path.as_posix(),
                "source_hash": file_sha256(path) if exists else "",
                "received_ts": mtime_utc(path) if exists else "",
                "candidate_state": state,
                "pit_source_candidate": "0",
                "block_reason": "not_row_level_historical_membership_evidence",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1132_pit_source_timestamp_hash_ledger(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(candidates, start=1):
        rows.append(
            {
                "task_id": "Task1132",
                "pit_source_timestamp_id": f"PITTS1132-{idx:03d}",
                "pit_candidate_id": row["pit_candidate_id"],
                "raw_source_path": row["raw_source_path"],
                "source_hash": row["source_hash"],
                "published_ts": "",
                "received_ts": row["received_ts"],
                "available_to_brain_ts": row["received_ts"],
                "source_time_complete_flag": "0",
                "source_hash_verified_flag": "1" if row["source_hash"] else "0",
                "pit_timestamp_state": "blocked_missing_published_and_effective_membership_times",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1133_pit_membership_event_candidates(membership_spine: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(membership_spine, start=1):
        rows.append(
            {
                "task_id": "Task1133",
                "membership_event_candidate_id": f"PITEVT1133-{idx:07d}",
                "decision_id": row["decision_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "universe_id": row["universe_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "role": row["role"],
                "membership_event_type": "candidate_missing_source",
                "effective_start_ts": "",
                "effective_end_ts": "",
                "published_ts": "",
                "received_ts": "",
                "available_to_brain_ts": "",
                "raw_source_path": "",
                "source_hash": "",
                "membership_event_state": "blocked_missing_row_level_pit_source",
                "pit_membership_pass": "0",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1134_pit_membership_pass_recheck(events: list[dict[str, object]], features: list[dict[str, str]]) -> list[dict[str, object]]:
    event_by_key = {(str(row["symbol"]), str(row["theme"]), str(row["decision_asof_ts"])): row for row in events}
    rows = []
    for idx, row in enumerate(features, start=1):
        event = event_by_key.get((row["symbol"], row["theme"], row["decision_asof_ts"]))
        pass_flag = "1" if event and event["pit_membership_pass"] == "1" else "0"
        rows.append(
            {
                "task_id": "Task1134",
                "pit_recheck_id": f"PITRECHECK1134-{idx:07d}",
                "trade_spec_id": row["trade_spec_id"],
                "decision_asof_ts": row["decision_asof_ts"],
                "entry_date": row["entry_date"],
                "split_id": row["split_id"],
                "symbol": row["symbol"],
                "theme": row["theme"],
                "sec_source_time_pass": row["source_time_pass"],
                "pit_membership_pass": pass_flag,
                "pit_recheck_state": "pit_pass" if pass_flag == "1" else "blocked_missing_row_level_pit_source",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1135_nonsec_raw_timestamp_recovery() -> list[dict[str, object]]:
    rows = []
    p0_path = TASK614 / "p0_intelligence_event_store.csv"
    task636_path = RAW / "task_636_content_source_text/task_636_source_text_checkpoint.csv"
    if p0_path.exists():
        for row in read_csv(p0_path):
            if row["source_name"] == "sec_company_submissions":
                continue
            raw_family_dir = RAW / "intelligence_task614"
            raw_files = list(raw_family_dir.rglob("*")) if raw_family_dir.exists() else []
            raw_files = [path for path in raw_files if path.is_file() and row["source_name"].split("_")[0].lower() in path.name.lower()]
            raw_path = raw_files[0] if raw_files else p0_path
            received = row.get("received_at") or mtime_utc(raw_path)
            published = row.get("published_at") or row.get("event_timestamp_utc") or row.get("event_date")
            available = max_ts(published, row.get("tradable_after_ts", ""), received)
            rows.append(
                {
                    "task_id": "Task1135",
                    "recovered_event_id": f"TASK614|{row['event_id']}",
                    "source_family": "intelligence_task614",
                    "source_name": row["source_name"],
                    "event_category": row["event_category"],
                    "event_title": row["event_title"],
                    "source_url": row["source_url"],
                    "symbol_tags": row["symbol_tags"],
                    "theme_tags": row["theme_tags"],
                    "policy_tags": row["policy_tags"],
                    "event_ts": row.get("event_timestamp_utc") or row.get("event_date"),
                    "published_ts": published,
                    "received_ts": received,
                    "available_to_brain_ts": available,
                    "raw_source_path": rel(raw_path),
                    "source_hash": file_sha256(raw_path),
                    "official_source_flag": row["official_source_flag"],
                    "time_precision": row["time_precision"],
                    "source_time_state": "historical_blocked_by_late_capture" if parse_dt(available) and parse_dt(available) > parse_dt(HISTORICAL_END_TS) else "source_time_candidate",
                    "historical_dynamic_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
    if task636_path.exists():
        for row in read_csv(task636_path):
            if row.get("source_name") == "sec_company_submissions":
                continue
            raw_path = ROOT / row["raw_text_path"] if row.get("raw_text_path") else task636_path
            received = mtime_utc(raw_path) if raw_path.exists() else ""
            rows.append(
                {
                    "task_id": "Task1135",
                    "recovered_event_id": f"TASK636|{row['event_id']}",
                    "source_family": "task_636_content_source_text",
                    "source_name": row["source_name"],
                    "event_category": row["event_category"],
                    "event_title": row["event_title"],
                    "source_url": row["source_url"],
                    "symbol_tags": row["symbol_tags"],
                    "theme_tags": row["theme_tags"],
                    "policy_tags": row["policy_tags"],
                    "event_ts": row["event_date"],
                    "published_ts": "",
                    "received_ts": received,
                    "available_to_brain_ts": received,
                    "raw_source_path": row["raw_text_path"],
                    "source_hash": row["source_text_hash"],
                    "official_source_flag": "1" if "whitehouse" in row["source_name"].lower() else "0",
                    "time_precision": "date_only_not_source_time",
                    "source_time_state": "blocked_missing_published_ts",
                    "historical_dynamic_use_allowed": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def task1136_macro_vintage_recheck() -> list[dict[str, object]]:
    path = RAW / "macro_fred/task_655/fred_macro_release_repaired_feature_panel.csv"
    rows = []
    if not path.exists():
        return rows
    source_hash = file_sha256(path)
    for idx, row in enumerate(read_csv(path), start=1):
        received = mtime_utc(path)
        published = row["release_ts_utc"]
        available = max_ts(published, row["tradable_after_ts_utc"], received)
        rows.append(
            {
                "task_id": "Task1136",
                "macro_vintage_recheck_id": f"MACROVINT1136-{idx:07d}",
                "series_id": row["series_id"],
                "category": row["category"],
                "observation_date": row["observation_date"],
                "published_ts": published,
                "received_ts": received,
                "available_to_brain_ts": available,
                "raw_source_path": rel(path),
                "source_hash": source_hash,
                "latest_vintage_only_flag": row["latest_vintage_only_flag"],
                "exact_release_calendar_verified_flag": row["exact_release_calendar_verified_flag"],
                "vintage_asof_certified_flag": row["vintage_asof_certified_flag"],
                "macro_vintage_pass": "0",
                "block_reason": "latest_vintage_or_late_capture_or_missing_vintage_asof_certification",
                "historical_dynamic_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1137_nonsec_asof_event_panel(recovered: list[dict[str, object]], macro: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(recovered, start=1):
        published = str(row.get("published_ts", ""))
        received = str(row.get("received_ts", ""))
        available = str(row.get("available_to_brain_ts", ""))
        complete = bool(published and received and available and row.get("source_hash") and row.get("raw_source_path"))
        historical = bool(complete and parse_dt(available) and parse_dt(available) <= parse_dt(HISTORICAL_END_TS))
        rows.append(
            {
                "task_id": "Task1137",
                "nonsec_asof_event_id": f"NONSECASOF1137-{idx:07d}",
                "source_event_id": row["recovered_event_id"],
                "source_family": row["source_family"],
                "event_category": row["event_category"],
                "symbol_tags": row["symbol_tags"],
                "theme_tags": row["theme_tags"],
                "policy_tags": row["policy_tags"],
                "published_ts": published,
                "received_ts": received,
                "available_to_brain_ts": available,
                "raw_source_path": row["raw_source_path"],
                "source_hash": row["source_hash"],
                "source_time_complete_flag": "1" if complete else "0",
                "historical_dynamic_use_allowed": "1" if historical else "0",
                "block_reason": "" if historical else "late_capture_or_missing_published_received_available_or_tags",
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    offset = len(rows)
    for idx, row in enumerate(macro, start=1):
        rows.append(
            {
                "task_id": "Task1137",
                "nonsec_asof_event_id": f"NONSECASOF1137-{offset + idx:07d}",
                "source_event_id": row["macro_vintage_recheck_id"],
                "source_family": "macro_fred",
                "event_category": row["category"],
                "symbol_tags": "",
                "theme_tags": "",
                "policy_tags": "macro_context",
                "published_ts": row["published_ts"],
                "received_ts": row["received_ts"],
                "available_to_brain_ts": row["available_to_brain_ts"],
                "raw_source_path": row["raw_source_path"],
                "source_hash": row["source_hash"],
                "source_time_complete_flag": "1",
                "historical_dynamic_use_allowed": "0",
                "block_reason": row["block_reason"],
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1138_dynamic_event_l1_l4_shadow_bridge(events: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for idx, row in enumerate(events, start=1):
        if row["source_time_complete_flag"] != "1":
            bridge_state = "blocked_missing_source_time"
        elif row["historical_dynamic_use_allowed"] != "1":
            bridge_state = "shadow_only_late_or_uncertified_source"
        else:
            bridge_state = "l1_l4_shadow_candidate"
        rows.append(
            {
                "task_id": "Task1138",
                "shadow_bridge_id": f"SHADOWBRIDGE1138-{idx:07d}",
                "source_event_id": row["source_event_id"],
                "source_family": row["source_family"],
                "event_category": row["event_category"],
                "symbol_tags": row["symbol_tags"],
                "theme_tags": row["theme_tags"],
                "l1_fact_state": bridge_state,
                "l2_meaning_state": "not_promoted",
                "l3_relation_state": "not_promoted",
                "l4_thesis_effect": "not_promoted",
                "historical_dynamic_use_allowed": row["historical_dynamic_use_allowed"],
                "selection_use_allowed": "0",
                "replay_use_allowed": "0",
                "authority": AUTHORITY,
            }
        )
    return rows


def task1139_policy_preregistration_readiness(fresh: list[dict[str, str]], exposure: list[dict[str, str]], pit_recheck: list[dict[str, object]], events: list[dict[str, object]]) -> list[dict[str, object]]:
    pit_pass = sum(1 for row in pit_recheck if row["pit_membership_pass"] == "1")
    dynamic_pass = sum(1 for row in events if row["historical_dynamic_use_allowed"] == "1")
    return [
        {
            "task_id": "Task1139",
            "policy_gate_id": "POLICYREADY1139-001",
            "gate_name": "pit_nonsec_reentry_policy_preregistration_readiness",
            "pit_pass_rows": pit_pass,
            "historical_dynamic_use_rows": dynamic_pass,
            "fresh_entry_candidate_rows": sum(1 for row in fresh if row["fresh_entry_candidate_flag"] == "1"),
            "stale_reentry_blocked_rows": sum(1 for row in fresh if row["stale_reentry_flag"] == "1"),
            "continuous_exposure_episode_rows": len(exposure),
            "policy_preregistration_allowed": "1" if pit_pass > 0 and dynamic_pass > 0 else "0",
            "blocked_reason": "" if pit_pass > 0 and dynamic_pass > 0 else "pit_or_historical_nonsec_dynamic_evidence_still_zero",
            "replay_executed": "0",
            "selection_promoted": "0",
            "authority": AUTHORITY,
        }
    ]


def closeout(pit_recheck: list[dict[str, object]], asof_events: list[dict[str, object]], readiness: list[dict[str, object]]) -> dict[str, object]:
    pit_pass = sum(1 for row in pit_recheck if row["pit_membership_pass"] == "1")
    complete_nonsec = sum(1 for row in asof_events if row["source_time_complete_flag"] == "1")
    dynamic_pass = sum(1 for row in asof_events if row["historical_dynamic_use_allowed"] == "1")
    return {
        "task_id": "Task1131-1140",
        "verdict": "go_for_policy_preregistration_only" if readiness[0]["policy_preregistration_allowed"] == "1" else "blocked_continue_source_repair",
        "pit_feature_rows_audited": len(pit_recheck),
        "pit_feature_pass_rows": pit_pass,
        "pit_feature_blocked_rows": len(pit_recheck) - pit_pass,
        "nonsec_asof_event_rows": len(asof_events),
        "nonsec_source_time_complete_rows": complete_nonsec,
        "historical_dynamic_use_rows": dynamic_pass,
        "policy_preregistration_allowed": readiness[0]["policy_preregistration_allowed"],
        "replay_executed": "0",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "acquire_true_pit_membership_sources_and_historical_received_timestamps_before_policy_preregistration",
        "authority": AUTHORITY,
    }


def build() -> dict[str, object]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    features = read_csv(TASK1081 / "task1082_sec_asof_adapter_feature_panel.csv")
    membership_spine = read_csv(TASK881 / "universe_membership_panel.csv")
    fresh = read_csv(TASK1121 / "task1128_fresh_entry_candidate_ledger.csv")
    exposure = read_csv(TASK1121 / "task1128_continuous_exposure_episode_ledger.csv")

    t1131 = task1131_pit_source_candidate_inventory()
    t1132 = task1132_pit_source_timestamp_hash_ledger(t1131)
    t1133 = task1133_pit_membership_event_candidates(membership_spine)
    t1134 = task1134_pit_membership_pass_recheck(t1133, features)
    t1135 = task1135_nonsec_raw_timestamp_recovery()
    t1136 = task1136_macro_vintage_recheck()
    t1137 = task1137_nonsec_asof_event_panel(t1135, t1136)
    t1138 = task1138_dynamic_event_l1_l4_shadow_bridge(t1137)
    t1139 = task1139_policy_preregistration_readiness(fresh, exposure, t1134, t1137)
    t1140 = closeout(t1134, t1137, t1139)

    write_csv(OUT_DIR / "task1131_pit_source_candidate_inventory.csv", t1131)
    write_csv(OUT_DIR / "task1132_pit_source_timestamp_hash_ledger.csv", t1132)
    write_csv(OUT_DIR / "task1133_pit_membership_event_candidates.csv", t1133)
    write_csv(OUT_DIR / "task1134_pit_membership_pass_recheck.csv", t1134)
    write_csv(OUT_DIR / "task1135_nonsec_raw_timestamp_recovery.csv", t1135)
    write_csv(OUT_DIR / "task1136_macro_vintage_recheck.csv", t1136)
    write_csv(OUT_DIR / "task1137_nonsec_asof_event_panel.csv", t1137)
    write_csv(OUT_DIR / "task1138_dynamic_event_l1_l4_shadow_bridge.csv", t1138)
    write_csv(OUT_DIR / "task1139_policy_preregistration_readiness.csv", t1139)
    write_csv(OUT_DIR / "task1140_evidence_fill_closeout.csv", [t1140])
    (OUT_DIR / "task1140_evidence_fill_closeout.json").write_text(json.dumps(t1140, indent=2), encoding="utf-8")
    return t1140


def main() -> None:
    summary = build()
    print(
        "[TRADER_BRAIN_1131_1140_EVIDENCE_FILL_OK] "
        f"verdict={summary['verdict']} pit_pass={summary['pit_feature_pass_rows']}/{summary['pit_feature_rows_audited']} "
        f"nonsec_complete={summary['nonsec_source_time_complete_rows']}/{summary['nonsec_asof_event_rows']} "
        f"historical_dynamic={summary['historical_dynamic_use_rows']} replay={summary['replay_executed']}"
    )


if __name__ == "__main__":
    main()
