# Task608G Live-Detectable Entry Failure Path Diagnostics

## Decision Summary

- Verdict: PASS_LIVE_DETECTABLE_FAILURE_CANDIDATES_FOUND_NEEDS_OOS_RULE_TEST
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Source coverage: 16/16 intraday symbols available.
- Clean entries: count 54, avg 26.03%, win 92.59%.
- Entry-reduce failed entries: count 35, avg -16.45%, win 0.00%.
- Diagnostic live signal candidates: 20.
- What changed: the loser label is now paired with pre/post-entry path evidence instead of only final PnL.
- Next action: Promote only diagnostic candidates into a no-label walk-forward reduce/exit simulation with cost stress.

## Quant Expert Report

- Data source and source readiness: Task509 OOS assignment panel plus `data/raw/us_intraday` OHLCV. QQQ is used only as a relative-strength reference.
- Exact join keys: lifecycle rows are not re-matched. Intraday bars are selected by exact symbol and timestamp windows around the existing `entry_ts`.
- Leakage audit: `entry_reduce_failure_flag` is used only as an evaluation cohort. It is not used to create entries or calculate signal candidates.
- Split/OOS metrics: the input rows are Task509 walk-forward OOS assignments.
- Failure decomposition: `entry_failure_path_panel.csv`, `clean_vs_failed_path_summary.csv`, `live_signal_candidate_summary.csv`, `state_signal_interaction_summary.csv`, and `quarter_live_signal_summary.csv`.
- Cost/slippage stress where PnL changed: not applied here; this is path detectability only. Any future reduce rule must rerun cost stress.
- Remaining blockers: diagnostic candidates are not accepted rules until no-label walk-forward reduce/exit simulation passes.

Top diagnostic candidates:
- volume_decay_120m_flag: failed 31.43%, clean 20.37%, separation 11.06%
- opening_rejection_120m_flag: failed 62.86%, clean 51.85%, separation 11.01%
- early_adverse_60m_flag: failed 20.00%, clean 12.96%, separation 7.04%
- early_adverse_120m_flag: failed 22.86%, clean 16.67%, separation 6.19%
- relative_strength_fail_60m_flag: failed 20.00%, clean 16.67%, separation 3.33%

Top state/path interaction candidates:
- symbol_multiday_setup_state=trend_persistence_near_high&early_adverse_60m_flag: trigger 5, failure 80.00%, lift 40.67%, capture 11.43%
- theme_id=aerospace_defense_space&relative_strength_fail_60m_flag: trigger 8, failure 75.00%, lift 35.67%, capture 17.14%
- symbol_multiday_setup_state=trend_persistence_near_high&relative_strength_fail_60m_flag: trigger 9, failure 66.67%, lift 27.34%, capture 17.14%
- theme_id=aerospace_defense_space&early_adverse_120m_flag: trigger 9, failure 66.67%, lift 27.34%, capture 17.14%
- symbol=BA&opening_rejection_120m_flag: trigger 9, failure 66.67%, lift 27.34%, capture 17.14%

Weak quarters:
- 2025Q1: avg -13.51%, entry-reduce 75.00%
- 2026Q1: avg 2.96%, entry-reduce 50.00%
- 2025Q3: avg 3.66%, entry-reduce 23.08%
- 2026Q2: avg 3.81%, entry-reduce 50.00%

## No-Background Decision-Maker Report

- What happened: we checked whether bad entries show warning signs soon after entry.
- Why it matters: if the warning sign exists early, we can test a real reduce/exit engine. If not, entry-reduce remains only a hindsight label.
- Whether this changes capital/deployment readiness: no. This is research evidence only.
- Plain-language next step: take only the best warning signs and test them as live reduce rules out-of-sample.

## Artifact Manifest

- See `artifact_manifest.csv`.
