from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.app.runtime_scheduler_supervisor import (
    RuntimeSchedulerConfig,
    load_runtime_scheduler_config,
    run_runtime_scheduler_supervisor_once,
)


def _config(db_path: str) -> RuntimeSchedulerConfig:
    return RuntimeSchedulerConfig.from_dict(
        {
            "owner_id": "operator-test",
            "db_path": db_path,
            "kis_environment": "paper",
            "lease_ttl_seconds": 300,
            "cadences": [
                {"cadence": "5_min_safety", "interval_minutes": 5, "enabled": True},
                {"cadence": "10_min_brain", "interval_minutes": 10, "enabled": True},
                {"cadence": "30_min_heavy_source", "interval_minutes": 30, "enabled": False},
            ],
        }
    )


class RuntimeSchedulerSupervisorTest(unittest.TestCase):
    def test_due_cadences_run_dry_run_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            result = run_runtime_scheduler_supervisor_once(
                config=_config(db_path),
                now="2026-06-20T10:00:00Z",
            )
            self.assertTrue(result.dry_run_only)
            statuses = {row["cadence"]: row["status"] for row in result.executed}
            self.assertEqual(statuses["5_min_safety"], "DIAGNOSTIC_RUN_REQUIRED")
            self.assertEqual(statuses["10_min_brain"], "NO_CHANGED_CANDIDATES_SKIPPED")
            self.assertIn({"cadence": "30_min_heavy_source", "reason": "CADENCE_DISABLED"}, result.skipped)

    def test_not_due_cadence_skips_without_heartbeat(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "trading.db")
            result = run_runtime_scheduler_supervisor_once(
                config=_config(db_path),
                now="2026-06-20T10:01:00Z",
            )
            self.assertEqual(result.executed, ())
            self.assertIn({"cadence": "5_min_safety", "reason": "NOT_DUE"}, result.skipped)

    def test_config_requires_paper_environment(self) -> None:
        with self.assertRaises(ValueError):
            RuntimeSchedulerConfig.from_dict(
                {
                    "owner_id": "operator-test",
                    "db_path": "trading.db",
                    "kis_environment": "live",
                    "cadences": [{"cadence": "5_min_safety", "interval_minutes": 5}],
                }
            )

    def test_load_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "owner_id": "operator-test",
                        "db_path": "trading.db",
                        "kis_environment": "paper",
                        "cadences": [{"cadence": "5_min_safety", "interval_minutes": 5}],
                    }
                ),
                encoding="utf-8-sig",
            )
            self.assertEqual(load_runtime_scheduler_config(path).owner_id, "operator-test")


if __name__ == "__main__":
    unittest.main()
