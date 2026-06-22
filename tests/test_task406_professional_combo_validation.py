from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task406_professional_combo_validation import build_task406_professional_combo_validation


class TestTask406ProfessionalComboValidation(unittest.TestCase):
    def test_predeclared_combos_exact_labels_and_no_label_assignment(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entries = root / "entries.csv"
            labels = root / "labels.csv"
            pd.DataFrame(_entry_rows()).to_csv(entries, index=False)
            pd.DataFrame(_label_rows()).to_csv(labels, index=False)

            artifacts = build_task406_professional_combo_validation(
                entry_candidates_path=entries,
                labels_path=labels,
                out_dir=root / "out",
            )

            self.assertGreaterEqual(len(artifacts.professional_combo_rulebook), 20)
            self.assertEqual(int(artifacts.professional_combo_rulebook["predeclared_flag"].min()), 1)
            self.assertEqual(int(artifacts.professional_combo_assignment_panel["label_used_for_assignment_flag"].max()), 0)
            self.assertEqual(int(artifacts.professional_combo_assignment_panel["inferred_matching_used_flag"].max()), 0)
            self.assertEqual(int(artifacts.professional_combo_label_coverage_audit["fallback_used_count"].sum()), 0)
            self.assertEqual(int(artifacts.professional_combo_label_coverage_audit["unlabeled_treated_as_negative_count"].sum()), 0)
            self.assertIn("validation", set(artifacts.professional_combo_split_quality["anchored_split"]))
            self.assertEqual(int(artifacts.professional_combo_leakage_audit["leakage_pass_flag"].min()), 1)
            self.assertTrue((root / "out" / "task_406_professional_multicombination_test.md").exists())


def _entry_rows() -> list[dict]:
    rows = []
    profiles = [
        ("L1", "2026-01-01T14:30:00Z", 0.70, 0.01, 0.02, 1, 0.80, 0.01, 0.01, 0.70, 1.0, 1.2, 1.2),
        ("L2", "2026-01-02T16:00:00Z", 0.72, 0.01, 0.02, 1, 0.82, 0.02, 0.01, 0.80, 1.4, 1.2, 1.2),
        ("L3", "2026-01-03T19:30:00Z", 0.35, -0.01, -0.01, 8, 0.30, 0.00, -0.01, 0.99, 2.8, 0.6, 0.7),
        ("L4", "2026-01-04T14:30:00Z", 0.55, 0.01, 0.02, 2, 0.75, 0.01, 0.01, 0.55, 1.0, 1.2, 1.2),
        ("L5", "2026-01-05T14:30:00Z", 0.70, 0.01, 0.02, 1, 0.80, 0.01, 0.01, 0.70, 1.0, 1.2, 1.2),
    ]
    for lifecycle_id, ts, breadth, avg, theme_ret, rank, theme_breadth, entry_ret, mom, pos, exp, sym_liq, mkt_liq in profiles:
        raw = {
            "forward_live_breadth_positive_rate": breadth,
            "forward_live_avg_symbol_return": avg,
            "forward_live_liquidity_ratio": mkt_liq,
            "forward_live_theme_return": theme_ret,
            "forward_live_theme_rank": rank,
            "forward_live_theme_breadth_positive_rate": theme_breadth,
            "forward_live_theme_leadership_regime": "theme_leader" if rank <= 3 else "not_theme_leader",
            "entry_return_so_far": entry_ret,
            "entry_momentum_2bar": mom,
            "entry_range_pos": pos,
            "entry_range_exp_ratio": exp,
            "symbol_liquidity_ratio": sym_liq,
            "estimated_total_cost": 0.003,
            "cost_to_range": 0.10,
            "role": "leader",
            "entry_hour": int(ts[11:13]),
        }
        rows.append(
            {
                "decision_id": f"D|{lifecycle_id}",
                "candidate_id": f"C|{lifecycle_id}",
                "lifecycle_id": lifecycle_id,
                "decision_kind": "ENTRY",
                "symbol": "AAA",
                "theme_id": "test_theme",
                "decision_ts_utc": ts,
                "raw_factors_json": json.dumps(raw),
                "bucket": "ALLOW",
            }
        )
    return rows


def _label_rows() -> list[dict]:
    return [
        {"lifecycle_id": "L1", "lifecycle_outcome_class": "add_scale_success", "label_status": "labeled_exact_lifecycle", "join_key_used": "lifecycle_id_exact_only", "symbol_date_price_time_fallback_used_flag": 0, "unlabeled_treated_as_negative_flag": 0, "net_return_from_entry": 0.02},
        {"lifecycle_id": "L2", "lifecycle_outcome_class": "entry_reduce_failure", "label_status": "labeled_exact_lifecycle", "join_key_used": "lifecycle_id_exact_only", "symbol_date_price_time_fallback_used_flag": 0, "unlabeled_treated_as_negative_flag": 0, "net_return_from_entry": -0.01},
        {"lifecycle_id": "L3", "lifecycle_outcome_class": "entry_reduce_failure", "label_status": "labeled_exact_lifecycle", "join_key_used": "lifecycle_id_exact_only", "symbol_date_price_time_fallback_used_flag": 0, "unlabeled_treated_as_negative_flag": 0, "net_return_from_entry": -0.02},
        {"lifecycle_id": "L4", "lifecycle_outcome_class": "add_only_weak", "label_status": "labeled_exact_lifecycle", "join_key_used": "lifecycle_id_exact_only", "symbol_date_price_time_fallback_used_flag": 0, "unlabeled_treated_as_negative_flag": 0, "net_return_from_entry": 0.001},
    ]


if __name__ == "__main__":
    unittest.main()
