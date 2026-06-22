from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task614_p0_intelligence_source_attachment import (
    ARTIFACT_DIR as TASK614_ARTIFACT_DIR,
    CIK_MAP,
    DEFENSE_RSS,
    OFAC_RECENT_ACTIONS,
    RAW_DIR as TASK614_RAW_DIR,
    RAW_SEC_DIR,
    SEC_CURRENT_FEEDS,
    SEC_USER_AGENT,
    TASK608K_PANEL,
    TASK608K_TAXONOMY,
    WHITEHOUSE_LISTING_BASES,
    WHITEHOUSE_RSS,
    build_task614_p0_intelligence_source_attachment,
    build_source_coverage,
    fetch_text,
    load_or_fetch_geopolitical_events,
    load_or_fetch_sec_intelligence_events,
    load_or_fetch_whitehouse_events,
    load_symbol_ciks,
    load_task608k_panel,
    normalize_event_frame,
    parse_ofac_recent_actions,
    parse_rss_events,
    parse_sec_atom_feed,
    parse_whitehouse_listing,
)
from .paper_runtime_common import append_registry_rows, write_csv, write_task_report


TASK_ID = "Task615"
REPORT_DIR = Path("docs/reports/task_615_realtime_intelligence_sidecar_runtime_integration")
TASK614_REPORT_DIR = Path("docs/reports/task_614_p0_intelligence_source_attachment")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _env_true(name: str, default: str = "0") -> bool:
    value = os.environ.get(name, default)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _int_env(name: str, default: int) -> int:
    try:
        return int(str(os.environ.get(name, str(default))).strip())
    except ValueError:
        return default


def sidecar_enabled() -> bool:
    return _env_true("TRADING_INTELLIGENCE_SIDECAR_ENABLED", "0")


def _latest_status_path(out_dir: Path) -> Path:
    return out_dir / "latest_runtime_intelligence_sidecar_status.csv"


def _read_latest_status(out_dir: Path) -> dict[str, Any]:
    path = _latest_status_path(out_dir)
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    if frame.empty:
        return {}
    return frame.iloc[-1].to_dict()


def _lock_path(out_dir: Path) -> Path:
    return out_dir / ".runtime_intelligence_sidecar.lock"


def _acquire_sidecar_lock(out_dir: Path) -> bool:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = _lock_path(out_dir)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            created = datetime.fromisoformat(str(payload.get("created_at_utc", "")).replace("Z", "+00:00"))
            if (datetime.now(UTC) - created).total_seconds() > 3600:
                path.unlink(missing_ok=True)
            else:
                return False
        except Exception:
            return False
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        payload = {"pid": os.getpid(), "created_at_utc": _utc_now()}
        os.write(fd, json.dumps(payload, ensure_ascii=True).encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _release_sidecar_lock(out_dir: Path) -> None:
    _lock_path(out_dir).unlink(missing_ok=True)


def _recent_enough(latest: dict[str, Any], now: datetime, min_interval_seconds: int) -> bool:
    finished = str(latest.get("finished_at_utc") or "").strip()
    if not finished:
        return False
    try:
        finished_dt = datetime.fromisoformat(finished.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (now - finished_dt).total_seconds() < min_interval_seconds


def _existing_event_store_rows(artifact_dir: Path) -> int:
    path = artifact_dir / "p0_intelligence_event_store.csv"
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path, usecols=["event_id"])))
    except Exception:
        return 0


def _collect_source_store_only(
    *,
    fetch_sources: bool,
    raw_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    panel = load_task608k_panel(TASK608K_PANEL, TASK608K_TAXONOMY)
    symbols = sorted(panel["symbol"].astype(str).unique().tolist())
    symbol_ciks = load_symbol_ciks(CIK_MAP, symbols)
    political, political_status = load_or_fetch_whitehouse_events(raw_dir, panel, fetch_sources=fetch_sources)
    geopolitical, geopolitical_status = load_or_fetch_geopolitical_events(raw_dir, panel, fetch_sources=fetch_sources)
    sec_events, sec_status = load_or_fetch_sec_intelligence_events(symbol_ciks, RAW_SEC_DIR, raw_dir, fetch_sources=fetch_sources)
    events = pd.concat([political, geopolitical, sec_events], ignore_index=True)
    if not events.empty:
        events = events.sort_values(["event_date", "source_lane", "event_title"], kind="stable").reset_index(drop=True)
    coverage = build_source_coverage(political, geopolitical, sec_events, political_status, geopolitical_status, sec_status, symbols)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(artifact_dir / "p0_intelligence_event_store.csv", index=False)
    coverage.to_csv(artifact_dir / "source_collection_status.csv", index=False)
    write_manifest(artifact_dir, artifact_dir / "artifact_manifest.csv")
    attached = int(coverage["coverage_status"].eq("ATTACHED").sum()) if "coverage_status" in coverage.columns else 0
    return {
        "event_store_rows": int(len(events)),
        "attached_source_lanes": attached,
    }


def _collect_runtime_source_snapshot(
    *,
    fetch_sources: bool,
    raw_dir: Path,
    artifact_dir: Path,
) -> dict[str, Any]:
    collection_received_at = _utc_now()
    existing_path = artifact_dir / "p0_intelligence_event_store.csv"
    existing = pd.read_csv(existing_path) if existing_path.exists() else pd.DataFrame()
    rows: list[pd.DataFrame] = []
    status_rows: list[dict[str, Any]] = []
    raw_dir.mkdir(parents=True, exist_ok=True)

    for source_name, base_url in WHITEHOUSE_LISTING_BASES.items():
        raw_path = raw_dir / "whitehouse" / f"{source_name}_page_001.html"
        status = fetch_text(base_url, raw_path, fetch_sources=fetch_sources)
        parsed = parse_whitehouse_listing(raw_path.read_text(encoding="utf-8"), source_name) if raw_path.exists() else []
        frame = normalize_event_frame(pd.DataFrame(parsed))
        rows.append(frame)
        status_rows.append(_status_row("trump_major_person_political_statements", source_name, status, raw_path, len(frame)))

    for source_name, url in WHITEHOUSE_RSS.items():
        raw_path = raw_dir / "whitehouse" / f"{source_name}.xml"
        status = fetch_text(url, raw_path, fetch_sources=fetch_sources)
        parsed = parse_rss_events(raw_path, source_name, "trump_major_person_political_statements") if raw_path.exists() else []
        frame = normalize_event_frame(pd.DataFrame(parsed))
        rows.append(frame)
        status_rows.append(_status_row("trump_major_person_political_statements", source_name, status, raw_path, len(frame)))

    raw_path = raw_dir / "geopolitical" / "ofac_recent_actions_page_000.html"
    status = fetch_text(OFAC_RECENT_ACTIONS, raw_path, fetch_sources=fetch_sources)
    parsed = parse_ofac_recent_actions(raw_path.read_text(encoding="utf-8"), 0) if raw_path.exists() else []
    frame = normalize_event_frame(pd.DataFrame(parsed))
    rows.append(frame)
    status_rows.append(_status_row("war_geopolitical_conflict_events", "ofac_recent_actions", status, raw_path, len(frame)))

    raw_path = raw_dir / "geopolitical" / "defense_rss.xml"
    status = fetch_text(DEFENSE_RSS, raw_path, fetch_sources=fetch_sources)
    parsed = parse_rss_events(raw_path, "defense_rss", "war_geopolitical_conflict_events") if raw_path.exists() else []
    frame = normalize_event_frame(pd.DataFrame(parsed))
    rows.append(frame)
    status_rows.append(_status_row("war_geopolitical_conflict_events", "defense_rss", status, raw_path, len(frame)))

    headers = {"User-Agent": SEC_USER_AGENT}
    for source_name, url in SEC_CURRENT_FEEDS.items():
        raw_path = raw_dir / "sec_current_feeds" / f"{source_name}.xml"
        status = fetch_text(url, raw_path, fetch_sources=fetch_sources, headers=headers)
        parsed = parse_sec_atom_feed(raw_path, source_name) if raw_path.exists() else []
        frame = normalize_event_frame(pd.DataFrame(parsed))
        rows.append(frame)
        status_rows.append(_status_row("institution_investment_actions", source_name, status, raw_path, len(frame)))

    new_events = normalize_event_frame(pd.concat(rows, ignore_index=True) if rows else pd.DataFrame())
    new_events = _stamp_runtime_temporal_contract(new_events, received_at=collection_received_at)
    merged = normalize_event_frame(pd.concat([new_events, existing], ignore_index=True) if not existing.empty else new_events)
    status_frame = pd.DataFrame(status_rows)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    merged.to_csv(existing_path, index=False)
    status_frame.to_csv(artifact_dir / "source_collection_status.csv", index=False)
    write_manifest(artifact_dir, artifact_dir / "artifact_manifest.csv")
    attached = int(merged[merged["source_lane"].astype(str).ne("")]["source_lane"].nunique()) if not merged.empty else 0
    return {
        "event_store_rows": int(len(merged)),
        "attached_source_lanes": attached,
        "new_event_rows": int(len(new_events)),
    }


def _status_row(source_lane: str, source_name: str, status: str, raw_path: Path, event_count: int) -> dict[str, Any]:
    return {
        "source_lane": source_lane,
        "priority": "P0",
        "coverage_status": "ATTACHED" if event_count else "SOURCE_BLOCKED",
        "source_name": source_name,
        "status": status,
        "raw_path": raw_path.as_posix(),
        "event_count": event_count,
        "backtest_use": "runtime collection only",
        "blocked_reason": "" if event_count else f"No runtime events parsed; status={status}",
    }


def _stamp_runtime_temporal_contract(events: pd.DataFrame, *, received_at: str) -> pd.DataFrame:
    frame = normalize_event_frame(events).copy()
    if frame.empty:
        return frame
    missing_received = frame["received_at"].astype(str).str.strip().eq("")
    frame.loc[missing_received, "received_at"] = received_at
    missing_published = frame["published_at"].astype(str).str.strip().eq("")
    has_event_timestamp = frame["event_timestamp_utc"].astype(str).str.strip().ne("")
    frame.loc[missing_published & has_event_timestamp, "published_at"] = frame.loc[
        missing_published & has_event_timestamp, "event_timestamp_utc"
    ]
    missing_tradable = frame["tradable_after_ts"].astype(str).str.strip().eq("")
    has_published = frame["published_at"].astype(str).str.strip().ne("")
    frame.loc[missing_tradable & has_published, "tradable_after_ts"] = frame.loc[
        missing_tradable & has_published, "published_at"
    ]
    missing_tradable = frame["tradable_after_ts"].astype(str).str.strip().eq("")
    frame.loc[missing_tradable, "tradable_after_ts"] = frame.loc[missing_tradable, "received_at"]
    return normalize_event_frame(frame)


def _write_status(out_dir: Path, row: dict[str, Any]) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = pd.DataFrame([row])
    history_path = out_dir / "runtime_intelligence_sidecar_status.csv"
    if history_path.exists():
        history = pd.concat([pd.read_csv(history_path), latest], ignore_index=True)
    else:
        history = latest.copy()
    history.to_csv(history_path, index=False, encoding="utf-8-sig")
    latest.to_csv(_latest_status_path(out_dir), index=False, encoding="utf-8-sig")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    write_csv(TASK614_REPORT_DIR, "latest_runtime_intelligence_sidecar_status.csv", latest)
    return {
        "runtime_intelligence_sidecar_status.csv": history,
        "latest_runtime_intelligence_sidecar_status.csv": latest,
    }


def run_task615_realtime_intelligence_sidecar(
    *,
    fetch_sources: bool | None = None,
    force: bool = False,
    out_dir: Path = REPORT_DIR,
    artifact_dir: Path = TASK614_ARTIFACT_DIR,
    raw_dir: Path = TASK614_RAW_DIR,
) -> dict[str, pd.DataFrame]:
    now = datetime.now(UTC)
    started = now.isoformat().replace("+00:00", "Z")
    min_interval_seconds = max(0, _int_env("TRADING_INTELLIGENCE_SIDECAR_MIN_INTERVAL_SEC", 900))
    should_fetch = _env_true("TRADING_INTELLIGENCE_SIDECAR_FETCH", "1") if fetch_sources is None else bool(fetch_sources)
    source_store_only = _env_true("TRADING_INTELLIGENCE_SIDECAR_SOURCE_STORE_ONLY", "1")

    row: dict[str, Any] = {
        "task_id": TASK_ID,
        "started_at_utc": started,
        "finished_at_utc": "",
        "decision_status": "",
        "enabled_flag": int(sidecar_enabled()),
        "fetch_sources_flag": int(should_fetch),
        "source_store_only_flag": int(source_store_only),
        "force_flag": int(force),
        "min_interval_seconds": min_interval_seconds,
        "event_store_rows": 0,
        "attached_source_lanes": 0,
        "best_p0_event_scenario": "",
        "p0_event_diagnostic_pass_flag": 0,
        "trading_promotion_pass_flag": 0,
        "sidecar_trade_signal_used_flag": 0,
        "strategy_acceptance_status": "NOT_ACCEPTED",
        "real_capital_status": "FORBIDDEN",
        "canonical_event_store": str(artifact_dir / "p0_intelligence_event_store.csv"),
        "exception": "",
    }
    if not row["enabled_flag"]:
        row["decision_status"] = "INTELLIGENCE_SIDECAR_DISABLED"
        row["event_store_rows"] = _existing_event_store_rows(artifact_dir)
        row["finished_at_utc"] = _utc_now()
        return _write_status(out_dir, row)

    latest = _read_latest_status(out_dir)
    if not force and latest and _recent_enough(latest, now, min_interval_seconds):
        row.update(latest)
        row["started_at_utc"] = started
        row["finished_at_utc"] = _utc_now()
        row["decision_status"] = "INTELLIGENCE_SIDECAR_SKIPPED_RECENT"
        row["sidecar_trade_signal_used_flag"] = 0
        return _write_status(out_dir, row)

    if not _acquire_sidecar_lock(out_dir):
        row["decision_status"] = "INTELLIGENCE_SIDECAR_BUSY"
        row["event_store_rows"] = _existing_event_store_rows(artifact_dir)
        row["finished_at_utc"] = _utc_now()
        return _write_status(out_dir, row)

    try:
        runtime_raw_dir = raw_dir / "runtime_snapshots" / now.strftime("%Y%m%dT%H%M%SZ")
        if source_store_only:
            collection = _collect_runtime_source_snapshot(
                fetch_sources=should_fetch,
                raw_dir=runtime_raw_dir,
                artifact_dir=artifact_dir,
            )
            decision = {
                "attached_source_lanes": collection["attached_source_lanes"],
                "best_p0_event_scenario": "",
                "p0_event_diagnostic_pass_flag": 0,
                "trading_promotion_pass_flag": 0,
            }
            event_store_rows = int(collection["event_store_rows"])
        else:
            artifacts = build_task614_p0_intelligence_source_attachment(
                raw_dir=runtime_raw_dir,
                artifact_dir=artifact_dir,
                out_dir=TASK614_REPORT_DIR,
                fetch_sources=should_fetch,
            )
            decision = artifacts["task_614_decision"].iloc[0].to_dict()
            event_store_rows = int(len(artifacts["p0_intelligence_events"]))
        row.update(
            {
                "decision_status": "INTELLIGENCE_SIDECAR_COLLECTION_OK",
                "event_store_rows": event_store_rows,
                "attached_source_lanes": int(decision.get("attached_source_lanes", 0)),
                "best_p0_event_scenario": decision.get("best_p0_event_scenario", ""),
                "p0_event_diagnostic_pass_flag": int(decision.get("p0_event_diagnostic_pass_flag", 0)),
                "trading_promotion_pass_flag": int(decision.get("trading_promotion_pass_flag", 0)),
                "sidecar_trade_signal_used_flag": 0,
            }
        )
    except Exception as exc:
        row["decision_status"] = "INTELLIGENCE_SIDECAR_COLLECTION_ERROR"
        row["event_store_rows"] = _existing_event_store_rows(artifact_dir)
        row["exception"] = str(exc)
    finally:
        _release_sidecar_lock(out_dir)

    row["finished_at_utc"] = _utc_now()
    artifacts_out = _write_status(out_dir, row)
    if row["decision_status"] != "INTELLIGENCE_SIDECAR_DISABLED":
        write_task_report(
            out_dir,
            "task_615_realtime_intelligence_sidecar_runtime_integration.md",
            title="Task615 - Realtime Intelligence Sidecar Runtime Integration",
            decision_summary=[
                f"decision_status={row['decision_status']}",
                f"event_store_rows={row['event_store_rows']}",
                "sidecar_trade_signal_used_flag=0",
                "strategy_acceptance_status=NOT_ACCEPTED",
                "real_capital_status=FORBIDDEN",
            ],
            quant_lines=[
                "Task615 runs the Task614 source collector as a runtime sidecar before or beside paper/autotrade execution.",
                "The sidecar writes a persistent event store and status artifacts only; no source event is passed into order submission or position sizing.",
                "Cadence is controlled by TRADING_INTELLIGENCE_SIDECAR_MIN_INTERVAL_SEC to avoid slowing the trading loop.",
            ],
            decision_maker_lines=[
                "The trading loop now has a separate intelligence collector.",
                "It stores news/filing/policy style evidence for later backtests.",
                "It does not make trades and does not approve the strategy.",
            ],
        )
        append_registry_rows(
            [
                {
                    "task_id": TASK_ID,
                    "title": "Realtime Intelligence Sidecar Runtime Integration",
                    "owner_team": "Data & Market Microstructure",
                    "status": "Accepted",
                    "canonical_state": "active",
                    "strategy_acceptance": "diagnostic-only",
                    "data_readiness": "runtime-source-sidecar",
                    "parent_task": "Task614",
                    "key_report": str(out_dir / "task_615_realtime_intelligence_sidecar_runtime_integration.md"),
                    "key_decision": str(out_dir / "latest_runtime_intelligence_sidecar_status.csv"),
                    "key_artifacts": str(out_dir),
                    "validation_command": "python -m unittest tests.test_task615_realtime_intelligence_sidecar tests.test_task588_kis_paper_market_hours_runtime_loop",
                    "notes": "Runs Task614 source collection beside paper/autotrade loops; output is collection-only and never a trading signal.",
                }
            ]
        )
    return artifacts_out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    fetch_sources = None
    if args.fetch:
        fetch_sources = True
    if args.no_fetch:
        fetch_sources = False
    os.environ["TRADING_INTELLIGENCE_SIDECAR_ENABLED"] = os.environ.get("TRADING_INTELLIGENCE_SIDECAR_ENABLED", "1")
    artifacts = run_task615_realtime_intelligence_sidecar(fetch_sources=fetch_sources, force=args.force)
    print(artifacts["latest_runtime_intelligence_sidecar_status.csv"].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
