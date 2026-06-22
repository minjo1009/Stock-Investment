from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.app.diagnostic_scheduler import run_diagnostic_scheduler_once
from src.state.store import acquire_scheduler_lease, get_scheduler_lease, initialize_store


class DiagnosticSchedulerTest(unittest.TestCase):
    def test_safety_tick_acquires_records_and_releases_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            result = run_diagnostic_scheduler_once(
                db_path=db_path,
                cadence="5_min_safety",
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                now="2026-06-20T10:00:01Z",
                owner_id="owner-a",
            )
            self.assertEqual(result.status, "DIAGNOSTIC_RUN_REQUIRED")
            self.assertTrue(result.should_execute)
            self.assertTrue(result.lease_acquired)
            self.assertTrue(result.heartbeat_inserted)
            self.assertIn("LEASE_TOKEN_VALIDATED", result.reason_codes)
            lease = get_scheduler_lease(db_path, lease_key="5_min_safety:2026-06-20T10:00:00Z")
            self.assertEqual(lease["status"], "RELEASED")

    def test_duplicate_state_skips_without_new_lease(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            run_diagnostic_scheduler_once(
                db_path=db_path,
                cadence="5_min_safety",
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                now="2026-06-20T10:00:01Z",
            )
            duplicate = run_diagnostic_scheduler_once(
                db_path=db_path,
                cadence="5_min_safety",
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                now="2026-06-20T10:00:30Z",
            )
            self.assertEqual(duplicate.status, "DUPLICATE_STATE_SKIPPED")
            self.assertFalse(duplicate.should_execute)
            self.assertFalse(duplicate.lease_acquired)

    def test_non_paper_environment_blocks_dry_run_tick(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            result = run_diagnostic_scheduler_once(
                db_path=db_path,
                cadence="5_min_safety",
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                now="2026-06-20T10:00:01Z",
                kis_environment="live",
            )
            self.assertEqual(result.status, "BLOCKED_NON_PAPER_ENV")
            self.assertFalse(result.should_execute)
            self.assertFalse(result.lease_acquired)
            self.assertIn("KIS_ENVIRONMENT_NOT_PAPER", result.reason_codes)

    def test_active_lease_held_by_other_owner_skips_tick(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            initialize_store(db_path)
            acquire_scheduler_lease(
                db_path,
                lease_key="5_min_safety:2026-06-20T10:00:00Z",
                cadence="5_min_safety",
                bucket_ts="2026-06-20T10:00:00Z",
                owner_id="owner-a",
                state_hash="external-hash",
                now="2026-06-20T10:00:00Z",
                ttl_seconds=300,
            )
            result = run_diagnostic_scheduler_once(
                db_path=db_path,
                cadence="5_min_safety",
                heartbeat_bucket_ts="2026-06-20T10:00:00Z",
                now="2026-06-20T10:00:01Z",
                owner_id="owner-b",
            )
            self.assertEqual(result.status, "LEASE_HELD_SKIPPED")
            self.assertFalse(result.should_execute)
            self.assertFalse(result.lease_acquired)


if __name__ == "__main__":
    unittest.main()
