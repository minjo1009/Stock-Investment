from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1318_1337_full_candidate_source_extractors"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1318To1337FullCandidateSourceExtractorsTest(unittest.TestCase):
    def test_full_candidate_rows_are_present(self) -> None:
        self.assertEqual(3100, len(read_csv(OUT_DIR / "task1319_full_candidate_source_plan.csv")))
        self.assertEqual(3100, len(read_csv(OUT_DIR / "task1324_candidate_l1_source_bindings.csv")))
        self.assertEqual(3100, len(read_csv(OUT_DIR / "task1325_candidate_l2_interpretation.csv")))
        self.assertEqual(3100, len(read_csv(OUT_DIR / "task1327_full_candidate_readiness_panel.csv")))

    def test_l3_edges_cover_each_candidate(self) -> None:
        rows = read_csv(OUT_DIR / "task1326_candidate_l3_evidence_edges.csv")
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["candidate_source_id"]] = counts.get(row["candidate_source_id"], 0) + 1
            self.assertEqual("0", row["assignment_uses_future_outcome"])
            self.assertEqual("0", row["selection_use_allowed"])
            self.assertEqual("0", row["replay_use_allowed"])
        self.assertEqual(3100, len(counts))
        self.assertTrue(all(count == 6 for count in counts.values()))

    def test_gate_preserves_diagnostic_status(self) -> None:
        gate = read_csv(OUT_DIR / "task1329_candidate_replacement_readiness_gate.csv")[0]
        self.assertEqual("1", gate["ready_for_candidate_replacement_preregistration"])
        self.assertEqual("0", gate["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])


if __name__ == "__main__":
    unittest.main()
