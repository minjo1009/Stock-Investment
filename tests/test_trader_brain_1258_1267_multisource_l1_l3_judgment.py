from __future__ import annotations

import unittest

from scripts.trader_brain_1258_1267_multisource_l1_l3_judgment_validate import validate


class Task1258MultisourceL1L3JudgmentTest(unittest.TestCase):
    def test_artifacts_validate(self) -> None:
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
