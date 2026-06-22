from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainMeaningAdapter(unittest.TestCase):
    def _task742_row(self) -> dict[str, object]:
        return {
            "lifecycle_id": "life-1",
            "source_event_id": "source-event-1",
            "symbol": "TEST",
            "event_date": "2026-06-19",
            "tradable_after_dt": "2026-06-20T00:00:00Z",
            "economic_direction_hint": "positive",
            "confidence_band": "medium",
            "ambiguity_flags": "sale_may_be_plan_or_compensation",
            "soft_uncertainty_flags": "market_scale_unknown",
            "hard_blocker_flags": "",
            "needed_confirmation": "price_absorption_after_filing",
            "relation_ready_tier": "directional",
            "direction_hint_trade_instruction_flag": 0,
            "asof_change_inference_forbidden_flag": 1,
            "trade_output_flag": 0,
            "score_output_flag": 0,
            "backtest_eligible_flag": 0,
            "outcome_used_for_assignment_flag": 0,
        }

    def test_task742_row_becomes_review_only_economic_meaning(self) -> None:
        from brain.contracts import MeaningDirection
        from brain.meaning_adapter import task742_row_to_economic_meaning

        meaning = task742_row_to_economic_meaning(self._task742_row())

        self.assertEqual(meaning.meaning_id, "task742:life-1:source-event-1")
        self.assertEqual(meaning.asof_ts, "2026-06-20T00:00:00Z")
        self.assertEqual(meaning.symbol, "TEST")
        self.assertEqual(meaning.direction, MeaningDirection.SUPPORTIVE)
        self.assertAlmostEqual(meaning.confidence, 0.6)
        self.assertEqual(meaning.source_packet_ids, ("source-event-1",))
        self.assertEqual(meaning.relation_readiness, "directional")
        self.assertIn("market_scale_unknown", meaning.uncertainty_flags)
        self.assertFalse(meaning.outcome_used_for_assignment)

    def test_task742_rows_batch_adapter_is_immutable_tuple(self) -> None:
        from brain.meaning_adapter import task742_rows_to_economic_meanings

        meanings = task742_rows_to_economic_meanings([self._task742_row(), {**self._task742_row(), "source_event_id": "source-event-2"}])

        self.assertEqual(len(meanings), 2)
        self.assertIsInstance(meanings, tuple)
        self.assertEqual(meanings[1].meaning_id, "task742:life-1:source-event-2")

    def test_task742_trade_output_flag_is_rejected(self) -> None:
        from brain.meaning_adapter import task742_row_to_economic_meaning

        row = self._task742_row()
        row["trade_output_flag"] = 1

        with self.assertRaises(ValueError):
            task742_row_to_economic_meaning(row)

    def test_task742_outcome_assignment_flag_is_rejected(self) -> None:
        from brain.meaning_adapter import task742_row_to_economic_meaning

        row = self._task742_row()
        row["outcome_used_for_assignment_flag"] = 1

        with self.assertRaises(ValueError):
            task742_row_to_economic_meaning(row)

    def test_task742_missing_asof_is_rejected(self) -> None:
        from brain.meaning_adapter import task742_row_to_economic_meaning

        row = self._task742_row()
        row["tradable_after_dt"] = ""

        with self.assertRaises(ValueError):
            task742_row_to_economic_meaning(row)

    def test_package_exports_meaning_adapter(self) -> None:
        import brain

        self.assertIn("task742_row_to_economic_meaning", brain.__all__)
        self.assertIn("task742_rows_to_economic_meanings", brain.__all__)
        self.assertTrue(hasattr(brain, "task742_row_to_economic_meaning"))
        self.assertTrue(hasattr(brain, "task742_rows_to_economic_meanings"))


if __name__ == "__main__":
    unittest.main()
