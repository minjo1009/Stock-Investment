from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1358_1377_trader_judgment_core_recovery"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1358To1377TraderJudgmentCoreRecoveryTest(unittest.TestCase):
    def test_l2_l3_l4_contract_shapes(self) -> None:
        primitives = read_csv(OUT_DIR / "task1361_l2_materiality_surprise_primitives.csv")
        mechanisms = read_csv(OUT_DIR / "task1362_l3_mechanism_edges.csv")
        ranks = read_csv(OUT_DIR / "task1363_l4_payoff_rank_panel.csv")
        self.assertEqual(3100, len(primitives))
        self.assertEqual(15500, len(mechanisms))
        self.assertEqual(3100, len(ranks))
        self.assertTrue(all(row["assignment_uses_future_outcome"] == "0" for row in primitives))
        self.assertTrue(all(row["assignment_uses_future_outcome"] == "0" for row in mechanisms))
        self.assertTrue(all(row["assignment_uses_future_outcome"] == "0" for row in ranks))

    def test_policy_counts_and_dynamic_exit_receipts(self) -> None:
        specs = read_csv(OUT_DIR / "task1367_l5_policy_specs.csv")
        selected: dict[str, int] = {}
        for row in specs:
            selected[row["policy_variant_id"]] = selected.get(row["policy_variant_id"], 0) + int(row["selected_for_replay"])
        self.assertEqual(310, selected["payoff_core_top5_v1"])
        self.assertEqual(620, selected["payoff_core_top10_v1"])
        self.assertEqual(620, selected["payoff_hurdle_top10_v1"])

        exits = read_csv(OUT_DIR / "task1364_l5_dynamic_exit_receipts.csv")
        trades = read_csv(OUT_DIR / "task1368_replay_trades.csv")
        ready_count = sum(1 for row in exits if row["dynamic_exit_ready"] == "1")
        dynamic_trade_count = sum(1 for row in trades if row["exit_reason"] == "dynamic_exit_post_entry_hard_sec_event")
        self.assertGreaterEqual(ready_count, 1)
        self.assertEqual(ready_count, dynamic_trade_count)

    def test_replacement_audit_is_outcome_only(self) -> None:
        rows = read_csv(OUT_DIR / "task1360_replacement_pair_audit.csv")
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(row["outcome_used_for_assignment"] == "0" for row in rows))
        self.assertTrue(all(row["outcome_used_for_audit_only"] == "1" for row in rows))

    def test_acceptance_status_is_not_changed(self) -> None:
        gate = read_csv(OUT_DIR / "task1372_acceptance_gate.csv")[0]
        self.assertEqual("payoff_core_top5_v1", gate["best_policy_variant_id"])
        self.assertEqual("NOT_ACCEPTED", gate["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", gate["deployment_readiness"])
        self.assertEqual("FORBIDDEN", gate["real_capital"])
        self.assertEqual("diagnostic_core_recovery_not_accepted", gate["decision"])


if __name__ == "__main__":
    unittest.main()
