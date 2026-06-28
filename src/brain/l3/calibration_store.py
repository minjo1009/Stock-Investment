from __future__ import annotations

import sqlite3
from dataclasses import asdict

from src.brain.l3.calibration_builder import calibration_rows_to_dicts
from src.brain.l3.calibration_contracts import L3CalibrationAuditBucket, L3CalibrationOutcomeRow


CALIBRATION_OUTCOME_COLUMNS = [
    "calibration_row_id",
    "meaning_id",
    "evidence_edge_id",
    "l2_primitive_id",
    "source_receipt_id",
    "symbol",
    "entity_id",
    "asof_ts",
    "event_time",
    "source_ts",
    "available_to_brain_ts",
    "runtime_context",
    "source_time_certified",
    "freshness_status",
    "event_type",
    "economic_dimension",
    "direction",
    "confidence_raw_band",
    "confidence_static_weight",
    "split_name",
    "outcome_source_table",
    "outcome_bridge_key",
    "lifecycle_id",
    "continuation_id",
    "outcome_start_ts",
    "outcome_end_ts",
    "outcome_horizon",
    "outcome_metric",
    "outcome_value",
    "outcome_label",
    "label_source",
    "inferred_matching_used_flag",
    "label_used_in_assignment_flag",
    "outcome_used_in_assignment_flag",
    "missing_label_flag",
    "diagnostic_only",
    "trade_output_flag",
    "score_output_flag",
    "order_intent_flag",
]


def ensure_l3_calibration_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l3_calibration_outcomes (
            calibration_row_id TEXT PRIMARY KEY,
            meaning_id TEXT NOT NULL,
            evidence_edge_id TEXT NOT NULL,
            l2_primitive_id TEXT NOT NULL,
            source_receipt_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            asof_ts TEXT NOT NULL,
            event_time TEXT NOT NULL,
            source_ts TEXT NOT NULL,
            available_to_brain_ts TEXT NOT NULL,
            runtime_context TEXT NOT NULL,
            source_time_certified INTEGER NOT NULL,
            freshness_status TEXT NOT NULL,
            event_type TEXT NOT NULL,
            economic_dimension TEXT NOT NULL,
            direction TEXT NOT NULL,
            confidence_raw_band TEXT NOT NULL,
            confidence_static_weight REAL NOT NULL,
            split_name TEXT NOT NULL,
            outcome_source_table TEXT NOT NULL,
            outcome_bridge_key TEXT NOT NULL,
            lifecycle_id TEXT NOT NULL,
            continuation_id TEXT NOT NULL,
            outcome_start_ts TEXT NOT NULL,
            outcome_end_ts TEXT NOT NULL,
            outcome_horizon TEXT NOT NULL,
            outcome_metric TEXT NOT NULL,
            outcome_value REAL,
            outcome_label TEXT NOT NULL,
            label_source TEXT NOT NULL,
            inferred_matching_used_flag INTEGER NOT NULL,
            label_used_in_assignment_flag INTEGER NOT NULL,
            outcome_used_in_assignment_flag INTEGER NOT NULL,
            missing_label_flag INTEGER NOT NULL,
            diagnostic_only INTEGER NOT NULL,
            trade_output_flag INTEGER NOT NULL,
            score_output_flag INTEGER NOT NULL,
            order_intent_flag INTEGER NOT NULL,
            CHECK (inferred_matching_used_flag = 0),
            CHECK (label_used_in_assignment_flag = 0),
            CHECK (outcome_used_in_assignment_flag = 0),
            CHECK (diagnostic_only = 1),
            CHECK (trade_output_flag = 0),
            CHECK (score_output_flag = 0),
            CHECK (order_intent_flag = 0)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS l3_calibration_audit_buckets (
            bucket_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            economic_dimension TEXT NOT NULL,
            direction TEXT NOT NULL,
            confidence_raw_band TEXT NOT NULL,
            split_name TEXT NOT NULL,
            sample_size INTEGER NOT NULL,
            positive_count INTEGER NOT NULL,
            negative_count INTEGER NOT NULL,
            neutral_count INTEGER NOT NULL,
            missing_count INTEGER NOT NULL,
            observed_positive_rate REAL,
            average_static_weight REAL NOT NULL,
            brier_score REAL,
            calibration_error REAL,
            calibration_status TEXT NOT NULL,
            calibrated_probability REAL,
            diagnostic_only INTEGER NOT NULL,
            CHECK (diagnostic_only = 1)
        )
        """
    )
    conn.commit()


def write_calibration_outcomes(conn: sqlite3.Connection, rows: tuple[L3CalibrationOutcomeRow, ...]) -> None:
    ensure_l3_calibration_schema(conn)
    values = calibration_rows_to_dicts(rows)
    if not values:
        return
    placeholders = ",".join("?" for _ in CALIBRATION_OUTCOME_COLUMNS)
    columns = ",".join(CALIBRATION_OUTCOME_COLUMNS)
    conn.executemany(
        f"INSERT OR REPLACE INTO l3_calibration_outcomes ({columns}) VALUES ({placeholders})",
        [tuple(_db_value(row[column]) for column in CALIBRATION_OUTCOME_COLUMNS) for row in values],
    )
    conn.commit()


def write_calibration_audit_buckets(conn: sqlite3.Connection, buckets: tuple[L3CalibrationAuditBucket, ...]) -> None:
    ensure_l3_calibration_schema(conn)
    rows = []
    for bucket in buckets:
        values = asdict(bucket)
        rows.append(
            {
                **values,
                "bucket_id": "|".join(
                    [
                        bucket.event_type,
                        bucket.economic_dimension,
                        bucket.direction.value,
                        bucket.confidence_raw_band,
                        bucket.split_name,
                    ]
                ),
                "direction": bucket.direction.value,
                "calibration_status": bucket.calibration_status.value,
            }
        )
    if not rows:
        return
    columns = [
        "bucket_id",
        "event_type",
        "economic_dimension",
        "direction",
        "confidence_raw_band",
        "split_name",
        "sample_size",
        "positive_count",
        "negative_count",
        "neutral_count",
        "missing_count",
        "observed_positive_rate",
        "average_static_weight",
        "brier_score",
        "calibration_error",
        "calibration_status",
        "calibrated_probability",
        "diagnostic_only",
    ]
    placeholders = ",".join("?" for _ in columns)
    conn.executemany(
        f"INSERT OR REPLACE INTO l3_calibration_audit_buckets ({','.join(columns)}) VALUES ({placeholders})",
        [tuple(_db_value(row[column]) for column in columns) for row in rows],
    )
    conn.commit()


def _db_value(value: object) -> object:
    if isinstance(value, bool):
        return 1 if value else 0
    return value
