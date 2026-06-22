from __future__ import annotations

import unittest

import pandas as pd

from src.risk.add_relay_diagnostics import build_add_relay_diagnostics


class TestAddRelayDiagnostics(unittest.TestCase):
    def test_empty_input_returns_stable_shapes(self) -> None:
        trace_df, dropoff_df, reasons_df = build_add_relay_diagnostics(pd.DataFrame())
        self.assertIn("final_add_relay_outcome", trace_df.columns)
        self.assertIn("stage_name", dropoff_df.columns)
        self.assertIn("relay_stage", reasons_df.columns)
        self.assertEqual(len(trace_df), 0)
        self.assertEqual(len(dropoff_df), 0)
        self.assertEqual(len(reasons_df), 0)

    def test_trace_and_dropoff_capture_add_relay_stages(self) -> None:
        shadow_log = pd.DataFrame(
            {
                "trade_id": ["t1", "t2", "t3"],
                "symbol": ["AMD", "MSFT", "NVDA"],
                "allow_new_entry": [True, True, False],
                "allow_add": [True, False, False],
                "factor_exposure_violated": [False, False, False],
                "staged_add_allowed": [True, False, False],
                "quality_aware_add_allowed": [True, False, False],
                "healthy_aggressive_final_add_allowed": [True, False, False],
                "shadow_reasons": ["row_state=normal", "row_state=crowded", "row_state=dislocation"],
                "participation_reasons": ["healthy", "fragile", ""],
                "quality_aware_reasons": ["healthy_expansion_relaxed_add", "fragile_crowding_strict_suppression", ""],
                "healthy_aggressive_reasons": ["healthy_expansion_aggressive_add", "", ""],
                "violated_factors": ["", "", ""],
            }
        )
        trace_df, dropoff_df, _reasons_df = build_add_relay_diagnostics(shadow_log)
        self.assertEqual(str(trace_df.loc[0, "final_add_relay_outcome"]), "add_relay_pass")
        self.assertEqual(str(trace_df.loc[1, "final_add_relay_block_stage"]), "exposure_add_gate")
        self.assertEqual(str(trace_df.loc[2, "final_add_relay_block_stage"]), "exposure_gate")
        self.assertTrue(dropoff_df["stage_name"].astype(str).eq("healthy_aggressive_gate").any())

    def test_blocking_reasons_parse_tuple_like_strings(self) -> None:
        shadow_log = pd.DataFrame(
            {
                "trade_id": ["t1"],
                "allow_new_entry": [True],
                "allow_add": [False],
                "factor_exposure_violated": [True],
                "staged_add_allowed": [False],
                "quality_aware_add_allowed": [False],
                "healthy_aggressive_final_add_allowed": [False],
                "shadow_reasons": ["('crowded_state_add_restricted', 'factor_budget_blocked_entry')"],
                "participation_reasons": ["['fragile_crowding']"],
                "quality_aware_reasons": ["fragile_crowding_strict_suppression"],
                "healthy_aggressive_reasons": [""],
                "violated_factors": ["semis,ai"],
            }
        )
        _trace_df, _dropoff_df, reasons_df = build_add_relay_diagnostics(shadow_log)
        self.assertTrue(reasons_df["reason"].astype(str).eq("crowded_state_add_restricted").any())
        self.assertTrue(reasons_df["reason"].astype(str).eq("semis").any())
        self.assertTrue(reasons_df["relay_stage"].astype(str).eq("final_block_stage").any())


if __name__ == "__main__":
    unittest.main()
