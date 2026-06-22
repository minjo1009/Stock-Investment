from __future__ import annotations

import importlib
import unittest


class RuntimeImportContractTest(unittest.TestCase):
    def test_runtime_modules_import_from_repo_root_without_pythonpath_src(self) -> None:
        modules = [
            "src.app.supervisor_slack_alert",
            "src.app.task_587_slack_trading_report_integration",
            "src.app.task_589_paper_eod_slack_report",
            "src.integration.kis_client",
        ]
        for module in modules:
            with self.subTest(module=module):
                self.assertIsNotNone(importlib.import_module(module))


if __name__ == "__main__":
    unittest.main()
