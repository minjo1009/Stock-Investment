from __future__ import annotations

import unittest

from scripts.trader_brain_1248_1257_raw_text_policy_replay_validate import validate


class Task1248RawTextPolicyReplayTest(unittest.TestCase):
    def test_artifacts_validate(self) -> None:
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
