from __future__ import annotations

import unittest

from src.backtest.build_task546_microstructure_live_capture_layer import (
    build_microstructure_live_source_contract,
    build_missing_source_blocker_audit,
    build_source_availability_audit,
)


class Task546MicrostructureSourceContractTest(unittest.TestCase):
    def test_missing_sources_are_audited_not_approximated(self) -> None:
        contract = build_microstructure_live_source_contract()
        audit = build_source_availability_audit(contract)
        blockers = build_missing_source_blocker_audit(audit)
        self.assertEqual(int(contract["approximation_allowed_flag"].max()), 0)
        self.assertIn("full_depth_book_stream", set(blockers["source_name"]))
        full_depth = blockers[blockers["source_name"].eq("full_depth_book_stream")].iloc[0]
        self.assertEqual(int(full_depth["blocked_flag"]), 1)
        self.assertEqual(int(full_depth["approximation_attempted_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
