from __future__ import annotations

import unittest
from pathlib import Path

from scripts.frontend_continuity_validate import validate


class FrontendContinuityContractTest(unittest.TestCase):
    def test_frontend_contract_and_app_markers_exist(self) -> None:
        errors = validate(Path("."))
        self.assertEqual(errors, [])

    def test_portfolio_overview_is_marked_as_not_task_artifact(self) -> None:
        app_text = Path("src/ui/app.py").read_text(encoding="utf-8")
        self.assertIn("_render_portfolio_source_warning", app_text)
        self.assertIn("NOT_TASK_ARTIFACT", app_text)
        self.assertIn("Research Task artifact", app_text)

    def test_research_reports_warn_when_performance_source_differs(self) -> None:
        app_text = Path("src/ui/app.py").read_text(encoding="utf-8")
        self.assertIn("Performance source task/artifact", app_text)
        self.assertIn("성과 데이터는", app_text)
        self.assertIn("두 기준을 혼동하지 마십시오", app_text)


if __name__ == "__main__":
    unittest.main()
