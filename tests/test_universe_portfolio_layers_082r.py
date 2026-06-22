from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestUniversePortfolioLayers082R(unittest.TestCase):
    def test_universe_sector_ranking_allocator_pipeline(self) -> None:
        from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_universe_daily_bars
        from portfolio.allocator import allocate_equal_weight
        from sector.sector_model import build_sector_snapshot
        from universe.ranking import rank_universe
        from universe.universe_selector import build_universe_snapshot, filter_universe_snapshot

        symbols = list(DEFAULT_US_UNIVERSE)[:6]
        frames = load_universe_daily_bars(symbols, base_dir=DEFAULT_BASE_DIR)
        snapshot = build_universe_snapshot(frames)
        self.assertGreater(len(snapshot), 0)
        filtered = filter_universe_snapshot(snapshot)
        ranked = rank_universe(filtered if not filtered.empty else snapshot)
        self.assertIn("score", ranked.columns)
        top = ranked["symbol"].head(3).tolist()
        allocation = allocate_equal_weight(top)
        self.assertGreaterEqual(len(allocation), 1)
        self.assertAlmostEqual(sum(float(row["allocation_pct"]) for row in allocation), 1.0, places=9)

        sector_snapshot = build_sector_snapshot(frames)
        self.assertGreaterEqual(len(sector_snapshot), 1)

    def test_engine_portfolio_mode_runs(self) -> None:
        from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE
        from backtest.engine_full import run_full_backtest_universe_with_stats

        symbols = list(DEFAULT_US_UNIVERSE)
        results_single, stats_single = run_full_backtest_universe_with_stats(
            symbols=symbols,
            base_dir=DEFAULT_BASE_DIR,
            initial_equity=100_000.0,
            fee_rate=0.0025,
            slippage_rate=0.0010,
            entry_policy="LIMITED_CHASE",
            risk_policy="TIME_STOP_ONLY",
            mode="single_symbol",
            max_positions=3,
        )
        results_portfolio, stats_portfolio = run_full_backtest_universe_with_stats(
            symbols=symbols,
            base_dir=DEFAULT_BASE_DIR,
            initial_equity=100_000.0,
            fee_rate=0.0025,
            slippage_rate=0.0010,
            entry_policy="LIMITED_CHASE",
            risk_policy="TIME_STOP_ONLY",
            mode="portfolio",
            max_positions=3,
        )
        self.assertGreaterEqual(len(results_single), len(results_portfolio))
        self.assertGreaterEqual(stats_single.total_signals, stats_portfolio.total_signals)


if __name__ == "__main__":
    unittest.main()
