# Task 343: Pro Quant Development Roadmap From Current State

## Current Snapshot

- Task 340 subset validation: `REJECT_SUBSET`
- Task 341 subset refinement: `REGIME_CONDITIONAL_EDGE`
- Task 342 portfolio integration: `NO_IMPROVEMENT`
- Current best regime condition: `entry_only + high_atr + vol_expanding + sector_group=software_internet`

## Interpretation

- Behavior state discovery succeeded, but pre-entry proxy prediction did not.
- True intraday information produced a regime-conditional edge, not a universal one.
- Portfolio-level direct sizing overlay improved some OOS metrics but did not pass robustness and cost gates.

## Phase Roadmap

| phase_id | phase_name | priority | objective | success_gate | stop_gate |
| --- | --- | --- | --- | --- | --- |
| A | intraday_evidence_expansion | 1 | Expand covered intraday sample, especially software_internet OOS trades, before making stronger deployment claims. | conditional edge persists with larger covered sample and longer rolling history | edge vanishes after coverage expansion or recent-only effect becomes obvious |
| B | conditional_priority_overlay | 2 | Translate the regime-conditional edge into ranking and slot-priority rather than direct size scaling. | priority overlay improves Sharpe and drawdown without trade-count collapse | priority overlay still fails to beat baseline after cost and concentration checks |
| C | portfolio_construction_integration | 3 | Validate whether the conditional edge helps under slot scarcity, sector caps, and crowding pressure. | portfolio-level improvement survives cross-section and crowding stress | benefit is driven by few trades, one sector, or one symbol cluster |
| D | shadow_monitoring_framework | 4 | Build a repeatable live-process monitor before any capital deployment. | shadow results align with historical direction and no hidden execution drift appears | shadow drift diverges materially from backtest behavior |
| E | live_go_no_go | 5 | Allow tiny live capital only after historical and shadow evidence both hold. | historical edge + shadow evidence + tiny-live evidence all align | slippage, concentration, or live decay breaks the edge |

## Research Priorities

| priority_rank | research_area | target_question | primary_artifact |
| --- | --- | --- | --- |
| 1 | sample_growth | Does the software_internet conditional edge persist when covered intraday sample expands beyond 390 trades? | sample_growth_sensitivity_report |
| 2 | priority_overlay | Does ranking condition_met trades higher work better than multiplying size? | conditional_priority_allocation_backtest |
| 3 | slot_competition | When multiple breakouts compete on the same day, should condition_met trades get execution priority? | same_day_candidate_competition_report |
| 4 | shadow_monitoring | Does live condition-met behavior stay aligned with historical expectation after costs and slippage? | shadow_overlay_monitoring_dashboard_spec |

## Overlay Translation Ranking

| priority_rank | overlay_type | recommended_use | acceptance_gate |
| --- | --- | --- | --- |
| 3 | direct_size_multiplier | backup_only | must beat ranking overlay after cost stress to remain relevant |
| 1 | trade_priority_ranking | primary_next_step | Sharpe up, MDD down, no trade-count collapse, concentration controlled |
| 2 | capital_slot_allocation | secondary_next_step | priority logic improves portfolio outcomes under slot scarcity and crowding pressure |

## Shadow Monitoring

| metric_name | frequency | purpose | warning_trigger |
| --- | --- | --- | --- |
| condition_met_trade_count | daily | Monitor how often the regime-conditional edge appears in live flow. | material drop versus recent rolling average |
| condition_met_vs_non_condition_realized_R | daily_and_weekly | Check whether the condition bucket still outperforms the neutral bucket. | condition bucket underperforms for multiple consecutive windows |
| drawdown_contribution_by_bucket | weekly | Identify whether drawdowns are being reduced or merely shifted. | condition bucket contributes disproportionately to downside |
| symbol_sector_concentration | daily | Prevent edge monetization from collapsing into a few names or one cluster. | single symbol or sector dominates live PnL contribution |
| slippage_drift | daily | Detect whether execution friction invalidates historical edge assumptions. | realized slippage materially exceeds backtest stress assumptions |

## Kill Criteria

| criterion_id | criterion | definition | action |
| --- | --- | --- | --- |
| K1 | expanded_sample_no_repeat | Expanded covered sample still fails to repeat rolling OOS improvement. | pause further deployment work and downgrade edge to research-only |
| K2 | software_internet_dependence_worsens | Sector dependence becomes stronger rather than more diversified as evidence grows. | treat edge as niche diagnostic, not scalable overlay |
| K3 | priority_overlay_no_gain | Ranking or slot-allocation overlay still does not improve Sharpe and drawdown versus baseline. | stop portfolio translation experiments and keep signal as descriptive only |
| K4 | cost_or_slippage_erases_edge | Reasonable execution friction removes the edge in historical or shadow evaluation. | block live deployment |
| K5 | shadow_drift_mismatch | Shadow bucket behavior diverges materially from historical direction. | investigate data/process drift before any capital deployment |

## Go/No-Go Gates

| gate_id | gate_name | definition |
| --- | --- | --- |
| G1 | expanded_intraday_revalidation | Tasks 338-342 rerun on enlarged coverage still support the regime-conditional edge. |
| G2 | priority_overlay_beats_size_overlay | Trade-priority or slot-allocation overlay is more robust than direct size scaling. |
| G3 | portfolio_sharpe_and_mdd | Portfolio-level Sharpe improves and drawdown does not worsen materially. |
| G4 | concentration_control | No extreme symbol or sector concentration emerges from the overlay logic. |
| G5 | shadow_alignment | Shadow results remain directionally aligned with historical expectation. |

## Practical Next Move

- First expand intraday evidence and rerun Tasks 338-342.
- Then test ranking / trade-priority overlay before trying any further size-based overlay.
- Only after historical revalidation should shadow monitoring and tiny capital live overlay begin.