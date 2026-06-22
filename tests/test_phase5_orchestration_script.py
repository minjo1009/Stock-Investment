from __future__ import annotations

import unittest
from pathlib import Path


class TestPhase5OrchestrationScript(unittest.TestCase):
    def test_no_direct_empty_symbols_passthrough(self) -> None:
        script = Path("scripts/run_phase5_paper_loop.ps1").read_text(encoding="utf-8")
        self.assertNotIn("-Symbols $Symbols", script)
        self.assertIn("Get-SymbolList", script)
        self.assertIn("$task089Args", script)
        self.assertIn("$task089Args[\"Symbols\"]", script)

    def test_step_wrapper_and_error_continuation_exist(self) -> None:
        script = Path("scripts/run_phase5_paper_loop.ps1").read_text(encoding="utf-8")
        self.assertIn("function Invoke-StepScript", script)
        self.assertIn("try {", script)
        self.assertIn("catch {", script)
        self.assertIn("Task 089 failed", script)
        self.assertIn("Task 087 failed", script)
        self.assertIn("Task 088 failed", script)


if __name__ == "__main__":
    unittest.main()

