from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_intraday_canonical_oos_validation_391 import (
    build_intraday_canonical_oos_validation_391,
)


class TestIntradayCanonicalOosValidation391(unittest.TestCase):
    def test_oos_validation_keeps_canonical_only_flags(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task388 = root / "task388"
            task388.mkdir()
            themes = root / "themes.csv"
            _write_fixture(task388, themes)

            artifacts = build_intraday_canonical_oos_validation_391(
                task388_dir=task388,
                theme_universe_path=themes,
                out_dir=root / "out",
            )

            decision = artifacts.task_391_decision.iloc[0]
            self.assertEqual(str(decision["task_391_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["reconstruction_used_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertGreater(int(decision["recent_oos_count"]), 0)
            self.assertIn("add_scale_vs_entry_only", set(artifacts.robustness_summary["check_name"].astype(str)))
            self.assertTrue((root / "out" / "task_391_intraday_canonical_oos_validation.md").exists())


def _write_fixture(task388: Path, themes: Path) -> None:
    pd.DataFrame(
        [
            {"theme": "ai_semiconductors", "symbol": "NVDA", "role": "gpu_leader"},
            {"theme": "cloud_ai_platforms", "symbol": "MSFT", "role": "cloud_leader"},
        ]
    ).to_csv(themes, index=False)
    lifecycles = []
    events = []
    for idx in range(30):
        symbol = "NVDA" if idx % 2 == 0 else "MSFT"
        lifecycle_id = f"L{idx:03d}"
        day = idx + 1
        add_scale = idx % 3 != 0
        ret = 0.03 if add_scale else -0.01
        lifecycles.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": symbol,
                "entry_ts": f"2026-01-{day:02d}T14:30:00Z",
                "exit_ts": f"2026-01-{day:02d}T16:00:00Z",
                "bars_held": 6,
                "add_flag": int(add_scale),
                "scale_flag": int(add_scale),
                "reduce_flag": int(not add_scale),
                "exit_reason": "intraday_time_exit",
                "return_from_entry": ret,
            }
        )
        events.append({"lifecycle_id": lifecycle_id, "symbol": symbol, "event_type": "ENTRY", "event_timestamp": f"2026-01-{day:02d}T14:30:00Z", "price": 100, "size_multiplier": 0.5})
        if add_scale:
            events.append({"lifecycle_id": lifecycle_id, "symbol": symbol, "event_type": "ADD", "event_timestamp": f"2026-01-{day:02d}T14:45:00Z", "price": 102, "size_multiplier": 0.75})
            events.append({"lifecycle_id": lifecycle_id, "symbol": symbol, "event_type": "SCALE", "event_timestamp": f"2026-01-{day:02d}T15:00:00Z", "price": 103, "size_multiplier": 1.0})
        else:
            events.append({"lifecycle_id": lifecycle_id, "symbol": symbol, "event_type": "REDUCE", "event_timestamp": f"2026-01-{day:02d}T15:00:00Z", "price": 99, "size_multiplier": 0.5})
        events.append({"lifecycle_id": lifecycle_id, "symbol": symbol, "event_type": "EXIT", "event_timestamp": f"2026-01-{day:02d}T16:00:00Z", "price": 100 * (1 + ret), "size_multiplier": 0.0})
    pd.DataFrame(lifecycles).to_csv(task388 / "intraday_canonical_lifecycle_summary.csv", index=False)
    pd.DataFrame(events).to_csv(task388 / "intraday_canonical_event_log.csv", index=False)


if __name__ == "__main__":
    unittest.main()
