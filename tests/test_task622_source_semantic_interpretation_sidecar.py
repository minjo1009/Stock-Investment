from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task622_source_semantic_interpretation_sidecar import (
    SCHEMA_FIELDS,
    build_task622_source_semantic_interpretation_sidecar,
)


class Task622SourceSemanticInterpretationSidecarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task622_source_semantic_interpretation_sidecar()

    def test_decision_keeps_semantic_layer_evaluation_only(self) -> None:
        decision = self.artifacts["task_622_decision"].iloc[0]

        self.assertEqual(decision["decision"], "IMPLEMENT_SEMANTIC_SOURCE_SIDECAR_FAIL_AEROSPACE_CERTIFICATION")
        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["semantic_labels_used_in_assignment_flag"]), 0)
        self.assertEqual(int(decision["trading_promotion_pass_flag"]), 0)

    def test_schema_fields_are_complete(self) -> None:
        labels = self.artifacts["source_semantic_labels"]
        pass_fail = self.artifacts["task_622_pass_fail_matrix"]
        gate = pass_fail[pass_fail["gate"].eq("schema_fields_complete")].iloc[0]

        self.assertTrue(set(SCHEMA_FIELDS).issubset(labels.columns))
        self.assertEqual(int(gate["pass_flag"]), 1)

    def test_generic_filings_and_broad_events_cannot_support_entry(self) -> None:
        labels = self.artifacts["source_semantic_labels"]
        generic_support = labels[
            labels["evidence_quality"].astype(str).isin(["generic_filing_only", "generic_filing_or_ownership_only"])
            & labels["actionability"].astype(str).eq("support_entry")
        ]
        broad_support = labels[
            labels["catalyst_economic_link"].astype(str).eq("broad_policy_or_geopolitical_background")
            & labels["actionability"].astype(str).eq("support_entry")
        ]

        self.assertTrue(generic_support.empty)
        self.assertTrue(broad_support.empty)

    def test_recent_aerospace_has_no_company_direct_support_certification(self) -> None:
        recent = self.artifacts["recent_aerospace_semantic_attachment"]
        decision = self.artifacts["task_622_decision"].iloc[0]

        self.assertGreater(len(recent), 0)
        self.assertEqual(int(recent["company_direct_support_entry_count"].sum()), 0)
        self.assertEqual(int(decision["recent_aerospace_source_certification_pass_flag"]), 0)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task622_source_semantic_interpretation_sidecar(out_dir=out_dir)

            self.assertTrue((out_dir / "task_622_source_semantic_interpretation_sidecar.md").exists())
            self.assertTrue((out_dir / "source_semantic_labels.csv").exists())
            self.assertTrue((out_dir / "recent_aerospace_semantic_attachment.csv").exists())
            self.assertTrue((out_dir / "task_622_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["source_semantic_labels"]), 100)


if __name__ == "__main__":
    unittest.main()
