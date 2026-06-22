from __future__ import annotations

import csv
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1388_1407_expert_reviewed_judgment_replay"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1388To1407ExpertReviewedJudgmentReplayTest(unittest.TestCase):
    def test_expert_loop_and_panels_exist(self) -> None:
        draft = read_csv(OUT_DIR / "task1388_formula_draft.csv")
        critique = read_csv(OUT_DIR / "task1389_expert_critique_matrix.csv")
        expectation = read_csv(OUT_DIR / "task1390_expectation_gap_panel.csv")
        materiality = read_csv(OUT_DIR / "task1391_materiality_denominator_panel.csv")
        self.assertEqual(8, len(draft))
        self.assertGreaterEqual(len({row["expert_role"] for row in critique}), 10)
        self.assertEqual(3100, len(expectation))
        self.assertEqual(3100, len(materiality))
        self.assertTrue(all(row["analyst_source_gap"] == "1" for row in expectation))
        self.assertTrue(all(row["denominator_missing_score_increase_allowed"] == "0" for row in materiality))

    def test_l3_l4_shape_and_no_future_assignment(self) -> None:
        enriched = read_csv(OUT_DIR / "task1394_l2_enriched_judgment_panel.csv")
        edges = read_csv(OUT_DIR / "task1394_l3_mechanism_edges_v2.csv")
        ranks = read_csv(OUT_DIR / "task1395_l4_payoff_ranker_v2.csv")
        self.assertEqual(3100, len(enriched))
        self.assertEqual(15500, len(edges))
        self.assertEqual(3100, len(ranks))
        self.assertTrue(all(row["assignment_uses_future_outcome"] == "0" for row in enriched))
        by_decision: dict[str, list[int]] = {}
        for row in ranks:
            by_decision.setdefault(row["decision_asof_ts"], []).append(int(row["expert_payoff_rank_within_decision"]))
        self.assertEqual(62, len(by_decision))
        self.assertTrue(all(sorted(values) == list(range(1, 51)) for values in by_decision.values()))

    def test_policy_counts_and_dynamic_exit_expansion(self) -> None:
        specs = read_csv(OUT_DIR / "task1396_l5_policy_specs_v2.csv")
        selected: Counter[str] = Counter()
        for row in specs:
            selected[row["policy_variant_id"]] += int(row["selected_for_replay"])
        self.assertEqual(310, selected["expert_payoff_top5_v2"])
        self.assertEqual(620, selected["expert_payoff_top10_v2"])
        self.assertEqual(620, selected["expert_hurdle_top10_v2"])

        receipts = read_csv(OUT_DIR / "task1396_dynamic_exit_receipts_v2.csv")
        trades = read_csv(OUT_DIR / "task1397_replay_trades.csv")
        ready_count = sum(1 for row in receipts if row["dynamic_exit_ready"] == "1")
        dynamic_trade_count = sum(1 for row in trades if row["exit_reason"] != "scheduled_exit")
        self.assertGreaterEqual(ready_count, 100)
        self.assertEqual(ready_count, dynamic_trade_count)

    def test_acceptance_status_is_not_changed(self) -> None:
        gate = read_csv(OUT_DIR / "task1404_acceptance_gate.csv")[0]
        self.assertEqual("expert_payoff_top5_v2", gate["best_policy_variant_id"])
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])
        self.assertEqual("diagnostic_expert_reviewed_replay_not_accepted", gate["decision"])


if __name__ == "__main__":
    unittest.main()
