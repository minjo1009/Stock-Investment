from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tools.db.source_acquisition.public_newswire_shards import build_inventory, build_shard, seed_shard_state
from scripts.run_l0_public_newswire_sharded_backfill import effective_source_lanes, source_round_robin


class L0PublicNewswireShardedBackfillTests(unittest.TestCase):
    def test_businesswire_month_units_handle_leap_year(self) -> None:
        shard = build_shard(source="businesswire", shard_key="2020-02", start=date(2020, 2, 1), end=date(2020, 2, 29))
        self.assertEqual(shard.total_units, 29)
        shard = build_shard(source="businesswire", shard_key="2021-02", start=date(2021, 2, 1), end=date(2021, 2, 28))
        self.assertEqual(shard.total_units, 28)

    def test_prnewswire_month_excludes_recent_pages(self) -> None:
        shard = build_shard(source="prnewswire", shard_key="2020-10", start=date(2020, 10, 1), end=date(2020, 10, 31))
        self.assertEqual(shard.total_units, 1)
        self.assertFalse(any("sitemap-news.xml?page=" in url for url in shard.archive_urls))
        recent = build_shard(source="prnewswire", shard_key="recent", start=date(2016, 1, 1), end=date(2026, 6, 30))
        self.assertEqual(recent.total_units, 15)
        self.assertTrue(all("sitemap-news.xml?page=" in url for url in recent.archive_urls))

    def test_full_inventory_matches_expected_units_through_june_2026(self) -> None:
        inventory = build_inventory(start_month="2016-01", end_month="2026-06")
        self.assertEqual(inventory["total_units"], 4101)
        self.assertEqual(inventory["by_source"]["businesswire"]["total_units"], 3834)
        self.assertEqual(inventory["by_source"]["globenewswire"]["total_units"], 126)
        self.assertEqual(inventory["by_source"]["prnewswire"]["total_units"], 141)

    def test_businesswire_day_granularity_preserves_total_units(self) -> None:
        inventory = build_inventory(
            start_month="2020-02",
            end_month="2020-02",
            sources=["businesswire"],
            businesswire_shard_granularity="day",
        )
        self.assertEqual(inventory["total_units"], 29)
        self.assertEqual(inventory["by_source"]["businesswire"]["total_units"], 29)
        self.assertEqual(len(inventory["shards"]), 29)
        self.assertTrue(all(row["total_units"] == 1 for row in inventory["shards"]))
        self.assertIn("businesswire:2020-02-29", {row["shard_id"] for row in inventory["shards"]})

    def test_businesswire_day_granularity_inherits_monthly_local_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact_root = root / "artifacts"
            raw_root = root / "raw"
            monthly_dir = artifact_root / "businesswire" / "2020-10"
            monthly_dir.mkdir(parents=True)
            completed_url = "https://bw-prod-sitemap.s3.us-east-1.amazonaws.com/webdmz1.vaprod.businesswire.com/home/2020-10-01.xml.gz"
            (monthly_dir / "collector_state.json").write_text(
                json.dumps({"backfill": {"businesswire": {"completed_archive_urls": [completed_url], "archive_entry_offsets": {}}}}),
                encoding="utf-8",
            )
            inventory = build_inventory(
                start_month="2020-10",
                end_month="2020-10",
                sources=["businesswire"],
                artifact_root=artifact_root,
                raw_root=raw_root,
                businesswire_shard_granularity="day",
            )
            first_day = next(row for row in inventory["shards"] if row["shard_key"] == "2020-10-01")
            self.assertEqual(first_day["legacy_completed_units"], 1)
            self.assertEqual(first_day["pending_units"], 0)

    def test_legacy_completed_units_are_seeded_to_shard_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            completed_url = "https://bw-prod-sitemap.s3.us-east-1.amazonaws.com/webdmz1.vaprod.businesswire.com/home/2020-10-01.xml.gz"
            legacy = {"backfill": {"businesswire": {"completed_archive_urls": [completed_url], "archive_entry_offsets": {}}}}
            shard = build_shard(
                source="businesswire",
                shard_key="2020-10",
                start=date(2020, 10, 1),
                end=date(2020, 10, 31),
                artifact_root=root / "artifacts",
                raw_root=root / "raw",
                legacy_state=legacy,
            )
            self.assertEqual(shard.legacy_completed_units, 1)
            seed_shard_state(shard.as_dict())
            state = json.loads(Path(shard.state_path).read_text(encoding="utf-8"))
            self.assertIn(completed_url, state["backfill"]["businesswire"]["completed_archive_urls"])

    def test_source_round_robin_does_not_front_load_businesswire(self) -> None:
        shards = [
            {"source": "businesswire", "shard_id": "businesswire:1"},
            {"source": "businesswire", "shard_id": "businesswire:2"},
            {"source": "businesswire", "shard_id": "businesswire:3"},
            {"source": "globenewswire", "shard_id": "globenewswire:1"},
            {"source": "prnewswire", "shard_id": "prnewswire:1"},
        ]
        ordered = source_round_robin(shards, ["businesswire", "globenewswire", "prnewswire"])
        self.assertEqual(
            [row["shard_id"] for row in ordered[:4]],
            ["businesswire:1", "globenewswire:1", "prnewswire:1", "businesswire:2"],
        )

    def test_dynamic_lane_rebalance_returns_finished_source_lane_to_businesswire(self) -> None:
        queue = [
            ({"source": "businesswire", "shard_id": "businesswire:1"}, 0),
            ({"source": "businesswire", "shard_id": "businesswire:2"}, 0),
            ({"source": "prnewswire", "shard_id": "prnewswire:1"}, 0),
        ]
        lanes = effective_source_lanes(
            queue,
            running=[],
            sources=["businesswire", "globenewswire", "prnewswire"],
            source_base_lanes={"businesswire": 2, "globenewswire": 1, "prnewswire": 1},
            source_lane_caps={"businesswire": 4, "globenewswire": 1, "prnewswire": 1},
            concurrency=4,
            rebalance_priority=["businesswire", "prnewswire", "globenewswire"],
        )
        self.assertEqual(lanes, {"businesswire": 3, "prnewswire": 1})


if __name__ == "__main__":
    unittest.main()
