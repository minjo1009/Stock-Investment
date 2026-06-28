from __future__ import annotations

import unittest
from pathlib import Path

from tools.db.run_source_acquisition_once import planned_jobs, run_once
from tools.db.source_acquisition.scheduler_override import load_effective_scheduler_config


class DbSourceAcquisitionRunnerTest(unittest.TestCase):
    def test_conservative_runner_is_dry_run_with_no_enabled_jobs(self) -> None:
        result = run_once(override_path=Path("__missing_local_override__.json"), dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["enabled_job_count"], 0)
        self.assertEqual(result["diagnostic_only"], True)
        self.assertEqual(result["execution_permitted"], 0)
        self.assertEqual(result["broker_mutation_permitted"], 0)

    def test_template_override_plans_diagnostic_jobs_only(self) -> None:
        config = load_effective_scheduler_config(
            override_path=Path("configs/local_templates/db_source_acquisition_scheduler.override.example.json"),
            audit_path=None,
        )
        jobs = planned_jobs(config)
        self.assertGreaterEqual(len(jobs), 4)
        self.assertTrue(all(job["diagnostic_only"] for job in jobs))
        self.assertTrue(all(int(job["execution_permitted"]) == 0 for job in jobs))


if __name__ == "__main__":
    unittest.main()
