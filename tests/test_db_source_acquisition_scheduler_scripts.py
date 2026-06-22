from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DbSourceAcquisitionSchedulerScriptsTests(unittest.TestCase):
    def test_scheduler_config_and_scripts_are_source_only(self) -> None:
        config_path = ROOT / "configs" / "db_source_acquisition_scheduler.json"
        run_script = ROOT / "scripts" / "run_db_source_acquisition_scheduler.ps1"
        install_script = ROOT / "scripts" / "install_db_source_acquisition_scheduler_task.ps1"
        payload = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["owner_id"], "operator-db-source-acquisition-scheduler")
        self.assertFalse(payload["default_allow_network"])
        self.assertEqual(payload["sec_user_agent_env_name"], "SEC_USER_AGENT")
        jobs = {row["name"]: row for row in payload["jobs"]}
        self.assertIn("intraday_market_sources_5m", jobs)
        self.assertIn("heavy_sources_60m", jobs)
        self.assertTrue(jobs["intraday_market_sources_5m"]["allow_network"])
        self.assertIn("market_bars_5m", jobs["intraday_market_sources_5m"]["families"])
        self.assertIn("sec_events", jobs["heavy_sources_60m"]["families"])

        run_text = run_script.read_text(encoding="utf-8")
        install_text = install_script.read_text(encoding="utf-8")
        self.assertIn("tools.db.run_source_acquisition_once", run_text)
        self.assertIn("tools.db.run_registered_loop_once", run_text)
        self.assertIn("--apply", run_text)
        self.assertIn("--allow-network", run_text)
        self.assertIn("TraderBrainDbSourceAcquisitionScheduler", install_text)
        forbidden = ("submit_order", "KISClient", "run_trade_once")
        combined = (run_text + "\n" + install_text).lower()
        for token in forbidden:
            self.assertNotIn(token.lower(), combined)


if __name__ == "__main__":
    unittest.main()
