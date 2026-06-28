from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.db.source_acquisition.secret_redaction import redact_text


DEFAULT_CHECKPOINT_PATH = Path("data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl")
CHECKPOINT_STATUSES = {
    "PENDING",
    "RUNNING",
    "EXPORTED",
    "SKIPPED_EXISTS",
    "FAILED_RETRYABLE",
    "FAILED_PERMANENT",
    "RATE_LIMITED",
    "CREDENTIAL_BLOCKED",
    "EMPTY_PROVIDER_RESPONSE",
    "QUARANTINED",
}
CHECKPOINT_FIELDS = [
    "checkpoint_id",
    "provider",
    "feed",
    "source_type",
    "symbol",
    "session_date",
    "chunk_start_ts",
    "chunk_end_ts",
    "chunk_id",
    "status",
    "attempt_count",
    "last_attempt_ts",
    "last_success_ts",
    "row_count",
    "raw_path",
    "raw_sha256",
    "error_category",
    "error_message_redacted",
    "created_at",
    "updated_at",
]


def compute_chunk_id(*, provider: str, feed: str, source_type: str, symbol: str, chunk_start_ts: str, chunk_end_ts: str) -> str:
    payload = "|".join([provider, feed, source_type, symbol.upper(), chunk_start_ts, chunk_end_ts])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MicrostructureCheckpointStore:
    def __init__(self, path: Path = DEFAULT_CHECKPOINT_PATH) -> None:
        self.path = path

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        return rows

    def latest(self) -> dict[str, Any] | None:
        rows = self.load()
        if not rows:
            return None
        return sorted(rows, key=lambda row: str(row.get("updated_at", "")))[-1]

    def should_skip(self, *, chunk_id: str, force: bool = False) -> bool:
        if force:
            return False
        for row in self.load():
            if row.get("chunk_id") == chunk_id and row.get("status") == "EXPORTED":
                return True
        return False

    def record(
        self,
        *,
        provider: str,
        feed: str,
        source_type: str,
        symbol: str,
        session_date: str,
        chunk_start_ts: str,
        chunk_end_ts: str,
        status: str,
        row_count: int = 0,
        raw_path: Path | str | None = None,
        raw_sha256: str = "",
        error_category: str = "",
        error_message: str = "",
    ) -> dict[str, Any]:
        if status not in CHECKPOINT_STATUSES:
            raise ValueError(f"unsupported microstructure checkpoint status: {status}")
        chunk_id = compute_chunk_id(
            provider=provider,
            feed=feed,
            source_type=source_type,
            symbol=symbol,
            chunk_start_ts=chunk_start_ts,
            chunk_end_ts=chunk_end_ts,
        )
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        rows = self.load()
        existing = next((row for row in rows if row.get("chunk_id") == chunk_id), None)
        if raw_path and not raw_sha256:
            path = Path(raw_path)
            if path.exists():
                raw_sha256 = sha256_file(path)
        record = {
            "checkpoint_id": existing.get("checkpoint_id") if existing else chunk_id,
            "provider": provider,
            "feed": feed,
            "source_type": source_type,
            "symbol": symbol.upper(),
            "session_date": session_date,
            "chunk_start_ts": chunk_start_ts,
            "chunk_end_ts": chunk_end_ts,
            "chunk_id": chunk_id,
            "status": status,
            "attempt_count": int(existing.get("attempt_count", 0)) + 1 if existing else 1,
            "last_attempt_ts": now,
            "last_success_ts": now if status in {"EXPORTED", "SKIPPED_EXISTS"} else (existing.get("last_success_ts", "") if existing else ""),
            "row_count": int(row_count),
            "raw_path": "" if raw_path is None else str(raw_path),
            "raw_sha256": raw_sha256,
            "error_category": error_category,
            "error_message_redacted": redact_text(error_message),
            "created_at": existing.get("created_at") if existing else now,
            "updated_at": now,
        }
        rows = [row for row in rows if row.get("chunk_id") != chunk_id]
        rows.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")
        return record


def checkpoint_schema() -> list[str]:
    return list(CHECKPOINT_FIELDS)
