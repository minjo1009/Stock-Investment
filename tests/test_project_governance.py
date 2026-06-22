from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts.codeowners_coverage_validate import validate as validate_codeowners
from scripts.governance_completion_audit import audit as governance_audit
from scripts.task_artifact_manifest import build_manifest, write_manifest
from scripts.task_registry_validate import validate_registry
from src.backtest.core.cost_stress import cost_stress_quality
from src.backtest.core.leakage import assignment_leakage_audit
from src.backtest.core.metrics import lifecycle_quality
from src.backtest.reports.standard_report import StandardReport


ROOT = Path(__file__).resolve().parents[1]


class ProjectGovernanceTest(unittest.TestCase):
    def test_task_registry_and_codeowners_are_valid(self) -> None:
        registry_errors = validate_registry(ROOT / "tasks" / "task_registry.csv", root=ROOT)
        self.assertEqual(registry_errors, [])
        codeowners_errors = validate_codeowners(ROOT / ".github" / "CODEOWNERS")
        self.assertEqual(codeowners_errors, [])
        self.assertEqual(governance_audit(ROOT), [])

    def test_artifact_manifest_classifies_large_and_decision_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / "task_x"
            task_dir.mkdir()
            (task_dir / "task_x_decision.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (task_dir / "task_x.md").write_text("# report\n", encoding="utf-8")
            (task_dir / "panel.csv").write_text("x\n1\n", encoding="utf-8")
            rows = build_manifest(task_dir)
            classes = {row["relative_path"]: row["artifact_class"] for row in rows}
            self.assertEqual(classes["task_x_decision.csv"], "decision")
            self.assertEqual(classes["task_x.md"], "report")
            out = task_dir / "artifact_manifest.csv"
            write_manifest(task_dir, out)
            self.assertTrue(out.exists())

    def test_shared_backtest_core_utilities(self) -> None:
        frame = pd.DataFrame(
            {
                "lifecycle_id": ["L1", "L2"],
                "net_return_from_entry": [0.03, -0.01],
                "win_flag": [1, 0],
                "add_scale_success_flag": [1, 0],
                "entry_reduce_failure_flag": [0, 1],
                "false_positive_flag": [0, 1],
            }
        )
        quality = lifecycle_quality(frame)
        self.assertEqual(quality["lifecycle_count"], 2)
        self.assertAlmostEqual(float(quality["avg_net_return_pct"]), 1.0)
        stress = cost_stress_quality(frame)
        self.assertIn("additional_50bp_round_trip_cost", set(stress["cost_stress_name"]))
        leakage = assignment_leakage_audit(["spread_state", "net_return_from_entry"])
        self.assertEqual(int(leakage.iloc[0]["leakage_pass_flag"]), 0)

    def test_standard_report_has_required_sections(self) -> None:
        report = StandardReport(
            title="Task X",
            decision_summary=["- Verdict: TEST"],
            quant_expert_report=["- Metrics checked"],
            decision_maker_report=["- Plain language"],
            artifact_manifest=pd.DataFrame([{"path": "x", "rows": 1}]),
        ).render()
        self.assertIn("## Decision Summary", report)
        self.assertIn("## Quant Expert Report", report)
        self.assertIn("## No-Background Decision-Maker Report", report)
        self.assertIn("## Artifact Manifest", report)


if __name__ == "__main__":
    unittest.main()
