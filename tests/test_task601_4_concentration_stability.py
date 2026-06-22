from __future__ import annotations

import unittest

import pandas as pd

from src.research.concentration_stability import build_concentration_stability


class Task6014ConcentrationStabilityTest(unittest.TestCase):
    def _events(self) -> pd.DataFrame:
        rows = []
        for index, (session, symbol) in enumerate(
            [
                ("2026-06-01", "AMD"),
                ("2026-06-01", "AMD"),
                ("2026-06-01", "AMZN"),
                ("2026-06-02", "AMD"),
                ("2026-06-02", "AMZN"),
                ("2026-06-02", "MSFT"),
                ("2026-06-03", "AMD"),
                ("2026-06-03", "NVDA"),
            ],
            start=1,
        ):
            rows.append(
                {
                    "candidate_id": f"candidate-{index}",
                    "symbol": symbol,
                    "generated_time": f"{session}T15:00:00Z",
                    "stage": "FILLED",
                }
            )
        return pd.DataFrame(rows)

    def test_multi_session_selected_window_passes_when_top3_share_is_below_threshold(self) -> None:
        selected = pd.DataFrame(
            [
                {"candidate_id": "s1", "symbol": "AMD", "generated_time": "2026-06-01T15:00:00Z"},
                {"candidate_id": "s2", "symbol": "AMZN", "generated_time": "2026-06-01T16:00:00Z"},
                {"candidate_id": "s3", "symbol": "MSFT", "generated_time": "2026-06-02T15:00:00Z"},
                {"candidate_id": "s4", "symbol": "NVDA", "generated_time": "2026-06-02T16:00:00Z"},
            ]
        )

        result = build_concentration_stability(self._events(), selected, recent_session_count=2)

        decision = result.decision.iloc[0]
        recent = result.recent_window_metrics.iloc[0]
        self.assertEqual(decision["decision_status"], "PASS_MULTI_SESSION_TOP3_BELOW_0_80")
        self.assertEqual(float(recent["top3_share"]), 0.75)
        self.assertEqual(int(recent["session_count"]), 2)
        self.assertEqual(int(decision["proximity_fallback_used_flag"]), 0)

    def test_single_session_selected_window_fails_even_if_symbols_are_diverse(self) -> None:
        selected = pd.DataFrame(
            [
                {"candidate_id": "s1", "symbol": "AMD", "generated_time": "2026-06-01T15:00:00Z"},
                {"candidate_id": "s2", "symbol": "AMZN", "generated_time": "2026-06-01T16:00:00Z"},
                {"candidate_id": "s3", "symbol": "MSFT", "generated_time": "2026-06-01T17:00:00Z"},
                {"candidate_id": "s4", "symbol": "NVDA", "generated_time": "2026-06-01T18:00:00Z"},
            ]
        )

        result = build_concentration_stability(self._events(), selected, recent_session_count=2)

        self.assertEqual(result.decision.iloc[0]["decision_status"], "FAIL_INSUFFICIENT_MULTI_SESSION_EVIDENCE")

    def test_multi_session_window_fails_when_top3_share_is_not_below_threshold(self) -> None:
        selected = pd.DataFrame(
            [
                {"candidate_id": "s1", "symbol": "AMD", "generated_time": "2026-06-01T15:00:00Z"},
                {"candidate_id": "s2", "symbol": "AMD", "generated_time": "2026-06-02T15:00:00Z"},
                {"candidate_id": "s3", "symbol": "AMZN", "generated_time": "2026-06-02T16:00:00Z"},
            ]
        )

        result = build_concentration_stability(self._events(), selected, recent_session_count=2)

        self.assertEqual(result.decision.iloc[0]["decision_status"], "FAIL_RECENT_WINDOW_TOP3_NOT_STABLE")
        self.assertEqual(float(result.recent_window_metrics.iloc[0]["top3_share"]), 1.0)


if __name__ == "__main__":
    unittest.main()
