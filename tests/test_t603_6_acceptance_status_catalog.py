from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_acceptance_status_catalog import (
    REQUIRED_CARD_TITLES,
    build_acceptance_status_catalog,
    write_acceptance_status_catalog,
)


class T6036AcceptanceStatusCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = build_acceptance_status_catalog(Path("."))

    def test_required_catalog_fields_and_banner_values(self) -> None:
        payload = self.payload
        for field in [
            "paper_status",
            "strategy_status",
            "deployment_status",
            "real_capital_status",
            "top_blockers",
            "acceptance_progress",
            "owner_actions",
            "last_updated",
        ]:
            self.assertIn(field, payload)
        self.assertEqual(payload["paper_status"], "READY_FOR_CONTROLLED_PAPER_RUN")
        self.assertEqual(payload["strategy_status"], "NOT_ACCEPTED")
        self.assertEqual(payload["deployment_status"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(payload["real_capital_status"], "FORBIDDEN")
        self.assertEqual(payload["banner_values"]["Paper"], "READY_FOR_CONTROLLED_PAPER_RUN")
        self.assertEqual(payload["banner_values"]["Strategy"], "NOT_ACCEPTED")
        self.assertEqual(payload["banner_values"]["Deployment"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        self.assertEqual(payload["banner_values"]["Real Capital"], "FORBIDDEN")

    def test_first_screen_cards_cover_required_status_surfaces(self) -> None:
        cards = self.payload["first_screen_cards"]
        titles = [card["title"] for card in cards]
        self.assertEqual(titles, REQUIRED_CARD_TITLES)
        by_title = {card["title"]: card for card in cards}
        self.assertEqual(by_title["Acceptance Status"]["value"], "NOT_ACCEPTED")
        self.assertIn("FAIL_BROKER_TRUTH_SELL_ZERO", by_title["Broker Truth Coverage"]["value"])
        self.assertIn("REVIEW_ORDER_STRETCH_POSITION_BELOW_99", by_title["Replay Health"]["value"])
        self.assertEqual(by_title["Risk Snapshot Coverage"]["value"], "FAIL")
        self.assertIn("PASS_MULTI_SESSION_STABILITY_REVIEW", by_title["Concentration Health"]["value"])
        self.assertIn("P0_EXIT_LIFECYCLE", by_title["Top Blockers"]["note"])

    def test_owner_actions_preserve_blocker_provenance(self) -> None:
        actions = self.payload["owner_actions"]
        self.assertGreater(len(actions), 0)
        first = actions[0]
        for field in ["blocker_id", "priority", "owner", "team", "status", "next_gate", "artifact", "validation"]:
            self.assertIn(field, first)
        self.assertEqual(first["priority"], "P0")

    def test_write_catalog_outputs_app_and_frontend_data_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_a = Path(tmp) / "frontend_data" / "catalog"
            out_b = Path(tmp) / "public" / "catalog"
            write_acceptance_status_catalog(self.payload, [out_a, out_b])
            for output in [out_a, out_b]:
                written = output / "acceptance_status_catalog.json"
                self.assertTrue(written.exists())
                loaded = json.loads(written.read_text(encoding="utf-8"))
                self.assertEqual(loaded["contract_version"], "acceptance-status-catalog-v1")
                self.assertEqual(loaded["real_capital_status"], "FORBIDDEN")
                json.dumps(loaded, allow_nan=False)

    def test_frontend_loads_acceptance_catalog_on_first_screen(self) -> None:
        app = Path("frontend/trader-terminal/src/App.jsx").read_text(encoding="utf-8")
        self.assertIn("/catalog/acceptance_status_catalog.json", app)
        self.assertIn("AcceptanceStatusPanel", app)
        self.assertIn("acceptance_status_catalog", app)


if __name__ == "__main__":
    unittest.main()
