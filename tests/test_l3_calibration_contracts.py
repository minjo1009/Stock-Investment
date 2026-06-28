from __future__ import annotations

import sqlite3
import unittest

from tests.test_l3_evidence_edge_graph import _meaning
from src.brain.contracts import MeaningDirection
from src.brain.l3.calibration_apply import confidence_from_calibration_bucket
from src.brain.l3.calibration_bridge import L3OutcomeBridgeMethod, L3OutcomeBridgeRow
from src.brain.l3.calibration_builder import (
    audit_calibration_buckets,
    build_calibration_outcome_row,
    build_calibration_outcome_row_from_bridge,
)
from src.brain.l3.calibration_contracts import L3OutcomeLabel
from src.brain.l3.calibration_store import write_calibration_audit_buckets, write_calibration_outcomes
from src.brain.l3.contracts import L3CalibrationStatus


class L3CalibrationContractsTest(unittest.TestCase):
    def test_explicit_bridge_builds_diagnostic_calibration_row(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        row = build_calibration_outcome_row(
            meaning,
            {
                "outcome_bridge_key": meaning.meaning_id,
                "split_name": "OOS_2026Q2",
                "outcome_source_table": "unit.outcomes",
                "outcome_start_ts": "2026-06-01T10:00:00Z",
                "outcome_end_ts": "2026-06-06T10:00:00Z",
                "outcome_horizon": "5D",
                "outcome_metric": "FORWARD_RETURN_PCT",
                "outcome_value": 0.03,
                "outcome_label": "POSITIVE",
                "label_source": "explicit_unit_fixture",
            },
        )
        self.assertEqual(row.meaning_id, meaning.meaning_id)
        self.assertEqual(row.inferred_matching_used_flag, 0)
        self.assertEqual(row.outcome_label, L3OutcomeLabel.POSITIVE)
        self.assertEqual(row.trade_output_flag, 0)

    def test_manifest_backed_bridge_allows_lifecycle_outcome_key(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        bridge = L3OutcomeBridgeRow(
            bridge_id="bridge-1",
            meaning_id=meaning.meaning_id,
            l2_primitive_id="",
            source_receipt_id="",
            outcome_source_table="unit.lifecycle_outcomes",
            outcome_bridge_key="life-1",
            lifecycle_id="life-1",
            continuation_id="",
            bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
            bridge_source_artifact="unit_manifest.csv",
            inferred_matching_used_flag=0,
        )
        row = build_calibration_outcome_row_from_bridge(
            meaning,
            bridge,
            {
                "lifecycle_id": "life-1",
                "entry_ts": "2026-06-01T10:00:00Z",
                "exit_ts": "2026-06-06T10:00:00Z",
                "return_from_entry": "0.04",
                "positive_return_flag": "1",
                "canonical_split": "OOS",
            },
        )
        self.assertEqual(row.outcome_bridge_key, "life-1")
        self.assertEqual(row.lifecycle_id, "life-1")
        self.assertEqual(row.outcome_label, L3OutcomeLabel.POSITIVE)
        self.assertEqual(row.inferred_matching_used_flag, 0)

    def test_manifest_backed_bridge_without_split_or_label_is_review_only_missing_label(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        bridge = L3OutcomeBridgeRow(
            bridge_id="bridge-1",
            meaning_id=meaning.meaning_id,
            l2_primitive_id="",
            source_receipt_id="",
            outcome_source_table="unit.lifecycle_summary",
            outcome_bridge_key="life-1",
            lifecycle_id="life-1",
            continuation_id="",
            bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
            bridge_source_artifact="unit_manifest.csv",
            inferred_matching_used_flag=0,
        )
        row = build_calibration_outcome_row_from_bridge(
            meaning,
            bridge,
            {
                "lifecycle_id": "life-1",
                "entry_ts": "2026-06-01T10:00:00Z",
                "exit_ts": "2026-06-06T10:00:00Z",
                "return_from_entry": "0.04",
            },
        )
        self.assertEqual(row.split_name, "UNSPECIFIED_SPLIT_REVIEW_ONLY")
        self.assertEqual(row.outcome_label, L3OutcomeLabel.MISSING)
        self.assertEqual(row.missing_label_flag, 1)

    def test_manifest_backed_bridge_rejects_mismatched_lifecycle_key(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        bridge = L3OutcomeBridgeRow(
            bridge_id="bridge-1",
            meaning_id=meaning.meaning_id,
            l2_primitive_id="",
            source_receipt_id="",
            outcome_source_table="unit.lifecycle_outcomes",
            outcome_bridge_key="life-1",
            lifecycle_id="life-1",
            continuation_id="",
            bridge_method=L3OutcomeBridgeMethod.MANIFEST_BACKED_EXACT_KEY,
            bridge_source_artifact="unit_manifest.csv",
            inferred_matching_used_flag=0,
        )
        with self.assertRaises(ValueError):
            build_calibration_outcome_row_from_bridge(
                meaning,
                bridge,
                {
                    "lifecycle_id": "life-2",
                    "return_from_entry": "0.04",
                    "positive_return_flag": "1",
                    "canonical_split": "OOS",
                },
            )

    def test_inferred_matching_is_rejected(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        with self.assertRaises(ValueError):
            build_calibration_outcome_row(
                meaning,
                {
                    "outcome_bridge_key": "AAPL:2026-06-01",
                    "split_name": "OOS_2026Q2",
                    "outcome_source_table": "unit.outcomes",
                    "outcome_metric": "FORWARD_RETURN_PCT",
                    "outcome_label": "POSITIVE",
                    "label_source": "proximity",
                    "inferred_matching_used_flag": 1,
                },
            )

    def test_calibration_bucket_requires_min_sample_for_calibrated_probability(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        rows = [
            build_calibration_outcome_row(
                meaning,
                {
                    "outcome_bridge_key": meaning.meaning_id,
                    "split_name": "OOS_2026Q2",
                    "outcome_source_table": "unit.outcomes",
                    "outcome_start_ts": "2026-06-01T10:00:00Z",
                    "outcome_end_ts": "2026-06-06T10:00:00Z",
                    "outcome_horizon": "5D",
                    "outcome_metric": "FORWARD_RETURN_PCT",
                    "outcome_value": 0.03,
                    "outcome_label": "POSITIVE",
                    "label_source": "explicit_unit_fixture",
                },
            )
        ]
        bucket = audit_calibration_buckets(rows, min_sample_size=100)[0]
        self.assertEqual(bucket.calibration_status, L3CalibrationStatus.INSUFFICIENT_SAMPLE)
        self.assertIsNone(bucket.calibrated_probability)

    def test_calibration_store_preserves_safety_flags(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        row = build_calibration_outcome_row(
            meaning,
            {
                "outcome_bridge_key": meaning.meaning_id,
                "split_name": "OOS_2026Q2",
                "outcome_source_table": "unit.outcomes",
                "outcome_start_ts": "2026-06-01T10:00:00Z",
                "outcome_end_ts": "2026-06-06T10:00:00Z",
                "outcome_horizon": "5D",
                "outcome_metric": "FORWARD_RETURN_PCT",
                "outcome_value": 0.03,
                "outcome_label": "POSITIVE",
                "label_source": "explicit_unit_fixture",
            },
        )
        bucket = audit_calibration_buckets((row,), min_sample_size=1)[0]
        conn = sqlite3.connect(":memory:")
        try:
            write_calibration_outcomes(conn, (row,))
            write_calibration_audit_buckets(conn, (bucket,))
            stored = conn.execute(
                "SELECT inferred_matching_used_flag, trade_output_flag FROM l3_calibration_outcomes"
            ).fetchone()
            stored_bucket = conn.execute(
                "SELECT calibration_status, calibrated_probability FROM l3_calibration_audit_buckets"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(tuple(stored), (0, 0))
        self.assertEqual(stored_bucket[0], "CALIBRATED")
        self.assertEqual(stored_bucket[1], 1.0)

    def test_calibrated_confidence_only_from_calibrated_bucket(self) -> None:
        meaning = _meaning("support", MeaningDirection.SUPPORTIVE)
        row = build_calibration_outcome_row(
            meaning,
            {
                "outcome_bridge_key": meaning.meaning_id,
                "split_name": "OOS_2026Q2",
                "outcome_source_table": "unit.outcomes",
                "outcome_start_ts": "2026-06-01T10:00:00Z",
                "outcome_end_ts": "2026-06-06T10:00:00Z",
                "outcome_horizon": "5D",
                "outcome_metric": "FORWARD_RETURN_PCT",
                "outcome_value": 0.03,
                "outcome_label": "POSITIVE",
                "label_source": "explicit_unit_fixture",
            },
        )
        bucket = audit_calibration_buckets((row,), min_sample_size=1)[0]
        confidence = confidence_from_calibration_bucket(
            raw_band="medium",
            static_weight=0.60,
            bucket=bucket,
            calibration_version="unit_v1",
        )
        self.assertEqual(confidence.calibration_status, L3CalibrationStatus.CALIBRATED)
        self.assertEqual(confidence.calibrated_probability, 1.0)


if __name__ == "__main__":
    unittest.main()
