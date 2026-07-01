from __future__ import annotations

import unittest

from tools.db.source_acquisition.bar_full_backfill import throttle_sleep_seconds


class BarFullBackfillRatePacingTests(unittest.TestCase):
    def test_sleep_subtracts_request_elapsed_time(self) -> None:
        self.assertAlmostEqual(
            throttle_sleep_seconds(started_at=10.0, finished_at=10.2, requests_per_minute=120, rate_limited=False),
            0.3,
            places=6,
        )

    def test_no_extra_sleep_when_request_already_exceeds_interval(self) -> None:
        self.assertEqual(
            throttle_sleep_seconds(started_at=10.0, finished_at=10.9, requests_per_minute=120, rate_limited=False),
            0.0,
        )

    def test_rate_limit_keeps_cooldown(self) -> None:
        self.assertEqual(
            throttle_sleep_seconds(started_at=10.0, finished_at=10.1, requests_per_minute=120, rate_limited=True),
            60.0,
        )


if __name__ == "__main__":
    unittest.main()
