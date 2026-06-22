from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBrainRuntimeCatalogAdapter(unittest.TestCase):
    def _payload(self):
        return {
            "contract_version": "paper-ops-runtime-v1",
            "rules": {
                "ui_reads_catalog_only": True,
                "deployment_claim_allowed": False,
                "missing_source_approximation_allowed": False,
            },
            "data_quality": {
                "data_quality_status": "PARTIAL",
                "data_quality_flags": ["PARTIAL_RUNTIME_EVIDENCE"],
            },
            "policy_compare_audit": {
                "strict_asof_status": "BLOCKED",
            },
        }

    def test_build_frontend_read_model_is_read_only(self) -> None:
        from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog

        read_model = build_frontend_read_model_from_paper_ops_catalog(
            self._payload(),
            read_model_id="read-model-1",
            runtime_decision_id="runtime-1",
            provenance_path="frontend/trader-terminal/public/catalog/paper_ops_runtime_catalog.json",
        )

        self.assertTrue(read_model.read_only)
        self.assertEqual(read_model.source_tier, "paper_shadow_runtime_catalog")
        self.assertEqual(read_model.display_status, "PARTIAL")
        self.assertIn("PARTIAL_RUNTIME_EVIDENCE", read_model.blocker_flags)
        self.assertIn("STRICT_ASOF_BLOCKED", read_model.blocker_flags)

    def test_rejects_deployment_claim_catalogs(self) -> None:
        from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog

        payload = self._payload()
        payload["rules"]["deployment_claim_allowed"] = True

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_paper_ops_catalog(
                payload,
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                provenance_path="paper_ops_runtime_catalog.json",
            )

    def test_rejects_missing_source_approximation(self) -> None:
        from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog

        payload = self._payload()
        payload["rules"]["missing_source_approximation_allowed"] = True

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_paper_ops_catalog(
                payload,
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                provenance_path="paper_ops_runtime_catalog.json",
            )

    def test_rejects_invalid_contract_version(self) -> None:
        from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog

        payload = self._payload()
        payload["contract_version"] = "paper-ops-runtime-v0"

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_paper_ops_catalog(
                payload,
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                provenance_path="paper_ops_runtime_catalog.json",
            )

    def test_rejects_catalogs_that_do_not_force_ui_catalog_reads(self) -> None:
        from brain.runtime_catalog import build_frontend_read_model_from_paper_ops_catalog

        payload = self._payload()
        payload["rules"]["ui_reads_catalog_only"] = False

        with self.assertRaises(ValueError):
            build_frontend_read_model_from_paper_ops_catalog(
                payload,
                read_model_id="read-model-1",
                runtime_decision_id="runtime-1",
                provenance_path="paper_ops_runtime_catalog.json",
            )

    def test_contract_version_matches_catalog_builder_literal(self) -> None:
        from brain.runtime_catalog import PAPER_OPS_RUNTIME_CONTRACT_VERSION

        builder_text = (ROOT / "scripts" / "build_trader_terminal_catalog.py").read_text(encoding="utf-8")

        self.assertEqual(PAPER_OPS_RUNTIME_CONTRACT_VERSION, "paper-ops-runtime-v1")
        self.assertIn(f'"contract_version": "{PAPER_OPS_RUNTIME_CONTRACT_VERSION}"', builder_text)


if __name__ == "__main__":
    unittest.main()
