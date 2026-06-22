from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_895_l1_source_attachment_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_895_l1_source_attachment"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain895L1SourceAttachmentTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_local_lineage_attached_without_raw_external_claim(self) -> None:
        ledger = rows("l1_source_attachment_ledger.csv")
        self.assertEqual(139, len(ledger))
        self.assertEqual({"local_lineage_bundle_attached"}, {row["local_attachment_state"] for row in ledger})
        self.assertEqual({"missing"}, {row["raw_external_document_state"] for row in ledger})
        self.assertEqual({"LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE"}, {row["attachment_authority"] for row in ledger})

    def test_no_trading_fields_in_attachment_outputs(self) -> None:
        forbidden = {"side", "entry", "exit", "position_size", "rank", "score", "raw_trade_id"}
        ledger_header = set(rows("l1_source_attachment_ledger.csv")[0].keys())
        enriched_header = set(rows("l1_source_evidence_seed_with_attachments.csv")[0].keys())
        self.assertTrue(forbidden.isdisjoint(ledger_header))
        self.assertTrue(forbidden.isdisjoint(enriched_header))

    def test_raw_source_acquisition_queue_covers_universe(self) -> None:
        queue = rows("raw_source_attachment_acquisition_queue.csv")
        self.assertEqual(70, len(queue))
        self.assertIn("attach_raw_external_document_to_existing_l1_seed", {row["implementation_step"] for row in queue})
        self.assertIn("collect_source_time_seed_then_attach_raw_external_document", {row["implementation_step"] for row in queue})


if __name__ == "__main__":
    unittest.main()
