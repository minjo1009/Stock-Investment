# GPT Strategy Review Notes

These are external review notes only. They are not source-of-truth and do not change strategy acceptance.

## P0 - research_candidate_not_deployment_candidate

- Review note: GPT review classified the strategy as a research candidate with possible signal, but the selected rulebook is materially over-optimized for the current sample.
- Repo evidence: avg_degradation_ratio=0.6870934389633534; overfit_risk_level=HIGH

## P0 - theme_dependency_must_be_tested

- Review note: Run leave-one-theme-out because only four themes are active and top_theme_share is high.
- Repo evidence: top_theme_share=0.3592233009708738; theme_count=4

## P0 - symbol_dependency_must_be_tested

- Review note: Run leave-top-symbols-out to prove this is not a small set of lucky names.
- Repo evidence: top_symbol_share=0.203883495145631; symbol_count=17

## P0 - parameter_neighborhood_stability_required

- Review note: A single best grid cell is not enough. Neighboring cells must mostly remain positive OOS.
- Repo evidence: selected_strategy=task505_theme_id_timing_state_avg12_win55_er45_pos10

## P1 - entry_reduce_failure_is_too_high

- Review note: Entry-reduce failure around the selected and walk-forward samples is high enough to require attribution before any refinement claim.
- Repo evidence: selected_entry_reduce=0.3592233009708738; walk_forward_entry_reduce=0.3932584269662921

## P1 - regime_failure_map_required

- Review note: Failing folds should be mapped as failure environments, not used to invent new hindsight rules.
- Repo evidence: worst_fold=2025Q1; worst_capital_pnl=-21.262638484903075
