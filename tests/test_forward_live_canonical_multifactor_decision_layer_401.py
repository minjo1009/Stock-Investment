from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_canonical_multifactor_decision_layer_401 import (
    build_forward_live_canonical_multifactor_decision_layer_401,
)
from src.backtest.intraday_canonical_continuation_engine_388 import IntradayContinuationConfig
from src.backtest.canonical_position_lifecycle_event_sourcing import list_canonical_position_events


class TestForwardLiveCanonicalMultiFactorDecisionLayer401(unittest.TestCase):
    def test_runtime_writes_pre_event_snapshots_and_explicit_lifecycles(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intraday = root / "intraday"
            intraday.mkdir()
            _bars("AAA").to_csv(intraday / "AAA.csv", index=False, encoding="utf-8-sig")
            _bars("BBB", weak=True).to_csv(intraday / "BBB.csv", index=False, encoding="utf-8-sig")
            universe = root / "universe.csv"
            pd.DataFrame(
                [
                    {"theme": "ai_semiconductors", "symbol": "AAA", "role": "leader"},
                    {"theme": "cloud_ai_platforms", "symbol": "BBB", "role": "expanded_candidate"},
                ]
            ).to_csv(universe, index=False, encoding="utf-8-sig")

            artifacts = build_forward_live_canonical_multifactor_decision_layer_401(
                intraday_dir=intraday,
                theme_universe_path=universe,
                out_dir=root / "out",
                db_path=root / "store.db",
                symbols=["AAA", "BBB"],
                config=IntradayContinuationConfig(
                    breakout_lookback=3,
                    max_holding_bars=6,
                    add_return_threshold=0.005,
                    scale_return_threshold=0.01,
                    reduce_drawdown_from_high=0.02,
                    exit_drawdown_from_high=0.04,
                    persist_to_store=True,
                ),
            )

            decision_log = artifacts.multifactor_decision_snapshot_log
            self.assertGreater(len(decision_log), 0)
            for blocked in ["return_from_entry", "net_return_from_entry", "add_flag", "scale_flag", "reduce_flag", "exit_reason", "failure_group"]:
                self.assertNotIn(blocked, decision_log.columns)
            self.assertEqual(int(artifacts.multifactor_leakage_audit["leakage_pass_flag"].min()), 1)
            self.assertEqual(int(artifacts.decision_ordering_invariant_audit.iloc[0]["ordering_pass_flag"]), 1)

            accepted = artifacts.multifactor_accepted_lifecycle_event_log
            self.assertGreater(int(accepted["event_type"].eq("ENTRY").sum()), 0)
            entry = accepted[accepted["event_type"].eq("ENTRY")].iloc[0]
            events = list_canonical_position_events(str(root / "store.db"), lifecycle_id=str(entry["lifecycle_id"]))
            self.assertEqual(events[0]["canonical_event_type"], "ENTRY")
            self.assertIn("decision_id", str(events[0]["details_json"]))
            self.assertTrue((root / "out" / "task_401_forward_live_canonical_multifactor_decision_layer.md").exists())

    def test_offline_bucket_quality_is_separate_from_online_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intraday = root / "intraday"
            intraday.mkdir()
            _bars("AAA").to_csv(intraday / "AAA.csv", index=False, encoding="utf-8-sig")
            universe = root / "universe.csv"
            pd.DataFrame([{"theme": "ai_semiconductors", "symbol": "AAA", "role": "leader"}]).to_csv(universe, index=False, encoding="utf-8-sig")

            artifacts = build_forward_live_canonical_multifactor_decision_layer_401(
                intraday_dir=intraday,
                theme_universe_path=universe,
                out_dir=root / "out",
                symbols=["AAA"],
                config=IntradayContinuationConfig(
                    breakout_lookback=3,
                    max_holding_bars=6,
                    add_return_threshold=0.005,
                    scale_return_threshold=0.01,
                    persist_to_store=False,
                ),
            )

            self.assertIn("offline_label_only_flag", artifacts.multifactor_bucket_quality_offline_label_audit.columns)
            self.assertEqual(int(artifacts.task_401_decision.iloc[0]["label_offline_only_flag"]), 1)
            self.assertEqual(int(artifacts.task_401_decision.iloc[0]["deployment_claim_flag"]), 0)


def _bars(symbol: str, weak: bool = False) -> pd.DataFrame:
    timestamps = pd.date_range("2026-01-02T14:30:00Z", periods=12, freq="15min")
    if weak:
        closes = [100, 99.8, 99.6, 99.4, 99.2, 99.0, 98.8, 98.6, 98.4, 98.2, 98.0, 97.8]
    else:
        closes = [100, 100.4, 100.8, 101.2, 102.0, 103.0, 103.8, 104.2, 103.0, 102.5, 102.2, 102.0]
    rows = []
    for i, close in enumerate(closes):
        rows.append(
            {
                "timestamp": timestamps[i].isoformat().replace("+00:00", "Z"),
                "open": close - 0.8,
                "high": close + 0.6,
                "low": close - 1.2,
                "close": close,
                "volume": 100000 + i * 10000,
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    unittest.main()
