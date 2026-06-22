from __future__ import annotations

import unittest

import pandas as pd

from src.app.task_601_3_portfolio_selection_layer import (
    PortfolioSelectionConfig,
    select_portfolio_candidates,
)


def _row(candidate_id: str, symbol: str, generated_time: str, rank_score: float, stage: str, eligibility: str = "ELIGIBLE", skip_reason: str = "") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "generated_time": generated_time,
        "rank_score": rank_score,
        "eligibility": eligibility,
        "cooldown_reason": "",
        "skip_reason": skip_reason,
        "order_id": f"order-{candidate_id}" if stage in {"ORDERED", "FILLED"} else "",
        "fill_id": f"fill-{candidate_id}" if stage == "FILLED" else "",
        "source_snapshot_id": f"snapshot-{candidate_id}",
        "decision_id": candidate_id,
        "created_at": generated_time,
        "stage": stage,
        "proximity_fallback_used_flag": 0,
    }


def _representative_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    old_distribution = [("AMD", 5, 0.52), ("AMZN", 4, 0.53), ("MSFT", 3, 0.56)]
    day = 1
    for symbol, count, score in old_distribution:
        for idx in range(count):
            rows.append(_row(f"old-{symbol}-{idx}", symbol, f"2026-05-{day:02d}T14:30:00Z", score, "FILLED"))
            day += 1

    candidates = [
        ("AMD", 0.52),
        ("AMZN", 0.53),
        ("MSFT", 0.56),
        ("NVDA", 0.52),
    ]
    for offset in range(3):
        for symbol, score in candidates:
            rows.append(_row(f"new-{symbol}-{offset}", symbol, f"2026-06-{offset + 1:02d}T14:30:00Z", score, "GENERATED"))
    return pd.DataFrame(rows)


class Task6013PortfolioSelectionLayerTest(unittest.TestCase):
    def test_representative_fixture_reduces_top3_share_below_080(self) -> None:
        result = select_portfolio_candidates(
            _representative_fixture(),
            config=PortfolioSelectionConfig(max_positions=12, same_symbol_weight_cap=0.25),
        )

        metric = result.metrics.iloc[0]
        self.assertLess(metric["top3_share_after"], 0.80)
        self.assertEqual(metric["top3_share_after"], 0.75)

    def test_representative_fixture_increases_symbol_entropy(self) -> None:
        result = select_portfolio_candidates(
            _representative_fixture(),
            config=PortfolioSelectionConfig(max_positions=12, same_symbol_weight_cap=0.25),
        )

        metric = result.metrics.iloc[0]
        self.assertGreater(metric["symbol_entropy_after"], metric["symbol_entropy_before"])

    def test_every_selected_and_rejected_candidate_has_explanation(self) -> None:
        result = select_portfolio_candidates(
            _representative_fixture(),
            config=PortfolioSelectionConfig(max_positions=12, same_symbol_weight_cap=0.25),
        )

        decisions = result.decisions
        self.assertEqual(result.metrics.iloc[0]["explanation_coverage"], 1.0)
        self.assertTrue(decisions["explanation"].astype(str).str.len().gt(0).all())
        self.assertTrue(decisions["selection_decision"].isin(["SELECTED", "REJECTED"]).all())
        for column in [
            "rank_score",
            "liquidity_score",
            "diversification_score",
            "cooldown_score",
            "existing_position_penalty",
        ]:
            self.assertIn(column, decisions.columns)


if __name__ == "__main__":
    unittest.main()
