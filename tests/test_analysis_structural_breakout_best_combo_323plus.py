from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODULE = "src.backtest.analysis_structural_breakout_best_combo_323plus"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    return env


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", MODULE, *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=_env(),
    )


class TestAnalysisStructuralBreakoutBestCombo323Plus(unittest.TestCase):
    def test_help_smoke(self) -> None:
        proc = _run(["--help"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Task 323+ best structural breakout combo evaluation", proc.stdout)

    def test_scenario_parser_roundtrip(self) -> None:
        from src.backtest.analysis_structural_breakout_322 import StructuralConfig, _scenario_name
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _config_from_scenario

        cfg = StructuralConfig(
            structure_mode="RANGE_COMPRESSION",
            stop_mode="ATR_STOP",
            atr_multiplier=2.5,
            max_holding_days=30,
            range_lookback=10,
            max_range_width_pct=0.15,
        )
        scenario = _scenario_name(cfg)
        parsed = _config_from_scenario(scenario)
        self.assertEqual(_scenario_name(parsed), scenario)

    def test_recent_six_month_window_uses_calendar_months(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _recent_six_month_window

        start, end = _recent_six_month_window(pd.Timestamp("2026-04-29", tz="UTC"))
        self.assertEqual(str(start.date()), "2025-11-01")
        self.assertEqual(str(end.date()), "2026-04-29")

    def test_preloaded_symbol_filter_excludes_removed_symbols(self) -> None:
        from src.backtest.analysis_structural_breakout_322 import (
            DEFAULT_BASE_DIR,
            StructuralConfig,
            _prepare_preloaded_frames,
            run_structural_backtest,
        )

        base_dir = Path(DEFAULT_BASE_DIR)
        symbols = ["AAPL", "AMD", "NVDA"]
        frames, timestamps = _prepare_preloaded_frames(base_dir, symbols)
        cfg = StructuralConfig(structure_mode="LONG_DONCHIAN", donchian_n=20, atr_multiplier=2.0, max_holding_days=20)
        result = run_structural_backtest(
            cfg,
            base_dir,
            preloaded_frames=frames,
            preloaded_timestamps=timestamps,
            preloaded_symbols=["AAPL"],
        )
        self.assertEqual(result["symbols"], ["AAPL"])
        traded_symbols = {str(row["symbol"]) for row in result["trade_log"]}
        self.assertTrue(traded_symbols.issubset({"AAPL"}))

    def test_select_mixed_top3_returns_exactly_three(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _select_mixed_top3

        balanced = pd.DataFrame({"scenario": ["A", "B", "C"], "sharpe": [3, 2, 1]})
        cagr = pd.DataFrame({"scenario": ["B", "D", "E"], "cagr_pct": [30, 25, 20]})
        reps = {"A": "A", "B": "B", "C": "C", "D": "D", "E": "E"}
        selected = _select_mixed_top3(balanced, cagr, reps)
        self.assertEqual(len(selected), 3)
        self.assertEqual([row["selection_group"] for row in selected], ["BALANCED", "BALANCED", "CAGR"])

    def test_entry_type_classification(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _entry_type_of_trade

        self.assertEqual(_entry_type_of_trade({"filled_at_open": True}), "gap_open_fill")
        self.assertEqual(_entry_type_of_trade({"filled_at_open": False}), "planned_breakout_fill")

    def test_regime_lookup_uses_shifted_values(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_market_regime_lookup
        from src.backtest.data_loader import DEFAULT_BASE_DIR

        lookup = _build_market_regime_lookup(Path(DEFAULT_BASE_DIR))
        self.assertIn("2021-05-03", lookup)
        self.assertIn(lookup["2021-05-03"]["market_regime_base"], {"risk_on", "risk_off"})
        self.assertIn(
            lookup["2021-05-03"]["market_regime_detail"],
            {"risk_off", "risk_on_healthy", "risk_on_overextended", "risk_on_high_vol_slowdown", "risk_on_cooling"},
        )

    def test_regime_split_is_mutually_exclusive_and_exhaustive(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _classify_market_regime

        base, detail = _classify_market_regime(
            pd.Series(
                {
                    "close_prev": 110.0,
                    "sma200_prev": 100.0,
                    "sma20_prev": 100.0,
                    "ret_5d_prev": 0.02,
                    "ret_20d_prev": 0.20,
                    "std5_prev": 0.02,
                    "std20_prev": 0.02,
                }
            )
        )
        self.assertEqual((base, detail), ("risk_on", "risk_on_overextended"))

    def test_recent_trade_frame_contains_anatomy_columns(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_symbol_feature_lookup, _recent_trade_frame
        from src.backtest.analysis_structural_breakout_322 import DEFAULT_BASE_DIR, _prepare_preloaded_frames

        base_dir = Path(DEFAULT_BASE_DIR)
        frames, _ = _prepare_preloaded_frames(base_dir, ["AAPL"])
        result = {
            "config": {
                "structure_mode": "LONG_DONCHIAN",
                "breakout_trigger_mode": "HIGH_TOUCH",
                "entry_model": "BREAKOUT_LEVEL_WITH_SLIPPAGE",
                "stop_mode": "ATR_STOP",
                "entry_bar_stop_mode": "DISABLE_ENTRY_BAR_STOP",
                "atr_multiplier": 2.0,
                "max_holding_days": 20,
                "min_avg_dollar_volume_20": 20_000_000.0,
                "donchian_n": 20,
            },
            "trade_log": [
                {
                    "symbol": "AAPL",
                    "entry_date": "2025-11-03",
                    "exit_date": "2025-11-10",
                    "realized_R": -1.0,
                    "filled_at_open": True,
                    "entry_open": 100.0,
                    "planned_entry_price": 99.0,
                }
            ],
        }
        regime_lookup = {"2025-11-03": {"market_regime_base": "risk_on", "market_regime_detail": "risk_on_healthy"}}
        symbol_lookup = _build_symbol_feature_lookup(frames)
        df = _recent_trade_frame(result, regime_lookup, symbol_lookup)
        for column in [
            "market_regime_base",
            "market_regime_detail",
            "ret_5d_pre",
            "ret_10d_pre",
            "ret_20d_pre",
            "dist_to_sma20_pct",
            "dist_to_sma50_pct",
            "dist_to_sma200_pct",
            "gap_from_prev_close_pct",
            "gap_over_planned_entry_pct",
            "vol_expansion_ratio",
            "atr_pct_pre",
        ]:
            self.assertIn(column, df.columns)

    def test_feature_summaries_emit_pooled_and_per_scenario_rows(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _feature_bin_breakdown, _feature_summary

        df = pd.DataFrame(
            [
                {"scenario": "A", "realized_R": -1.0, "ret_5d_pre": 0.06, "ret_10d_pre": 0.09, "ret_20d_pre": 0.15, "dist_to_sma20_pct": 0.04, "dist_to_sma50_pct": 0.05, "dist_to_sma200_pct": 0.10, "gap_from_prev_close_pct": 0.01, "gap_over_planned_entry_pct": 0.02, "vol_expansion_ratio": 1.3, "atr_pct_pre": 0.04},
                {"scenario": "B", "realized_R": -2.0, "ret_5d_pre": -0.01, "ret_10d_pre": 0.03, "ret_20d_pre": 0.08, "dist_to_sma20_pct": 0.01, "dist_to_sma50_pct": 0.02, "dist_to_sma200_pct": 0.03, "gap_from_prev_close_pct": -0.01, "gap_over_planned_entry_pct": 0.0, "vol_expansion_ratio": 0.9, "atr_pct_pre": 0.03},
            ]
        )
        summary = _feature_summary(df)
        bins = _feature_bin_breakdown(df)
        self.assertIn("ALL", set(summary["scenario"]))
        self.assertIn("A", set(summary["scenario"]))
        self.assertIn("ALL", set(bins["scenario"]))
        self.assertIn("B", set(bins["scenario"]))

    def test_feature_binning_is_deterministic_on_boundaries(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _assign_feature_bin, FEATURE_BIN_SPECS

        self.assertEqual(_assign_feature_bin(0.05, FEATURE_BIN_SPECS["ret_5d_pre"]), "5~10%")
        self.assertEqual(_assign_feature_bin(0.0, FEATURE_BIN_SPECS["gap_over_planned_entry_pct"]), "0~1%")

    def test_reclustered_regime_labels_are_valid(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_reclustered_regime_lookup
        from src.backtest.data_loader import DEFAULT_BASE_DIR

        lookup = _build_reclustered_regime_lookup(Path(DEFAULT_BASE_DIR))
        self.assertIn("2026-04-29", lookup)
        self.assertIn(
            lookup["2026-04-29"]["reclustered_regime"],
            {"risk_off", "early_trend", "strong_trend", "extended_trend", "exhaustion", "choppy"},
        )

    def test_winner_loser_comparison_has_stats_columns(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _winner_loser_comparison_table

        df = pd.DataFrame(
            [
                {"scenario": "A", "trade_label": "winner", "ret_20d_pre": 0.01},
                {"scenario": "A", "trade_label": "winner", "ret_20d_pre": 0.02},
                {"scenario": "A", "trade_label": "loser", "ret_20d_pre": 0.10},
                {"scenario": "A", "trade_label": "loser", "ret_20d_pre": 0.12},
            ]
        )
        out = _winner_loser_comparison_table(df, ["ret_20d_pre"])
        self.assertIn("mann_whitney_p_value", out.columns)
        self.assertIn("effect_size", out.columns)
        self.assertIn("direction_label", out.columns)

    def test_signal_to_entry_delay_is_zero_when_dates_match(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _signal_to_entry_delay_bars

        ts = pd.Timestamp("2026-01-02", tz="UTC")
        self.assertEqual(_signal_to_entry_delay_bars(ts, ts, [ts]), 0)

    def test_anchored_window_matches_recent_six_month_exclusion(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _anchored_oos_window

        window = _anchored_oos_window(pd.Timestamp("2026-04-29", tz="UTC"))
        self.assertEqual(str(window.train_end.date()), "2025-10-31")
        self.assertEqual(str(window.test_start.date()), "2025-11-01")
        self.assertEqual(str(window.test_end.date()), "2026-04-29")

    def test_rolling_windows_exist_and_are_stable(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _rolling_oos_windows

        windows = _rolling_oos_windows(pd.Timestamp("2021-04-29", tz="UTC"), pd.Timestamp("2026-04-29", tz="UTC"))
        self.assertGreater(len(windows), 0)
        self.assertLessEqual(pd.Timestamp(windows[-1].test_end), pd.Timestamp("2026-04-30", tz="UTC"))

    def test_sharpe_reliability_nan_safe(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _sharpe_reliability

        result = _sharpe_reliability(1.0, [0.1, -0.1], [0.5], 1)
        self.assertEqual(result["confidence_label"], "insufficient")

    def test_outcome_groups_are_deterministic(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _apply_outcome_groups

        df = pd.DataFrame({"realized_R": [-3, -2, -1, 0, 1, 2, 3, 4, 5, 6]})
        out = _apply_outcome_groups(df)
        self.assertEqual(len(out), 10)
        self.assertIn("winner_top30", set(out["outcome_group"]))
        self.assertIn("neutral_mid40", set(out["outcome_group"]))
        self.assertIn("loser_bottom30", set(out["outcome_group"]))
        self.assertTrue(out["is_best_decile"].any())
        self.assertTrue(out["is_worst_decile"].any())

    def test_universe_state_lookup_populates_core_fields(self) -> None:
        from src.backtest.analysis_structural_breakout_322 import DEFAULT_BASE_DIR, _prepare_preloaded_frames
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_universe_state_lookup

        base_dir = Path(DEFAULT_BASE_DIR)
        frames, _ = _prepare_preloaded_frames(base_dir, ["AAPL", "AMD", "NVDA"])
        lookup = _build_universe_state_lookup(frames, ["AAPL", "AMD", "NVDA"])
        sample_key = sorted(lookup.keys())[-1]
        self.assertIn("breadth_above_sma20", lookup[sample_key])
        self.assertIn("dispersion_20d", lookup[sample_key])
        self.assertIn("mean_pairwise_corr", lookup[sample_key])

    def test_regime_state_labels_are_exhaustive(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_regime_state_lookup
        from src.backtest.data_loader import DEFAULT_BASE_DIR

        lookup = _build_regime_state_lookup(
            Path(DEFAULT_BASE_DIR),
            {"2026-04-29": {"breadth_above_sma200": 0.6, "breadth_above_sma20": 0.6, "breadth_above_sma50": 0.6, "breadth_positive_20d": 0.6, "top_sector_dominance_score": 0.3, "correlation_spike": False}},
        )
        sample_key = sorted(lookup.keys())[-1]
        self.assertIn(
            lookup[sample_key]["regime_state"],
            {"risk_off", "true_early_trend", "rebound_chop", "failed_recovery", "strong_trend", "extended", "exhaustion"},
        )

    def test_rule_candidates_are_combination_rules(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_rule_candidates

        df = pd.DataFrame(
            [
                {"scenario": "A", "entry_date": "2026-01-01", "realized_R": -1.0, "regime_state": "true_early_trend", "sector_bucket": "semis", "crowding_proxy": True, "rs_percentile_20d": 0.9, "vol_expansion_ratio": 1.4, "breakout_strength_pct": 0.0, "semis_concentration_ratio": 0.6},
                {"scenario": "A", "entry_date": "2026-01-02", "realized_R": 1.2, "regime_state": "strong_trend", "sector_bucket": "other", "crowding_proxy": False, "rs_percentile_20d": 0.3, "vol_expansion_ratio": 0.8, "breakout_strength_pct": 0.02, "semis_concentration_ratio": 0.2},
                {"scenario": "B", "entry_date": "2026-02-01", "realized_R": -0.5, "regime_state": "rebound_chop", "sector_bucket": "software/internet", "crowding_proxy": False, "rs_percentile_20d": 0.8, "vol_expansion_ratio": 1.5, "breakout_strength_pct": -0.01, "semis_concentration_ratio": 0.3},
                {"scenario": "B", "entry_date": "2026-02-02", "realized_R": 0.8, "regime_state": "extended", "sector_bucket": "other tech", "crowding_proxy": False, "rs_percentile_20d": 0.5, "vol_expansion_ratio": 1.0, "breakout_strength_pct": 0.03, "semis_concentration_ratio": 0.2},
            ]
        )
        validation_df = pd.DataFrame([{"condition": "weak_ft_high_retrace", "action": "exit_next_open_day3", "trigger_count": 2, "trade_count": 4, "expectancy_r": 0.1, "win_rate": 0.5, "total_r": 0.4, "drawdown_proxy": -0.6, "expectancy_delta": 0.2, "drawdown_delta": 0.1}])
        out = _build_rule_candidates(df, validation_df)
        self.assertIn("rule_logic", out.columns)
        self.assertTrue(any(" and " in logic for logic in out["rule_logic"].astype(str)))

    def test_post_entry_validation_actions_are_next_open_style(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _build_post_entry_validation

        df = pd.DataFrame(
            [
                {"scenario": "A", "realized_R": -1.0, "ft_3d_band": "weak", "retrace_3d_band": "high", "mae_3d_band": "high", "crowding_proxy": True, "regime_state": "true_early_trend", "follow_through_5d_pct": 0.01, "post_breakout_retrace_5d_pct": 0.2, "validation_day3_next_open_r": -0.3, "validation_day5_next_open_r": -0.4},
                {"scenario": "A", "realized_R": 1.0, "ft_3d_band": "strong", "retrace_3d_band": "low", "mae_3d_band": "low", "crowding_proxy": False, "regime_state": "strong_trend", "follow_through_5d_pct": 0.10, "post_breakout_retrace_5d_pct": 0.03, "validation_day3_next_open_r": 0.7, "validation_day5_next_open_r": 0.9},
            ]
        )
        out = _build_post_entry_validation(df)
        self.assertTrue(any(str(action).startswith("exit_next_open") or str(action).startswith("reduce_next_open") for action in out["action"]))

    def test_feature_reduction_keeps_top_five(self) -> None:
        from src.backtest.analysis_structural_breakout_best_combo_323plus import _feature_reduction

        df = pd.DataFrame({"scenario": ["A", "A", "B", "B"], "regime_state": ["risk_off", "strong_trend", "risk_off", "true_early_trend"], "sector_bucket": ["other", "semis", "other", "semis"], "crowding_proxy": [False, True, False, True], "realized_R": [1.0, -1.0, 0.5, -0.5]})
        comparison_df = pd.DataFrame(
            [
                {"analysis_scope": "winner_vs_loser", "scenario": "ALL", "feature": "follow_through_3d_pct", "effect_size": 0.4},
                {"analysis_scope": "winner_vs_loser", "scenario": "A", "feature": "follow_through_3d_pct", "effect_size": 0.3},
                {"analysis_scope": "winner_vs_loser", "scenario": "B", "feature": "follow_through_3d_pct", "effect_size": 0.2},
            ]
        )
        out = _feature_reduction(df, comparison_df)
        self.assertIn("keep_flag", out.columns)
        self.assertLessEqual(int(out["keep_flag"].sum()), 5)


if __name__ == "__main__":
    unittest.main()
