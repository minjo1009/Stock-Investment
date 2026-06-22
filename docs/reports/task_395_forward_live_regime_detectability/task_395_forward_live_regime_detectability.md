# Task 395 - Forward-Live Regime Detectability Validation

## Required Answers
- Did Task 395 use full-day regime labels for forward-live detection? `NO`
- Did Task 395 use future outcome returns for regime detection? `NO`
- Did Task 395 use symbol/session inference? `NO`
- Did Task 395 make a deployment claim? `NO`

## Decision
task_395_verdict,evaluation_status,canonical_lifecycle_count,forward_live_regime_available_count,hindsight_strict_count,forward_live_strict_count,strict_overlap_count,forward_vs_hindsight_precision,forward_vs_hindsight_recall,forward_live_validation_avg_return,forward_live_recent_oos_avg_return,forward_live_gate_diagnostic_pass_flag,full_day_regime_used_flag,future_outcome_used_for_regime_flag,symbol_session_inference_used_flag,blocked_leakage_field_count,strategy_acceptance_status,next_priority
COMPLETE_PASS,FORWARD_LIVE_REGIME_DETECTABILITY_DIAGNOSTIC_COMPLETE,13095,13095,2453,2681,1519,0.566579634464752,0.6192417448022829,0.00265240161004989,0.0020087026911907915,1,0,0,0,0,FORWARD_LIVE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT,cost_capital_constrained_forward_live_policy_validation

## Detectability Alignment Audit
lifecycle_count,forward_live_regime_available_count,hindsight_strict_count,forward_live_strict_count,strict_overlap_count,forward_vs_hindsight_precision,forward_vs_hindsight_recall,forward_vs_hindsight_agreement,detectability_status
13095,13095,2453,2681,1519,0.566579634464752,0.6192417448022829,0.8399389079801451,FORWARD_LIVE_DIAGNOSTIC_AVAILABLE

## Forward-Live Gate Validation Audit
gate_name,validation_trade_count,validation_avg_return,validation_compounded_pnl,recent_oos_trade_count,recent_oos_avg_return,recent_oos_compounded_pnl,validation_avg_lift_vs_ungated,validation_collapse_reduced_flag,recent_oos_positive_flag,forward_live_gate_diagnostic_pass_flag
forward_live_strict_gate,521,0.00265240161004989,2.237987100633381,466,0.0020087026911907915,1.0923248917736101,0.0034730772555831924,1,1,1
hindsight_strict_gate,417,0.010025719356257805,53.19288470527277,401,0.012182975160014415,103.83655084828005,0.010846395001791107,1,1,0
ungated_baseline,2619,-0.0008206756455333025,-0.9523828911458587,2619,0.0005355432612605926,0.41277715262835457,0.0,0,1,0

## Leakage Audit
field,used_for_forward_live_regime,allowed
full_day_return,0,0
full_day_breadth,0,0
full_day_dollar_volume,0,0
post_entry_outcome_return,0,0
symbol_session_recovery,0,0
entry_timestamp_bars_so_far,1,1
prior_20d_same_bar_liquidity_median,1,1