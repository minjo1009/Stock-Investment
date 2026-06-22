from __future__ import annotations

import unittest

from scripts.trader_brain_1238_1247_raw_text_terminal_evidence_validate import validate


class Task1238RawTextTerminalEvidenceTest(unittest.TestCase):
    def test_artifacts_validate(self) -> None:
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
