# Task681 Integrated Prediction Stack Design

## Decision Summary

- Verdict: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: the five requested engines were converted into one linked prediction-stack design.
- Key decision: do not add any other stage until these five engines are implemented and linked by explicit data contracts.
- Next action: implement the five-engine stack with cohort slot qualification, not another global rank or cap.

## Quant Expert Report

### Data source and source readiness

- Reviewed source files:
  - `src/backtest/build_task672_current_data_state_axis_panel.py`
  - `src/backtest/build_task678_active_cap3_winner_archetype.py`
  - `src/backtest/build_task679_top5_qualification_engine.py`
  - `src/backtest/build_task673_677_setup_slot_exposure_action.py`
- Reviewed outputs:
  - Task678 winner archetype and max10 evidence.
  - Task679 top5 qualification failure and winner preservation guardrail.
- GPT/Chrome was used only as an external review partner.
- No new market data, labels, or assignment features were created.

### Exact join keys

- This is a design task, so no new join was performed.
- Required future joins must use `lifecycle_id` and `entry_ts`.
- Same-timestamp cohort logic must use `entry_ts`.

### Leakage audit

- No trading rule was promoted.
- No future returns, labels, or future prices are allowed in assignment.
- Task678 evaluation functions must not be directly reused as assignment functions.
- Historical outcomes may be used only for audit and validation, not for feature construction.

### Current Code Diagnosis

The current pipeline is effectively:

```text
state axes
-> diagnostic winner archetype labels
-> top5 tier
-> global priority rank
-> simulator
```

This is not firm-grade enough because:

- Task678 functions were diagnostic/reporting tools but were reused by Task679 assignment.
- Task679 collapses multiple dimensions into `top5_priority_rank`.
- `classify_top5_tier` assigns elite/contender/reject too early.
- Slot qualification is row-level/global-rank based, not cohort based.
- Leadership, catalyst, archetype, same-symbol context, and slot qualification do not have separate contracts.

### Required Integrated Stack

The required stack is:

```text
Raw entry-time row
-> Leadership Lifecycle Panel
-> Catalyst Quality Matrix
-> Winner Archetype Candidate
-> Same Symbol Context Signature
-> Cohort Slot Qualification
-> Simulation
-> Evaluation Audit
```

### Engine 1: Leadership Lifecycle Panel

Responsibility:

- Classify theme lifecycle at entry.

Inputs:

- `theme_ret20_prev`
- `theme_breadth20_prev`
- `theme_volume_ratio_prev`
- `theme_rank_prev`
- `theme_regime_state_v4`
- `market_ret_20d`
- `breadth_20d`

Outputs:

- `leadership_lifecycle_state`
- `leadership_strength`
- `leadership_breadth_quality`
- `leadership_timing_risk`
- `leadership_reason_codes`

Required states:

- `emerging_leadership`
- `persistent_leadership`
- `late_leadership`
- `fading_leadership`
- `participating_theme`
- `narrow_leader`

Forbidden:

- No theme blacklist.
- No winner outcome.
- No MDD-window-only rule.

### Engine 2: Catalyst Quality Matrix

Responsibility:

- Convert company/event content into economic quality.

Inputs:

- `positive_contract_customer_count`
- `positive_backlog_order_count`
- `positive_guidance_up_count`
- `positive_margin_supply_combo_count`
- `content_supply_demand_count`
- `content_guidance_margin_count`
- `catalyst_quality_score`
- `catalyst_quality_tier`

Outputs:

- `catalyst_path_type`
- `catalyst_economic_quality`
- `catalyst_durability`
- `catalyst_directness`
- `catalyst_surprise_proxy`
- `catalyst_reason_codes`

Example states:

- `contract_customer_backlog`
- `guidance_margin_upgrade`
- `supply_demand_shock`
- `contract_only`
- `multi_signal_but_unclear`
- `weak_or_single_dimension`
- `no_company_catalyst`

Forbidden:

- No average-return-driven catalyst relabeling.
- No "good news exists" shortcut.

### Engine 3: Winner Archetype Candidate

Responsibility:

- Classify entry-time upside-structure candidates.
- It does not predict or label actual winners.

Inputs:

- Leadership outputs.
- Catalyst outputs.
- `price_acceptance_state`
- `price_acceptance_score`
- `range_pos`
- `near_high60_prev`
- `trend_stack_prev`
- `volume_ratio_prev`
- `relation_transmission_state`
- `mechanism_support_count`
- `mechanism_pressure_count`

Outputs:

- `archetype_candidate`
- `archetype_confidence`
- `archetype_risk_flags`
- `archetype_reason_codes`

Required naming change:

- Replace `classify_winner_archetype` with `classify_archetype_candidate`.
- Replace outcome-sounding names:
  - `explosive_fragile_continuation` -> `early_acceleration_candidate`
  - `late_extended_breakout` -> `late_extension_candidate`
  - `theme_rotation_or_narrow_leader` -> `theme_rotation_candidate`
  - `catalyst_repricing_confirmed` -> `catalyst_repricing_candidate`
  - `steady_trend_persistence` -> `steady_trend_candidate`
  - `mixed_continuation` -> `mixed_or_unclear_candidate`

Forbidden:

- No big-winner label.
- No future return.
- No Task678 evaluation label reused directly.

### Engine 4: Same Symbol Divergence Matrix

Responsibility:

- Explain why the same symbol can be attractive in one setup and weak in another.
- It must describe state combinations, not blacklist symbols.

Inputs:

- `symbol`
- Leadership outputs.
- Catalyst outputs.
- Archetype outputs.
- Price state.
- Relation state.
- Macro state.
- Portfolio capacity state.

Outputs:

- `symbol_context_signature`
- `same_symbol_state_variant`
- `same_symbol_divergence_reason_codes`

Forbidden:

- No symbol blacklist.
- No symbol-level past PnL as assignment input.

### Engine 5: Cohort Slot Qualification

Responsibility:

- Decide which candidates deserve scarce max5 slots within the same `entry_ts` cohort.

Inputs:

- Engine 1-4 outputs.
- `entry_ts`
- `symbol`
- `theme_id`
- `portfolio_capacity_state`
- current open positions at `entry_ts`
- active theme/relation/driver concentrations.

Outputs:

- `cohort_slot_rank`
- `slot_qualification_bucket`
- `slot_admission_reason`
- `slot_displacement_risk`
- `slot_guardrail_flags`

Required change:

- Retire global rank logic like:

```text
top5_priority_rank = top5_qualification_rank * 1000 + original priority_rank
```

- Replace with cohort-level assignment:

```text
for each entry_ts:
  close expired positions
  build cohort candidates
  enrich candidates with engine outputs
  compare within cohort
  assign only available slots
```

Preferred ladder:

1. Source valid and not sparse.
2. Catalyst economic quality.
3. Archetype candidate clarity.
4. Leadership lifecycle fit.
5. Price acceptance mode.
6. Relation support versus pressure.
7. Portfolio concentration penalty.
8. Original active cap3 priority only as final tiebreaker.

Forbidden:

- No global row-level rank.
- No return-based slot score.
- No winner guardrail as assignment feature.
- No permanent symbol/theme block.

### Validation Design

Required leakage audit:

- `return_used_in_assignment_flag = 0`
- `label_used_in_assignment_flag = 0`
- `future_price_used = 0`
- `symbol_blacklist_used = 0`
- `theme_blacklist_used = 0`
- `microstructure_used = 0`

Required split/OOS audit:

- all / validation / recent_oos.
- Compare against Task639 and active cap3.
- Entry, exit, timing, and cost must remain unchanged.

Required slot audit:

- Added trades.
- Removed active cap3 trades.
- Removed active cap3 big winners, evaluation-only.
- Cohort decision reason.
- Displacement pairs.

### Acceptance Criteria For Implementation

Implementation quality passes only if:

- Five engines produce separate artifacts.
- Each engine has explicit input/output fields.
- `classify_winner_archetype` is not used for assignment.
- `classify_top5_tier` global tiering is retired.
- Slot qualification is cohort-based by `entry_ts`.
- Entry/exit/cost remain unchanged.
- Forbidden input audit is clean.
- Microstructure remains unused until source is ready.

Research performance passes only if:

- Task639 final capital improves.
- Task639 MDD is not worse.
- validation and recent_oos do not degrade.
- Active cap3 big-winner removal is lower than Task679 prototypes.
- Max10-style alpha dilution does not reappear.

Failure conditions:

- Global elite/contender/reject tier returns.
- State names alone drive rank.
- Row-level global rank replaces cohort comparison.
- Active cap3 winner removal increases.
- Task639 return or MDD gates fail.
- validation/recent_oos collapses.

## No-Background Decision-Maker Report

- What happened: the code structure was reviewed with GPT using the actual Task672/678/679 design.
- Why it matters: the current code compresses everything into one rank, so the five ideas do not really work together.
- Main decision: build five separate engines and link them by contracts before another strategy test.
- Capital readiness: unchanged. NOT_ACCEPTED and FORBIDDEN.
- Plain-language next step: stop making one big score. Build the five parts, then let candidates compete only against others at the same entry time.

## Artifact Manifest

- Inputs: current code structure, Task678 evidence, Task679 failure evidence, GPT review.
- Outputs: this report, decision CSV, GPT review, artifact manifest.
- Validation command: `python scripts\task_registry_validate.py`.
