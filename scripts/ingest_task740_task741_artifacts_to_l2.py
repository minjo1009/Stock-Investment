from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.l2.contracts import L2PrimitiveBatch, L2PrimitiveFact
from src.l2.freshness import CURRENT_OR_RECENT
from src.l2.lineage import canonical_json, stable_hash, stable_id
from src.l2.registry import L2_BUILDER_VERSION
from src.l2.runtime_context import HISTORICAL_RESEARCH
from src.l2.stores.primitive_writer import write_l2_batch, write_l2_primitives
from src.l2.stores.sqlite_l2_store import ensure_l2_schema


DEFAULT_ARTIFACTS = [
    Path("docs/reports/task_741_economic_denominator_meaning_layer/task741_economic_meaning_packets.csv"),
    Path("docs/reports/task_740_engineering_high_resolver_completion/task740_extracted_primitives.csv"),
]


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _event_time(row: dict[str, Any], fallback: str) -> tuple[str, bool]:
    for col in ("event_time", "source_ts", "timestamp", "trade_date", "date", "created_at"):
        value = str(row.get(col) or "").strip()
        if value:
            return value, True
    return fallback, False


def build_historical_artifact_batch_and_facts(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    asof_ts: str,
    created_at: str,
) -> tuple[L2PrimitiveBatch, list[L2PrimitiveFact]]:
    artifact_hash = file_sha256(path)
    source_receipt_id = f"artifact:{path.name}:{artifact_hash[:16]}"
    primitive_batch_id = stable_id("l2batch", "historical_artifact", path.as_posix(), artifact_hash)
    symbols = sorted({str(row.get("symbol") or "").upper() for row in rows if str(row.get("symbol") or "").strip()})
    input_hash = stable_hash({"path": path.as_posix(), "sha256": artifact_hash, "row_count": len(rows)})
    batch = L2PrimitiveBatch(
        primitive_batch_id=primitive_batch_id,
        runtime_context=HISTORICAL_RESEARCH,
        builder_name="ingest_task740_task741_artifacts_to_l2",
        builder_version=L2_BUILDER_VERSION,
        asof_ts=asof_ts,
        created_at=created_at,
        source_family_set="historical_artifact",
        symbol_set=canonical_json(symbols),
        row_count=len(rows),
        input_hash=input_hash,
        output_hash=stable_hash({"batch": primitive_batch_id, "rows": rows}),
        diagnostic_only=True,
    )
    facts: list[L2PrimitiveFact] = []
    for idx, row in enumerate(rows, start=1):
        event_time, source_time_certified = _event_time(row, asof_ts)
        symbol = str(row.get("symbol") or "").upper() or None
        payload = {
            "artifact_path": path.as_posix(),
            "artifact_sha256": artifact_hash,
            "row_number": idx,
            "row": row,
        }
        row_hash = stable_hash(payload)
        primitive_id = stable_id("l2fact", primitive_batch_id, idx, row_hash)
        lineage_edge_id = stable_id("l2lineage", primitive_id, source_receipt_id, row_hash)
        facts.append(
            L2PrimitiveFact(
                primitive_id=primitive_id,
                primitive_batch_id=primitive_batch_id,
                source_receipt_id=source_receipt_id,
                source_family="historical_artifact",
                provider=path.as_posix(),
                symbol=symbol,
                entity_id=str(row.get("entity_id") or "") or None,
                event_time=event_time,
                source_ts=event_time,
                capture_ts=created_at,
                available_to_brain_ts=created_at,
                asof_ts=asof_ts,
                primitive_type="historical_research_artifact",
                primitive_subtype=path.stem,
                primitive_payload_json=canonical_json(payload),
                freshness_status=CURRENT_OR_RECENT,
                source_time_certified=source_time_certified,
                closed_bar_only=True,
                runtime_context=HISTORICAL_RESEARCH,
                input_hash=row_hash,
                output_hash=stable_hash({"primitive_id": primitive_id, "payload": payload}),
                lineage_edge_id=lineage_edge_id,
            )
        )
    return batch, facts


def ingest_artifacts_to_l2(conn: sqlite3.Connection, artifact_paths: list[Path], *, asof_ts: str | None = None) -> dict[str, Any]:
    ensure_l2_schema(conn)
    created_at = utc_now()
    asof = asof_ts or created_at
    missing: list[str] = []
    ingested_rows = 0
    ingested_batches = 0
    for path in artifact_paths:
        resolved = path if path.is_absolute() else ROOT / path
        if not resolved.exists():
            missing.append(path.as_posix())
            continue
        rows = read_csv_rows(resolved)
        batch, facts = build_historical_artifact_batch_and_facts(resolved, rows, asof_ts=asof, created_at=created_at)
        write_l2_batch(conn, batch)
        write_l2_primitives(conn, facts)
        conn.execute(
            """
            UPDATE l2_runtime_context_audit
            SET historical_artifact_count = ?, live_evidence_count = 0,
                mixed_context_violation_flag = 0, freshness_violation_flag = 0, source_time_violation_flag = 0
            WHERE batch_id = ?
            """,
            (len(facts), batch.primitive_batch_id),
        )
        conn.commit()
        ingested_rows += len(facts)
        ingested_batches += 1
    return {
        "ingested_batches": ingested_batches,
        "ingested_rows": ingested_rows,
        "missing_artifacts": missing,
        "runtime_context": HISTORICAL_RESEARCH,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Task740/Task741 historical artifacts into canonical L2.")
    parser.add_argument("--db-path", type=Path, default=Path("trading.db"))
    parser.add_argument("--artifact", action="append", type=Path, default=[])
    parser.add_argument("--asof-ts", type=str, default="")
    args = parser.parse_args()
    paths = args.artifact or DEFAULT_ARTIFACTS
    conn = sqlite3.connect(args.db_path)
    try:
        result = ingest_artifacts_to_l2(conn, paths, asof_ts=args.asof_ts or None)
    finally:
        conn.close()
    if result["missing_artifacts"]:
        print(f"[L2_HISTORICAL_ARTIFACT_MISSING] {result['missing_artifacts']}")
    print(
        f"[L2_HISTORICAL_ARTIFACT_INGEST] batches={result['ingested_batches']} rows={result['ingested_rows']} context={result['runtime_context']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
