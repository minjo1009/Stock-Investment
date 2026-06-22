from __future__ import annotations

import unittest

from backtest.analysis_benchmark_gate_512 import build_benchmark_comparison


class TestAnalysisBenchmarkGate512(unittest.TestCase):
    def test_benchmark_gate_reject_when_underperform_tqqq(self) -> None:
        candidate = {"final_capital": 180000.0, "mdd_pct": 30.0}
        qld = {"final_capital": 150000.0}
        tqqq = {"final_capital": 220000.0}
        out = build_benchmark_comparison(candidate, qld, tqqq, mdd_limit_pct=60.0)
        self.assertFalse(out["win_both_benchmarks"])
        self.assertFalse(out["gate_pass"])
        self.assertEqual(out["elimination_reason"], "benchmark_underperformance")

    def test_benchmark_gate_reject_when_mdd_breach(self) -> None:
        candidate = {"final_capital": 300000.0, "mdd_pct": 61.0}
        qld = {"final_capital": 150000.0}
        tqqq = {"final_capital": 220000.0}
        out = build_benchmark_comparison(candidate, qld, tqqq, mdd_limit_pct=60.0)
        self.assertTrue(out["win_both_benchmarks"])
        self.assertFalse(out["mdd_pass"])
        self.assertFalse(out["gate_pass"])
        self.assertEqual(out["elimination_reason"], "mdd_limit_breach")

    def test_benchmark_gate_pass_when_beats_both_and_mdd_ok(self) -> None:
        candidate = {"final_capital": 300000.0, "mdd_pct": 40.0}
        qld = {"final_capital": 150000.0}
        tqqq = {"final_capital": 220000.0}
        out = build_benchmark_comparison(candidate, qld, tqqq, mdd_limit_pct=60.0)
        self.assertTrue(out["win_both_benchmarks"])
        self.assertTrue(out["mdd_pass"])
        self.assertTrue(out["gate_pass"])
        self.assertEqual(out["elimination_reason"], "")


if __name__ == "__main__":
    unittest.main()

