from __future__ import annotations

import unittest

from src.brain.l3.freshness_decay import freshness_decay, load_freshness_half_life_config


class L3FreshnessDecayTest(unittest.TestCase):
    def test_stale_source_decay_is_lower_than_fresh_source(self) -> None:
        self.assertEqual(freshness_decay(0, 240), 1.0)
        self.assertLess(freshness_decay(240, 240), freshness_decay(30, 240))
        config = load_freshness_half_life_config()
        self.assertEqual(config["news_discovery_proxy"], 240.0)


if __name__ == "__main__":
    unittest.main()
