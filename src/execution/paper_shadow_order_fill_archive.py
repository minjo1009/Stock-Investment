from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


REQUIRED_ORDER_FILL_FIELDS = (
    "decision_id",
    "client_order_id",
    "order_id",
    "lifecycle_id",
    "order_status",
    "submitted_ts",
    "filled_ts",
    "filled_qty",
    "filled_avg_price",
    "reject_reason",
    "raw_message_hash",
    "broker_truth_flag",
    "shadow_mode_flag",
)


@dataclass(frozen=True)
class ShadowOrderArchiveConfig:
    output_dir: Path
    policy_version: str
    scope_mode: str = "NBBO_ONLY_SCOPE_LIMITED"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def deterministic_shadow_id(prefix: str, payload: dict[str, object]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:20]}"


def build_shadow_order_fill_records(
    decisions: pd.DataFrame,
    *,
    policy_version: str,
    archive_ts_utc: str | None = None,
) -> dict[str, pd.DataFrame]:
    archive_ts_utc = archive_ts_utc or utc_now_iso()
    decision_rows = []
    order_rows = []
    fill_rows = []
    lineage_rows = []
    for row in decisions.to_dict(orient="records"):
        lifecycle_id = str(row.get("lifecycle_id", ""))
        if not lifecycle_id:
            continue
        decision_payload = {
            "lifecycle_id": lifecycle_id,
            "entry_ts": row.get("entry_ts"),
            "symbol": row.get("symbol"),
            "policy_version": policy_version,
        }
        decision_id = deterministic_shadow_id("decision", decision_payload)
        client_order_id = deterministic_shadow_id("client", {"decision_id": decision_id})
        order_id = deterministic_shadow_id("shadow_order", {"client_order_id": client_order_id})
        fill_id = deterministic_shadow_id("shadow_fill", {"order_id": order_id, "lifecycle_id": lifecycle_id})
        raw_message = {
            "event_type": "SHADOW_FILL",
            "decision_id": decision_id,
            "client_order_id": client_order_id,
            "order_id": order_id,
            "lifecycle_id": lifecycle_id,
            "symbol": row.get("symbol"),
            "filled_avg_price": row.get("entry_price"),
        }
        raw_hash = hashlib.sha256(json.dumps(raw_message, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        decision_rows.append(
            {
                "decision_id": decision_id,
                "candidate_lifecycle_id": lifecycle_id,
                "lifecycle_id": lifecycle_id,
                "symbol": row.get("symbol"),
                "theme_id": row.get("theme_id"),
                "decision_kind": "ENTRY",
                "decision_action": "SHADOW_ENTRY",
                "entry_ts": row.get("entry_ts"),
                "decision_recorded_ts_utc": archive_ts_utc,
                "receive_ts_utc": row.get("recv_ts_utc", pd.NA),
                "receive_ts_available_flag": int(pd.notna(row.get("recv_ts_utc", pd.NA))),
                "live_clock_record_flag": int(pd.notna(row.get("recv_ts_utc", pd.NA))),
                "historical_seed_record_flag": int(pd.isna(row.get("recv_ts_utc", pd.NA))),
                "policy_version": policy_version,
                "scope_mode": "NBBO_ONLY_SCOPE_LIMITED",
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
            }
        )
        order_rows.append(
            {
                "decision_id": decision_id,
                "client_order_id": client_order_id,
                "order_id": order_id,
                "lifecycle_id": lifecycle_id,
                "order_status": "shadow_filled",
                "submitted_ts": archive_ts_utc,
                "filled_ts": archive_ts_utc,
                "filled_qty": 1.0,
                "filled_avg_price": row.get("entry_price"),
                "reject_reason": pd.NA,
                "raw_message_hash": raw_hash,
                "broker_truth_flag": 0,
                "shadow_mode_flag": 1,
            }
        )
        fill_rows.append(
            {
                "fill_id": fill_id,
                "decision_id": decision_id,
                "client_order_id": client_order_id,
                "order_id": order_id,
                "lifecycle_id": lifecycle_id,
                "symbol": row.get("symbol"),
                "filled_ts": archive_ts_utc,
                "filled_qty": 1.0,
                "filled_avg_price": row.get("entry_price"),
                "raw_message_hash": raw_hash,
                "broker_truth_flag": 0,
                "shadow_mode_flag": 1,
            }
        )
        lineage_rows.append(
            {
                "decision_id": decision_id,
                "client_order_id": client_order_id,
                "order_id": order_id,
                "fill_id": fill_id,
                "lifecycle_id": lifecycle_id,
                "lineage_complete_flag": 1,
                "broker_truth_flag": 0,
                "shadow_mode_flag": 1,
            }
        )
    return {
        "paper_shadow_decision_snapshot_log": pd.DataFrame(decision_rows),
        "paper_shadow_order_archive": pd.DataFrame(order_rows),
        "paper_shadow_fill_archive": pd.DataFrame(fill_rows),
        "paper_shadow_lifecycle_lineage": pd.DataFrame(lineage_rows),
    }


def validate_order_fill_contract(order_frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for field in REQUIRED_ORDER_FILL_FIELDS:
        rows.append(
            {
                "field_name": field,
                "present_flag": int(field in order_frame.columns),
                "non_null_count": int(order_frame[field].notna().sum()) if field in order_frame.columns else 0,
            }
        )
    return pd.DataFrame(rows)
