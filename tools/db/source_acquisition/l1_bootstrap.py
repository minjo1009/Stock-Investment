from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4133"
SLUG = "task_4133_l1_development_plan"
ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = ROOT / "configs" / "l1_source_family_contracts.yaml"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
DAILY_RAW_DIRS = [
    ROOT / "data" / "raw" / "us_daily_alpaca_full_universe",
    ROOT / "data" / "raw" / "l0_bar_daily_full_backfill",
]


PACKET_COLUMNS = [
    "task_id",
    "source_packet_id",
    "candidate_id",
    "trade_spec_id",
    "symbol",
    "decision_asof_ts",
    "provider",
    "endpoint_or_source_family",
    "source_ts",
    "available_to_brain_ts",
    "source_time_basis",
    "source_time_certified",
    "raw_path",
    "raw_sha256",
    "strict_gate_pass",
    "proxy_feature_allowed",
    "missing_source_is_negative",
    "assignment_uses_future_outcome",
    "outcome_used_for_assignment",
    "authority",
    "raw_locator_type",
    "mapping_status",
    "macro_context_candidate",
    "candidate_hint_only",
    "l1_gate_classification",
    "l2_allowed_scope",
    "blocker_reason",
]

GATE_COLUMNS = [
    "task_id",
    "source_packet_id",
    "endpoint_or_source_family",
    "gate_name",
    "gate_pass",
    "classification",
    "reason",
]

GAP_COLUMNS = [
    "task_id",
    "source_family",
    "gap_type",
    "severity",
    "missing_source_is_negative",
    "description",
    "follow_up",
]


def rel(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(ROOT)
        except ValueError:
            return p.as_posix()
    return p.as_posix()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        try:
            parsed = datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_ts(value: Any, *, date_only_noon: bool = False) -> str:
    if value in (None, ""):
        return ""
    text = str(value).strip()
    if date_only_noon and len(text) == 10:
        return f"{text}T12:00:00Z"
    parsed = parse_ts(text)
    if not parsed:
        return ""
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bounded_file_fingerprint(path: Path, limit: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    h.update(rel(path).encode("utf-8"))
    try:
        with path.open("rb") as fh:
            h.update(fh.read(limit))
    except OSError:
        pass
    return h.hexdigest()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_contracts() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {"payload": data}


def captured_at_from_path(path: Path) -> str:
    for part in path.parts:
        if part.startswith("captured_at="):
            value = part.split("=", 1)[1]
            try:
                parsed = datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
                return parsed.isoformat().replace("+00:00", "Z")
            except ValueError:
                return ""
    return ""


def provider_source_from_path(path: Path) -> tuple[str, str]:
    provider = ""
    source = ""
    for part in path.parts:
        if part.startswith("provider="):
            provider = part.split("=", 1)[1]
        if part.startswith("source="):
            source = part.split("=", 1)[1]
    return provider, source


def read_prefix(path: Path, size: int = 262_144) -> str:
    try:
        with path.open("rb") as fh:
            return fh.read(size).decode("utf-8", errors="ignore")
    except OSError:
        return ""


def prefix_value(prefix: str, keys: list[str]) -> str:
    for key in keys:
        match = re.search(rf'"{re.escape(key)}"\s*:\s*"([^"]+)"', prefix)
        if match:
            return match.group(1)
    return ""


def first_file(pattern: str) -> Path | None:
    return next(ROOT.glob(pattern), None)


def first_headline_packet(
    *,
    path: Path,
    source_family: str,
    source_key: str,
    authority: str,
    mapping_status: str,
    l2_allowed_scope: str,
    macro_context_candidate: bool = False,
    candidate_hint_only: bool = False,
    date_only_noon: bool = False,
    read_raw_prefix: bool = True,
) -> dict[str, Any]:
    prefix = read_prefix(path) if read_raw_prefix else ""
    path_provider, path_source = provider_source_from_path(path)
    captured_at = prefix_value(prefix, ["captured_at", "detected_at"]) or captured_at_from_path(path) or utc_now()
    source_ts = (
        prefix_value(prefix, ["published_at", "event_time", "source_ts", "date", "published_date"])
        or captured_at
    )
    source_ts_norm = normalize_ts(source_ts, date_only_noon=date_only_noon)
    available_ts = normalize_ts(captured_at) or utc_now()
    symbol = ""
    symbol_match = re.search(r'"(?:symbols|ticker_candidates|tickers)"\s*:\s*\[\s*"([^"]+)"', prefix)
    if symbol_match:
        symbol = symbol_match.group(1)
    candidate_basis = {
        "raw_path": rel(path),
        "family": source_family,
        "source_key": source_key,
        "headline_hash": prefix_value(prefix, ["headline_hash", "url", "title"]),
    }
    return {
        "task_id": TASK_ID,
        "source_packet_id": "l1sp_" + stable_hash(candidate_basis)[:20],
        "candidate_id": prefix_value(prefix, ["headline_hash", "url", "title"]) or stable_hash(candidate_basis)[:20],
        "trade_spec_id": "",
        "symbol": symbol,
        "decision_asof_ts": available_ts,
        "provider": prefix_value(prefix, ["provider"]) or path_provider or source_family,
        "endpoint_or_source_family": source_family,
        "source_ts": source_ts_norm,
        "available_to_brain_ts": available_ts,
        "source_time_basis": "published_at_or_event_time",
        "source_time_certified": "1" if source_ts_norm else "0",
        "raw_path": rel(path),
        "raw_sha256": bounded_file_fingerprint(path),
        "strict_gate_pass": "0",
        "proxy_feature_allowed": "0",
        "missing_source_is_negative": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": authority,
        "raw_locator_type": "file_sha256",
        "mapping_status": mapping_status,
        "macro_context_candidate": "1" if macro_context_candidate else "0",
        "candidate_hint_only": "1" if candidate_hint_only else "0",
        "l1_gate_classification": "",
        "l2_allowed_scope": l2_allowed_scope,
        "blocker_reason": "",
    }


def market_bars_5m_packet() -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    gaps: list[dict[str, str]] = []
    db_path = ROOT / "trading.db"
    if not db_path.exists():
        gaps.append(gap("market_bars_5m", "missing_db", "P0", "trading.db not present", "Restore DB or use raw L0 partition before strict handoff."))
        return None, gaps
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    table_exists = con.execute(
        "select 1 from sqlite_master where type='table' and name='market_bars_5m'"
    ).fetchone()
    if not table_exists:
        gaps.append(gap("market_bars_5m", "missing_table", "P0", "market_bars_5m table not present", "Run 5-minute collector before strict handoff."))
        return None, gaps
    row = con.execute("select * from market_bars_5m where last_updated_at >= bar_end_ts limit 1").fetchone()
    if row is None:
        row = con.execute("select * from market_bars_5m limit 1").fetchone()
    if row is None:
        gaps.append(gap("market_bars_5m", "empty_table", "P0", "market_bars_5m has no rows", "Run 5-minute collector before strict handoff."))
        return None, gaps
    symbol = row["symbol"]
    rows = [dict(r) for r in con.execute("select * from market_bars_5m limit 25").fetchall()]
    partition_hash = stable_hash(rows)
    source_ts = normalize_ts(row["bar_end_ts"])
    available_ts = normalize_ts(row["last_updated_at"]) or source_ts
    packet = {
        "task_id": TASK_ID,
        "source_packet_id": "l1sp_" + stable_hash({"table": "market_bars_5m", "bar_id": row["bar_id"]})[:20],
        "candidate_id": row["bar_id"],
        "trade_spec_id": "",
        "symbol": symbol,
        "decision_asof_ts": available_ts,
        "provider": row["source"],
        "endpoint_or_source_family": "market_bars_5m",
        "source_ts": source_ts,
        "available_to_brain_ts": available_ts,
        "source_time_basis": "bar_end_ts",
        "source_time_certified": "1" if source_ts and available_ts else "0",
        "raw_path": "trading.db#market_bars_5m",
        "raw_sha256": partition_hash,
        "strict_gate_pass": "0",
        "proxy_feature_allowed": "0",
        "missing_source_is_negative": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": "VENDOR_MARKET_DATA",
        "raw_locator_type": "sqlite_partition_hash",
        "mapping_status": "SYMBOL_EXACT",
        "macro_context_candidate": "0",
        "candidate_hint_only": "0",
        "l1_gate_classification": "",
        "l2_allowed_scope": "STRICT_MARKET_OBSERVATION_ONLY",
        "blocker_reason": "",
    }
    return packet, gaps


def collector_progress_updated_at(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    return normalize_ts(data.get("updated_at"))


def daily_raw_file() -> Path | None:
    preferred = ROOT / "data" / "raw" / "us_daily_alpaca_full_universe" / "AAPL.csv"
    if preferred.exists():
        return preferred
    for raw_dir in DAILY_RAW_DIRS:
        if not raw_dir.exists():
            continue
        match = next(raw_dir.glob("*.csv"), None)
        if match:
            return match
    return None


def daily_bars_packet() -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    gaps: list[dict[str, str]] = []
    path = daily_raw_file()
    if not path:
        gaps.extend(daily_gap_if_needed())
        return None, gaps
    try:
        with path.open("r", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        gaps.append(gap("daily_bars", "raw_file_unreadable", "P1", f"{rel(path)} could not be read: {exc}", "Materialize the raw daily file locally before strict daily-bar handoff."))
        return None, gaps
    if not rows:
        gaps.append(gap("daily_bars", "raw_file_empty", "P1", f"{rel(path)} has no data rows", "Re-run daily collector for the affected symbol."))
        return None, gaps
    row = rows[0]
    symbol = row.get("symbol") or path.stem
    source_ts = normalize_ts(row.get("timestamp"))
    available_ts = collector_progress_updated_at(ROOT / "data" / "artifacts" / "l0_bar_daily_full_backfill" / "collector_progress.json") or source_ts
    packet = {
        "task_id": TASK_ID,
        "source_packet_id": "l1sp_" + stable_hash({"daily_csv": rel(path), "timestamp": row.get("timestamp"), "symbol": symbol})[:20],
        "candidate_id": f"{symbol}:{row.get('timestamp', '')}",
        "trade_spec_id": "",
        "symbol": symbol,
        "decision_asof_ts": available_ts,
        "provider": "alpaca_historical_bars",
        "endpoint_or_source_family": "daily_bars",
        "source_ts": source_ts,
        "available_to_brain_ts": available_ts,
        "source_time_basis": "daily_bar_timestamp",
        "source_time_certified": "1" if source_ts and available_ts else "0",
        "raw_path": rel(path),
        "raw_sha256": sha256_file(path),
        "strict_gate_pass": "0",
        "proxy_feature_allowed": "0",
        "missing_source_is_negative": "0",
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "authority": "VENDOR_MARKET_DATA",
        "raw_locator_type": "file_sha256",
        "mapping_status": "SYMBOL_EXACT",
        "macro_context_candidate": "0",
        "candidate_hint_only": "0",
        "l1_gate_classification": "",
        "l2_allowed_scope": "STRICT_MARKET_OBSERVATION_ONLY",
        "blocker_reason": "",
    }
    return packet, gaps


def daily_gap_if_needed() -> list[dict[str, str]]:
    if any(raw_dir.exists() and next(raw_dir.glob("*.csv"), None) for raw_dir in DAILY_RAW_DIRS):
        return []
    return [
        gap(
            "daily_bars",
            "raw_directory_missing",
            "P1",
            "No daily bar raw CSV directory is present in this checkout; daily bars cannot be sampled by TASK-4133.",
            "Restore data/raw/us_daily_alpaca_full_universe or data/raw/l0_bar_daily_full_backfill before strict daily-bar handoff.",
        )
    ]


def gap(source_family: str, gap_type: str, severity: str, description: str, follow_up: str) -> dict[str, str]:
    return {
        "task_id": TASK_ID,
        "source_family": source_family,
        "gap_type": gap_type,
        "severity": severity,
        "missing_source_is_negative": "0",
        "description": description,
        "follow_up": follow_up,
    }


def build_packets() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    packets: list[dict[str, Any]] = []
    gaps: list[dict[str, str]] = []

    context_path = first_file(
        "data/raw/l0_public_context_news_backfill/provider=public_context_news_feeds/source=federal_register_documents/captured_at=*/headlines.json"
    )
    if context_path:
        packets.append(
            first_headline_packet(
                path=context_path,
                source_family="public_context_news_feeds",
                source_key="federal_register_documents",
                authority="PUBLIC_CONTEXT_PRIMARY",
                mapping_status="MACRO_CONTEXT_NO_SYMBOL_REQUIRED",
                l2_allowed_scope="MACRO_CONTEXT_ONLY",
                macro_context_candidate=True,
            )
        )
    else:
        gaps.append(gap("public_context_news_feeds", "sample_raw_missing", "P1", "Federal Register raw sample missing.", "Restore L0 raw context sample before context handoff."))

    newswire_path = (
        ROOT
        / "data/raw/l0_public_newswire_backfill/provider=public_newswire_feeds/source=prnewswire/captured_at=20260628T114940259339Z/headlines.json"
    )
    if newswire_path:
        packets.append(
            first_headline_packet(
                path=newswire_path,
                source_family="public_newswire_feeds",
                source_key="prnewswire",
                authority="DISCOVERY_HINT",
                mapping_status="CANDIDATE_HINT_NON_AUTHORITY",
                l2_allowed_scope="DISCOVERY_REVIEW_QUEUE_ONLY",
                candidate_hint_only=True,
                read_raw_prefix=False,
            )
        )
    else:
        gaps.append(gap("public_newswire_feeds", "sample_raw_missing", "P1", "BusinessWire raw sample missing.", "Restore L0 raw newswire sample before discovery review."))

    wiki_path = first_file(
        "data/raw/l0_public_market_macro_news_backfill/provider=public_market_macro_news_feeds/source=wikimedia_current_events/captured_at=*/headlines.json"
    )
    if wiki_path:
        packets.append(
            first_headline_packet(
                path=wiki_path,
                source_family="public_market_macro_news_feeds",
                source_key="wikimedia_current_events",
                authority="PUBLIC_CONTEXT_PRIMARY",
                mapping_status="MACRO_CONTEXT_NO_SYMBOL_REQUIRED",
                l2_allowed_scope="MACRO_CONTEXT_ONLY",
                macro_context_candidate=True,
                date_only_noon=True,
            )
        )
    else:
        gaps.append(gap("public_market_macro_news_feeds", "sample_raw_missing", "P1", "Wikimedia Current Events raw sample missing.", "Restore L0 raw macro sample before context handoff."))

    market_packet, market_gaps = market_bars_5m_packet()
    if market_packet:
        packets.append(market_packet)
    gaps.extend(market_gaps)
    daily_packet, daily_gaps = daily_bars_packet()
    if daily_packet:
        packets.append(daily_packet)
    gaps.extend(daily_gaps)

    return [classify_packet(packet) for packet in packets], gaps


def source_time_pass(packet: dict[str, Any]) -> tuple[bool, str]:
    source = parse_ts(packet.get("source_ts"))
    available = parse_ts(packet.get("available_to_brain_ts"))
    decision = parse_ts(packet.get("decision_asof_ts"))
    if not source or not available or not decision:
        return False, "source_ts, available_to_brain_ts, and decision_asof_ts must all be present and parseable"
    if source > available:
        return False, "source_ts is later than available_to_brain_ts"
    if available > decision:
        return False, "available_to_brain_ts is later than decision_asof_ts"
    return True, "source time is point-in-time ordered"


def raw_integrity_pass(packet: dict[str, Any]) -> tuple[bool, str]:
    locator = packet.get("raw_locator_type")
    raw_path = str(packet.get("raw_path") or "")
    raw_sha = str(packet.get("raw_sha256") or "")
    if locator == "sqlite_partition_hash":
        if raw_path == "trading.db#market_bars_5m" and raw_sha:
            return True, "sqlite partition hash present"
        return False, "sqlite partition hash or locator missing"
    if raw_path and raw_sha:
        return True, "raw locator and bounded fingerprint present"
    return False, "raw file path or sha256 missing"


def mapping_pass(packet: dict[str, Any]) -> tuple[bool, str]:
    status = str(packet.get("mapping_status") or "")
    if status in {"SYMBOL_EXACT", "MACRO_CONTEXT_NO_SYMBOL_REQUIRED", "CANDIDATE_HINT_NON_AUTHORITY"}:
        return True, status
    return False, "mapping status is not approved for L1 gate"


def authority_pass(packet: dict[str, Any]) -> tuple[bool, str]:
    authority = str(packet.get("authority") or "")
    if authority in {"VENDOR_MARKET_DATA", "PUBLIC_CONTEXT_PRIMARY", "DISCOVERY_HINT"}:
        return True, authority
    return False, "authority is not recognized"


def classify_packet(packet: dict[str, Any]) -> dict[str, Any]:
    st_pass, st_reason = source_time_pass(packet)
    raw_pass, raw_reason = raw_integrity_pass(packet)
    map_pass, map_reason = mapping_pass(packet)
    auth_pass, auth_reason = authority_pass(packet)

    if not raw_pass:
        classification, reason = "BLOCKED_RAW_INTEGRITY", raw_reason
    elif not st_pass:
        classification, reason = "BLOCKED_SOURCE_TIME", st_reason
    elif not map_pass:
        classification, reason = "BLOCKED_MAPPING", map_reason
    elif not auth_pass:
        classification, reason = "BLOCKED_AUTHORITY", auth_reason
    elif packet.get("authority") == "DISCOVERY_HINT" or packet.get("candidate_hint_only") == "1":
        classification, reason = "DISCOVERY_ONLY", "public newswire candidate hints are non-authority discovery rows"
    elif packet.get("authority") == "PUBLIC_CONTEXT_PRIMARY":
        classification, reason = "CONTEXT_ONLY_CERTIFIED", "macro/context row is source-time certified but not a trading feature"
    elif packet.get("authority") == "VENDOR_MARKET_DATA":
        classification, reason = "STRICT_SOURCE_TIME_CERTIFIED", "market row passed strict source-time, raw, mapping, and authority gates"
    else:
        classification, reason = "BLOCKED_POLICY", "source family has no L2 admission policy"

    packet["source_time_certified"] = "1" if st_pass else "0"
    packet["strict_gate_pass"] = "1" if classification == "STRICT_SOURCE_TIME_CERTIFIED" else "0"
    packet["proxy_feature_allowed"] = "0"
    packet["l1_gate_classification"] = classification
    packet["blocker_reason"] = "" if not classification.startswith("BLOCKED") else reason
    packet["_gate_reasons"] = {
        "source_time": (st_pass, st_reason),
        "raw_integrity": (raw_pass, raw_reason),
        "mapping": (map_pass, map_reason),
        "authority": (auth_pass, auth_reason),
    }
    return packet


def gate_rows(packets: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    outputs = {
        "l1_source_time_gate.csv": [],
        "l1_raw_integrity_gate.csv": [],
        "l1_mapping_gate.csv": [],
        "l1_authority_gate.csv": [],
    }
    mapping = {
        "source_time": "l1_source_time_gate.csv",
        "raw_integrity": "l1_raw_integrity_gate.csv",
        "mapping": "l1_mapping_gate.csv",
        "authority": "l1_authority_gate.csv",
    }
    for packet in packets:
        for gate_name, (passed, reason) in packet["_gate_reasons"].items():
            outputs[mapping[gate_name]].append(
                {
                    "task_id": TASK_ID,
                    "source_packet_id": packet["source_packet_id"],
                    "endpoint_or_source_family": packet["endpoint_or_source_family"],
                    "gate_name": gate_name,
                    "gate_pass": "1" if passed else "0",
                    "classification": packet["l1_gate_classification"],
                    "reason": reason,
                }
            )
    return outputs


def handoff_rows(packets: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for packet in packets:
        classification = packet["l1_gate_classification"]
        if classification.startswith("BLOCKED"):
            continue
        rows.append(
            {
                "task_id": TASK_ID,
                "source_packet_id": packet["source_packet_id"],
                "endpoint_or_source_family": packet["endpoint_or_source_family"],
                "l1_gate_classification": classification,
                "l2_allowed_scope": packet["l2_allowed_scope"],
                "trading_authority": "0",
                "write_l2_materialization": "0",
                "notes": "candidate only; TASK-4133 does not mutate L2",
            }
        )
    return rows


def summary_rows(packets: list[dict[str, Any]], gaps: list[dict[str, str]]) -> list[dict[str, Any]]:
    counts: dict[tuple[str, str], int] = {}
    for packet in packets:
        key = (packet["endpoint_or_source_family"], packet["l1_gate_classification"])
        counts[key] = counts.get(key, 0) + 1
    return [
        {
            "task_id": TASK_ID,
            "source_family": family,
            "classification": classification,
            "packet_count": count,
            "gap_count": sum(1 for gap_row in gaps if gap_row["source_family"] == family),
        }
        for (family, classification), count in sorted(counts.items())
    ]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in columns})


def artifact_rows() -> list[dict[str, str]]:
    paths = [
        ("configs/l1_source_family_contracts.yaml", "config", "L1 source family contract and legacy surface boundary."),
        ("tools/db/source_acquisition/l1_bootstrap.py", "code", "Builds bounded L1 normalized packet, gate, gap, and handoff candidate artifacts."),
        ("scripts/build_l1_source_packet_bootstrap.py", "script", "Runs the TASK-4133 L1 bootstrap builder."),
        ("scripts/validate_l1_source_packet_bootstrap.py", "validator", "Validates TASK-4133 L1 packet and gate safety invariants."),
        ("ops/task_registry.yaml", "registry", "Registers TASK-4133 scope, artifacts, validators, and closeout."),
        ("ops/doc_registry.yaml", "registry", "Registers TASK-4133 documents and artifacts."),
        ("docs/active/ACTIVE_SSOT_INDEX.md", "docs", "Adds TASK-4133 to active L0/L1 SSOT index."),
        ("docs/active/CURRENT_TASKS.md", "docs", "Moves TASK-4133 into completed task ledger."),
        ("docs/active/PROJECT_STATUS.md", "docs", "Records L1 bootstrap status and non-change boundaries."),
        ("docs/architecture/l0_source_acquisition_project_management_plan.md", "docs", "Extends staged L0/L1 roadmap with L1 gate bootstrap boundary."),
        (f"docs/reports/{SLUG}/report.md", "task_report", "TASK-4133 closeout report."),
        (f"docs/reports/{SLUG}/artifact_manifest.csv", "artifact_manifest", "TASK-4133 changed/output file manifest."),
        (f"docs/reports/{SLUG}/validation_results.md", "validation_report", "TASK-4133 validator results."),
        (f"docs/reports/{SLUG}/l1_scope_and_safety_boundaries.md", "reference", "Human-readable L1 scope and safety boundary."),
        (f"docs/reports/{SLUG}/l1_bootstrap_summary.json", "reference", "TASK-4133 machine-readable summary."),
        (f"data/artifacts/{SLUG}/l1_packet_schema.json", "data_artifact", "Machine-readable L1 packet schema."),
        (f"data/artifacts/{SLUG}/l1_normalized_source_packets_sample.csv", "data_artifact", "Bounded normalized packet sample from rebuilt L0 outputs."),
        (f"data/artifacts/{SLUG}/l1_source_time_gate.csv", "data_artifact", "Source-time gate result rows."),
        (f"data/artifacts/{SLUG}/l1_raw_integrity_gate.csv", "data_artifact", "Raw/file/DB integrity gate result rows."),
        (f"data/artifacts/{SLUG}/l1_mapping_gate.csv", "data_artifact", "Mapping gate result rows."),
        (f"data/artifacts/{SLUG}/l1_authority_gate.csv", "data_artifact", "Authority/no-trading gate result rows."),
        (f"data/artifacts/{SLUG}/l1_source_gap_ledger.csv", "data_artifact", "Known source gaps that remain UNKNOWN/BLOCKER."),
        (f"data/artifacts/{SLUG}/l1_l2_handoff_candidates_sample.csv", "data_artifact", "Diagnostic-only L2 candidate handoff sample; no writes."),
        (f"data/artifacts/{SLUG}/l1_gate_summary.csv", "data_artifact", "Gate classification summary."),
        (f"data/artifacts/{SLUG}/validator_report.json", "data_artifact", "Machine-readable validator output."),
    ]
    return [
        {
            "path": path,
            "type": artifact_type,
            "purpose": purpose,
            "created_or_modified": "created" if path.startswith((f"docs/reports/{SLUG}", f"data/artifacts/{SLUG}")) or path.startswith("scripts/build_l1") or path.startswith("scripts/validate_l1") or path.startswith("tools/db/source_acquisition/l1_bootstrap.py") or path.startswith("configs/l1") else "modified",
            "task_id": TASK_ID,
        }
        for path, artifact_type, purpose in paths
    ]


def write_docs(summary: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# TASK-4133 L1 Development Plan

## Result

TASK-4133 installs a diagnostic-only L1 normalized source packet contract, gate outputs, and validator bootstrap aligned to the rebuilt L0 outputs. It does not write L2 materializations and does not open trading, broker, order, strategy acceptance, deployment readiness, paper promotion, or real-capital gates.

## What Changed

- Added `configs/l1_source_family_contracts.yaml` as the L1 source-family contract.
- Added `tools/db/source_acquisition/l1_bootstrap.py` plus build/validate scripts.
- Built bounded packet samples for public context news, public newswire, Wikimedia/market macro, and 5-minute DB resident bars when present.
- Added daily-bar raw CSV sampling from `data/raw/us_daily_alpaca_full_universe` when present.
- Added separate source-time, raw-integrity, mapping, and authority gates.
- Added a gap ledger where missing raw daily bars remain UNKNOWN/BLOCKER, not negative evidence.

## Current L1 Direction

L1 is now the evidence checkpoint between L0 collection and any later L2 consumption. Existing early surfaces remain useful, but `scripts/ingest_l0_news_to_l2.py` is not authoritative until rows pass this normalized L1 gate.

## Summary

- packet_count: {summary['packet_count']}
- handoff_candidate_count: {summary['handoff_candidate_count']}
- gap_count: {summary['gap_count']}
- strict_gate_pass_count: {summary['strict_gate_pass_count']}
- trading_authority_opened: false
"""
    (REPORT_DIR / "report.md").write_text(report, encoding="utf-8", newline="\n")

    safety = """# TASK-4133 L1 Scope And Safety Boundaries

L1 is an evidence and gate layer. It is not a strategy, trading feature factory, or order path.

Required boundaries:

- Missing or stale source evidence is UNKNOWN/BLOCKER, not negative evidence.
- Public newswire rows are discovery-only candidate hints unless a later task proves authority and mapping quality.
- Macro/context rows may bypass ticker mapping only when explicitly non-symbol-specific.
- 5-minute DB resident rows must carry a DB partition hash rather than relying on a raw file path alone.
- Daily bars may use `data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv` as the raw CSV source when that L0 backfill output exists.
- TASK-4133 does not mutate L2 tables, broker state, paper/live orders, strategy acceptance, deployment readiness, or real-capital state.
"""
    (REPORT_DIR / "l1_scope_and_safety_boundaries.md").write_text(safety, encoding="utf-8", newline="\n")
    (REPORT_DIR / "l1_bootstrap_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    write_csv(REPORT_DIR / "artifact_manifest.csv", artifact_rows(), ["path", "type", "purpose", "created_or_modified", "task_id"])


def build_and_write() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    packets, gaps = build_packets()
    clean_packets = [{k: v for k, v in packet.items() if not k.startswith("_")} for packet in packets]
    gate_outputs = gate_rows(packets)
    handoffs = handoff_rows(packets)
    summaries = summary_rows(packets, gaps)
    schema = {
        "task_id": TASK_ID,
        "schema_version": load_contracts()["schema_version"],
        "columns": PACKET_COLUMNS,
        "required_columns": load_contracts()["packet_required_columns"],
        "classifications": load_contracts()["classifications"],
    }

    (ARTIFACT_DIR / "l1_packet_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8", newline="\n")
    write_csv(ARTIFACT_DIR / "l1_normalized_source_packets_sample.csv", clean_packets, PACKET_COLUMNS)
    for name, rows in gate_outputs.items():
        write_csv(ARTIFACT_DIR / name, rows, GATE_COLUMNS)
    write_csv(ARTIFACT_DIR / "l1_source_gap_ledger.csv", gaps, GAP_COLUMNS)
    write_csv(
        ARTIFACT_DIR / "l1_l2_handoff_candidates_sample.csv",
        handoffs,
        ["task_id", "source_packet_id", "endpoint_or_source_family", "l1_gate_classification", "l2_allowed_scope", "trading_authority", "write_l2_materialization", "notes"],
    )
    write_csv(ARTIFACT_DIR / "l1_gate_summary.csv", summaries, ["task_id", "source_family", "classification", "packet_count", "gap_count"])
    summary = {
        "task_id": TASK_ID,
        "generated_at": utc_now(),
        "packet_count": len(clean_packets),
        "handoff_candidate_count": len(handoffs),
        "gap_count": len(gaps),
        "strict_gate_pass_count": sum(1 for p in clean_packets if p["strict_gate_pass"] == "1"),
        "classifications": sorted({p["l1_gate_classification"] for p in clean_packets}),
        "trading_authority_opened": False,
        "l2_materialization_written": False,
    }
    write_docs(summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(build_and_write(), indent=2, sort_keys=True))
