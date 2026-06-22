from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1338_1357_full_candidate_replacement_replay"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1338To1357FullCandidateReplacementReplayTest(unittest.TestCase):
    def test_rank_panel_covers_full_candidates(self) -> None:
        rows = read_csv(OUT_DIR / "task1339_l4_replacement_rank_panel.csv")
        self.assertEqual(3100, len(rows))
        decisions: dict[str, list[int]] = {}
        for row in rows:
            self.assertEqual("0", row["assignment_uses_future_outcome"])
            decisions.setdefault(row["decision_asof_ts"], []).append(int(row["replacement_rank_within_decision"]))
        self.assertEqual(62, len(decisions))
        self.assertTrue(all(sorted(ranks) == list(range(1, 51)) for ranks in decisions.values()))

    def test_policy_counts_match_slot_caps(self) -> None:
        specs = read_csv(OUT_DIR / "task1340_l5_replacement_policy_specs.csv")
        selected: dict[str, int] = {}
        for row in specs:
            selected[row["policy_variant_id"]] = selected.get(row["policy_variant_id"], 0) + int(row["selected_for_replay"])
        self.assertEqual(186, selected["full_candidate_l2l3_replace_top3_v1"])
        self.assertEqual(310, selected["full_candidate_l2l3_replace_top5_v1"])
        self.assertEqual(620, selected["full_candidate_l2l3_replace_top10_v1"])

    def test_acceptance_status_is_not_changed(self) -> None:
        gate = read_csv(OUT_DIR / "task1346_acceptance_gate.csv")[0]
        self.assertEqual("full_candidate_l2l3_replace_top10_v1", gate["best_policy_variant_id"])
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])


if __name__ == "__main__":
    unittest.main()
