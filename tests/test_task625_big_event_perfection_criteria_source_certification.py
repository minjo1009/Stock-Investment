from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task625_big_event_perfection_criteria_source_certification import (
    build_task625_big_event_perfection_criteria_source_certification,
)


def fake_fetcher(url: str) -> tuple[int, str, str]:
    text = (
        "Russia Iran Counterterrorism Non-Proliferation Designations "
        "official source text certification body with enough repeated words. "
        "This source text is deliberately long enough for certification. "
    ) * 20
    return 200, url, text


class Task625BigEventPerfectionCriteriaSourceCertificationTest(unittest.TestCase):
    def test_fake_official_text_certifies_nonzero_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "report"
            raw_dir = Path(tmp) / "raw"
            artifacts = build_task625_big_event_perfection_criteria_source_certification(
                out_dir=out_dir,
                raw_text_dir=raw_dir,
                max_events=3,
                fetcher=fake_fetcher,
            )

            decision = artifacts["task_625_decision"].iloc[0]
            cert = artifacts["task_625_source_certification_matrix"]
            criteria = artifacts["task_625_perfection_criteria_matrix"]

            self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
            self.assertEqual(int(cert["source_text_certified_flag"].sum()), 3)
            self.assertEqual(int(cert["source_presence_only_used_flag"].sum()), 0)
            self.assertEqual(int(cert["gpt_score_used_as_source_flag"].sum()), 0)
            self.assertEqual(
                int(criteria[criteria["gate"].eq("nonzero_scores_have_certified_source_text")]["pass_flag"].iloc[0]),
                1,
            )
            self.assertTrue((out_dir / "task_625_big_event_perfection_criteria_source_certification.md").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(list(raw_dir.glob("*.txt"))), 0)


if __name__ == "__main__":
    unittest.main()
