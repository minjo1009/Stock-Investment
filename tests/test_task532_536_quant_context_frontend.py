from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task532_536_quant_context_frontend import (
    build_task532_external_quant_context_map,
    build_task533_factor_premium_validation_design,
    build_task534_statistical_validation_upgrade,
    build_task535_frontend_research_cockpit_v1,
    build_task536_frontend_api_boundary,
)
from src.reporting.research_task_catalog import build_research_task_catalog


class Task532536QuantContextFrontendTest(unittest.TestCase):
    def test_context_and_factor_design_do_not_approximate_missing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            t532 = build_task532_external_quant_context_map(out_dir=root / "532")["task_532_decision"].iloc[0]
            self.assertEqual(int(t532["missing_data_approximated_flag"]), 0)

            t533 = build_task533_factor_premium_validation_design(out_dir=root / "533")
            decision = t533["task_533_decision"].iloc[0]
            self.assertEqual(int(decision["factor_result_used_as_trading_trigger_flag"]), 0)
            missing = pd.read_csv(root / "533" / "factor_premium_missing_data_audit.csv")
            self.assertIn("Fama_French_daily_factors", set(missing["input_name"]))

    def test_statistical_and_frontend_artifacts_are_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            t534 = build_task534_statistical_validation_upgrade(out_dir=root / "534")["task_534_decision"].iloc[0]
            self.assertEqual(str(t534["strategy_acceptance_status"]), "STATISTICAL_VALIDATION_DIAGNOSTIC_ONLY")
            self.assertTrue((root / "534" / "multiple_testing_correction_audit.csv").exists())

            t535 = build_task535_frontend_research_cockpit_v1(out_dir=root / "535")["task_535_decision"].iloc[0]
            self.assertEqual(int(t535["streamlit_auto_catalog_ready_flag"]), 1)

            t536 = build_task536_frontend_api_boundary(out_dir=root / "536")["task_536_decision"].iloc[0]
            self.assertEqual(int(t536["react_fastapi_v2_compatible_flag"]), 1)

    def test_research_catalog_loads_latest_tasks(self) -> None:
        catalog = build_research_task_catalog()
        self.assertIn("Task531", set(catalog["task_id"]))
        self.assertIn("decision_badge", catalog.columns)


if __name__ == "__main__":
    unittest.main()
