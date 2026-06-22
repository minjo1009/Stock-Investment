from __future__ import annotations

import unittest

from scripts.trader_brain_1268_1287_source_extractors_validate import validate


class Task1268SourceExtractorsTest(unittest.TestCase):
    def test_artifacts_validate(self) -> None:
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
