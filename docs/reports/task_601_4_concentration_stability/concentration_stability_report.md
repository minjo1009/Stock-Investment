# Decision Summary

- Verdict: PASS_MULTI_SESSION_TOP3_BELOW_0_80
- Strategy acceptance status: NOT_ACCEPTED
- Key metrics: before_top3_share=1.0, after_top3_share=0.75, recent_window_top3_share=0.75, entropy=1.386294, gini=0.0, symbol_count=4
- What changed: concentration stability is now measured across selected candidate sessions without changing entry, exit, replay, or strategy logic.
- Next action: PASS for T601-4 stability validation; strategy remains NOT_ACCEPTED.

# Before

- source_stage=FILLED
- candidate_count=24
- session_count=9
- top1_share=0.416667
- top3_share=1.0
- entropy=1.059385
- gini=0.138889
- symbol_count=3

# After

- candidate_count=12
- session_count=7
- top1_share=0.25
- top3_share=0.75
- entropy=1.386294
- gini=0.0
- symbol_count=4

# Stability Assessment

- recent selected window spans multiple sessions and top3_share is below 0.80
- recent_sessions=2026-05-19;2026-05-20;2026-05-21;2026-05-22;2026-05-26;2026-05-28;2026-05-29
- Per-session metrics are reported separately because sessions with fewer than four selected candidates make top3_share mechanically equal to 1.0.
- Matching policy: exact candidate_id and generated_time session grouping only; no lifecycle symbol/date/price/time fallback was used.

# Acceptance Impact

- PASS for T601-4 stability validation; strategy remains NOT_ACCEPTED.
- Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY and real capital remains FORBIDDEN.

# Quant Expert Report

- Data source and source readiness: T601-1 candidate_funnel_events and T601-3 selected_portfolio_candidates.
- Exact join keys: candidate_id for selection rows and generated_time-derived session labels for stability grouping.
- Leakage audit: labels/outcomes do not enter assignment logic.
- Split/OOS metrics: not applicable; this is operational concentration stability over runtime candidate sessions.
- Failure decomposition: insufficient session count or recent top3_share >= 0.80 fails this gate.
- Cost/slippage stress where PnL changed: not applicable.
- Remaining blockers: sector concentration remains source-blocked until sector evidence exists.

# No-Background Decision-Maker Report

- What happened: the selected portfolio is checked across the recent multi-session window instead of one aggregate headline only.
- Why it matters: a single-session concentration improvement is not enough for acceptance review.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: PASS for T601-4 stability validation; strategy remains NOT_ACCEPTED.

# Artifact Manifest

- concentration_before_after_metrics.csv
- concentration_session_metrics.csv
- concentration_recent_window_metrics.csv
- task_601_4_decision.csv
- artifact_manifest.csv
