# Task T099 Prep - Breakout Hypothesis Framework (Draft)

## 0) Scope and Guardrails
- Scope: analysis/docs only.
- This document defines a test plan, not a strategy implementation.
- No changes to entry/exit rules, risk policy, portfolio caps, or execution engine in this task.

## 1) Baseline (Current System Snapshot)
Source: `docs/reports/task_098_5/task_098_5_signal_funnel.json`

- Stage funnel (selected universe path):
  - `s1` selected-universe bars: 8,288
  - `s2` breakout pass: 694 (`s2/s1 = 0.083736`)
  - `s3` breakout+MA: 503 (`s3/s2 = 0.724784`)
  - `s4` liquidity: 503 (`s4/s3 = 1.000000`)
  - `s5` gap pass: 485 (`s5/s4 = 0.964215`)
  - `s6` generated signals: 39 (`s6/s5 = 0.080412`)
  - `s7` executed: 37 (`s7/s6 = 0.948718`)
- Primary bottleneck (current attribution): `BREAKOUT`
- Over-filtering flag detected at `BREAKOUT`:
  - `removed_count = 7,594`
  - `removed_avg_fwd_ret_20 = 0.020941`

Interpretation baseline:
- Execution and overlay are not the main choke points.
- Opportunity loss is concentrated before signal materialization, especially at breakout gating.

## 2) Professional Breakout Thesis -> System Definitions

For T099, define five measurable components before any rule discussion:

1. **Structure**
   - A pre-breakout price organization state (compression/base) before trigger.
   - Unit: event-level score `structure_score in [0,1]`.
   - Candidate dimensions: range compression, breakout-level proximity consistency, local swing organization.

2. **Liquidity Build-up**
   - Pre-trigger improvement in tradability, not only absolute thresholds.
   - Unit: event-level `liquidity_buildup_score`.
   - Candidate dimensions: trend in `avg_volume_20`, trend in `avg_turnover_20`, relative volume acceleration.

3. **Participation**
   - Whether the breakout bar itself reflects broad market participation.
   - Unit: event-level `participation_score`.
   - Candidate dimensions: breakout-day volume shock versus rolling baseline, close location quality, follow-through day breadth at symbol level.

4. **Volatility Regime**
   - Whether breakout occurs after contraction and into acceptable expansion.
   - Unit: event-level `vol_regime_score`.
   - Candidate dimensions: pre-breakout volatility compression percentile and post-trigger volatility expansion profile.

5. **Trigger Quality**
   - The technical trigger event quality itself, independent of downstream risk blocks.
   - Unit: event-level `trigger_score`.
   - Candidate dimensions: close-based breach strength, gap-adjusted breach efficiency, immediate failure/reversal rate.

## 3) Gap vs Current Breakout Pipeline

Current pipeline (from T098/T098.5): Universe -> Breakout -> MA -> Liquidity threshold -> Gap -> Signal materialization -> Risk overlay.

Gaps to thesis components:

1. Structure:
   - Current: binary breakout check.
   - Gap: no graded pre-breakout structure quality variable in artifacts.

2. Liquidity build-up:
   - Current: static pass/fail on `avg_volume_20`, `avg_turnover_20`.
   - Gap: no trend/acceleration metric around trigger.

3. Participation:
   - Current: indirectly covered by breakout and liquidity thresholds.
   - Gap: no explicit breakout-day participation measure.

4. Volatility regime:
   - Current: no explicit regime score in T098/T098.5 breakout funnel.
   - Gap: contraction/expansion context missing at event level.

5. Trigger quality:
   - Current: binary stage transition.
   - Gap: no trigger-strength distribution analysis tied to forward outcomes.

## 4) Hypotheses (H1-H5) With Falsifiable Criteria

All hypotheses are analysis-only and evaluated on existing historical data windows.

### H1 - Structure Hypothesis
- Claim: higher pre-breakout structure quality leads to better 20-bar forward outcomes.
- Test set: Stage-2 pass events (and optionally Stage-5 pre-risk candidates).
- Falsifiable criteria:
  - Reject H1 if `E[fwd_ret_20 | top_structure_quantile] - E[fwd_ret_20 | bottom_structure_quantile] <= 0`.
  - Reject H1 if `positive_rate_20(top) - positive_rate_20(bottom) <= 0`.

### H2 - Liquidity Build-up Hypothesis
- Claim: dynamic liquidity build-up predicts breakout quality better than static liquidity pass.
- Test set: events with liquidity pass at Stage-4/5.
- Falsifiable criteria:
  - Reject H2 if rank correlation between `liquidity_buildup_score` and `fwd_ret_20` is `<= 0`.
  - Reject H2 if top-vs-bottom quantile spread in `fwd_ret_20` is `<= 0`.

### H3 - Participation Hypothesis
- Claim: breakout-day participation quality separates durable breakouts from weak ones.
- Test set: Stage-2 pass events.
- Falsifiable criteria:
  - Reject H3 if high-participation cohort does not exceed low-participation cohort on both:
    - `avg_fwd_ret_10`
    - `positive_rate_20`

### H4 - Volatility Regime Hypothesis
- Claim: contraction-before-breakout regime improves subsequent returns.
- Test set: Stage-2 and Stage-5 cohorts.
- Falsifiable criteria:
  - Reject H4 if contraction-qualified events do not improve `avg_fwd_ret_20` versus non-qualified events.
  - Reject H4 if contraction-qualified events do not reduce early failure proxy (`ret_5 < 0`) rate.

### H5 - Trigger Quality Hypothesis
- Claim: stronger trigger quality improves signal materialization and forward return.
- Test set: Stage-2 -> Stage-6 transition analysis plus forward returns.
- Falsifiable criteria:
  - Reject H5 if trigger score does not increase:
    - transition odds `P(s6 | s2)` by score bucket
    - `avg_fwd_ret_20` by score bucket

## 5) Required Measurements and Formulas

Forward return (already aligned with T098.5 logic):
- `fwd_ret_h(i) = (close[i+h] - close[i]) / close[i]`, `h in {5,10,20}`

Core rates:
- `stage_pass_rate(k) = count(stage_k) / count(stage_{k-1})`
- `materialization_rate = s6 / s5`
- `execution_rate = s7 / s6`

Removed-signal impact:
- `net_impact_h(filter) = removed_count(filter) * avg_fwd_ret_h(filter)` (T098.5 already reports this)

Hypothesis comparison stats (minimum):
- Quantile spread: `delta_q = mean(top_q) - mean(bottom_q)`
- Hit-rate spread: `delta_hit = pr(fwd_ret_20 > 0 | top_q) - pr(fwd_ret_20 > 0 | bottom_q)`
- Rank association: Spearman rho between score and `fwd_ret_20`

Reporting thresholds for practical significance (recommended):
- `delta_q >= 0.005` (50 bps at 20 bars)
- `delta_hit >= 0.03` (3 percentage points)
- keep both statistical sign and practical sign in report; do not rely on p-value only.

## 6) Data Requirements From Current Repo Artifacts

Primary artifacts:
1. `docs/reports/task_098_5/task_098_5_signal_funnel.json`
   - `stage_funnel`, `filter_attribution`, `removed_signal_quality`, `symbol_level`, `time_series_behavior.monthly_stage_counts`
2. `docs/reports/task_098/task_098_signal_density_diagnosis.json`
   - `selected_universe_funnel`, `signal_density`, `risk_overlay_reentry_impact`
3. `docs/reports/task_097/task_097_execution_density_capital_efficiency.json`
   - `opportunity_loss`, `trade_frequency`, `capital_utilization`
4. `docs/reports/task_097_5/task_097_5_capital_deployment.json`
   - `signal_execution`, `opportunity_capture`, scenario invariance checks
5. `docs/reports/task_096/task_096_revalidation.json`
   - `stability.blocked_by_reason`, `capital_efficiency`, consistency controls

Raw series needed for event-level scoring (analysis only):
- `data/raw/us_daily/*` via existing loader path used in T098.5 (`load_daily_bars`, `prepare_condition_frame`).

Optional control context:
- `docs/reports/task_093/task_093_capital_backtest.json` for selected universe and base trade list alignment.

## 7) Non-Goals (Explicit)
- No strategy/risk/execution code edits.
- No threshold tuning proposal in this task.
- No claim of production readiness.
- No replacement of existing breakout rule in T099-prep.
- No reclassification of T096/T097/T098 conclusions.

## 8) T099 Handoff Checklist

1. Freeze baseline snapshot:
   - Record T098.5 stage counts and removal impacts as baseline table.
2. Build event panel:
   - For each evaluable bar/event, create rows with stage membership and `fwd_ret_{5,10,20}`.
3. Add thesis scores (analysis columns only):
   - `structure_score`, `liquidity_buildup_score`, `participation_score`, `vol_regime_score`, `trigger_score`.
4. Run H1-H5 falsification tests:
   - quantile spreads, hit-rate spreads, rank correlations, stage-transition conditioning.
5. Produce metric-first output:
   - one table per hypothesis with pass/fail, effect size, and sample count.
6. Integrity checks:
   - reconcile `s5`, `s6`, `s7` with T098.5/T098/T097.5 totals.
7. Decision memo for follow-up task:
   - identify only hypotheses with consistent positive signal and adequate sample size.

## 9) Expected T099 Deliverables
- `task_099_hypothesis_test_results.json` (recommended schema)
- `task_099_hypothesis_test_results.md`
- explicit H1-H5 pass/fail matrix with sample counts and effect sizes
- appendix with formula dictionary and data lineage map.
