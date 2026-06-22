from __future__ import annotations

import pandas as pd


def fixture_panel() -> pd.DataFrame:
    rows = []
    for idx in range(40):
        good = idx % 4 != 0
        entry = pd.Timestamp("2025-01-01", tz="UTC") + pd.Timedelta(days=idx)
        rows.append(
            {
                "decision_id": f"D{idx}",
                "candidate_id": f"C{idx}",
                "lifecycle_id": f"L{idx}",
                "symbol": f"S{idx % 5}",
                "theme_id": "ai_semiconductors" if idx % 2 == 0 else "cloud_ai_platforms",
                "session_date_et": entry.strftime("%Y-%m-%d"),
                "entry_ts": entry,
                "exit_ts": entry + pd.Timedelta(days=5 if good else 0),
                "net_return_from_entry": 0.05 if good else -0.03,
                "win_flag": int(good),
                "add_scale_success_flag": int(good),
                "entry_reduce_failure_flag": int(not good),
                "false_positive_flag": int(not good),
                "quarter": "2025Q1",
                "split_name": "train_design" if idx < 20 else ("validation" if idx < 30 else "recent_oos"),
                "broad_market_score": 4 if good else 2,
                "broad_market_stress": 1 if good else 4,
                "payoff_theme_score": 4 if good else 2,
                "payoff_theme_stress_score": 1 if good else 4,
                "forward_live_theme_breadth_positive_rate": 0.8 if good else 0.3,
                "forward_live_theme_return": 0.02 if good else -0.01,
                "forward_live_theme_rank": 1 if good else 5,
                "vwap_acceptance_state": "above_vwap" if good else "below_vwap",
                "timing_state": "midday_continuation" if good else "late_day",
                "close_location": 0.85 if good else 0.35,
                "upper_wick_pct": 0.1 if good else 0.55,
                "range_pos": 0.8 if good else 0.95,
                "entry_extension_atr": 1.0 if good else 2.5,
                "volume_ratio_20": 2.2 if good else 0.7,
                "vwap_deviation": 0.01 if good else -0.01,
                "spread_state": "tight_spread" if good else "wide_spread",
                "quote_freshness_state": "fresh_quote" if good else "stale_quote",
                "nbbo_size_state": "thick_nbbo" if good else "thin_nbbo",
                "microstructure_feature_available_flag": 1,
            }
        )
    return pd.DataFrame(rows)
