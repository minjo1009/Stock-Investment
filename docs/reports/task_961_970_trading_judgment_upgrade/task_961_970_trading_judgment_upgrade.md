# Task961-970 Trading Judgment Upgrade

## Decision Summary

- Verdict: reject the fresh duplicate suppression replay as a strategy improvement.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: Task941 slot10 baseline ended at 2939.23, 22.870268% CAGR, -29.484953% MDD. Task969 upgraded replay ended at 1891.71, 12.950355% CAGR, -58.200274% MDD.
- What changed: Task961-970 added freshness, duplicate thesis, independent evidence, catalyst expiry, contradiction severity, exposure, cohort stability, and one diagnostic replay policy.
- Next action: do not stack this filter onto the strategy. Use the new panels to isolate better entry timing and thesis quality rules without broad suppression.

## Quant Expert Report

### Data Source And Source Readiness

Inputs are existing diagnostic artifacts only:

- Task929 ready controlled trade specs.
- Task941 slot-capped selection feature panel and baseline selection ledger.
- Task917 L1 source evidence.
- Task919 candidate bundles and nine-primitive relation edges.
- Task880 canonical daily market data and QQQ calendar.

Source readiness remains diagnostic. The run does not create strategy acceptance or deployment readiness.

### Exact Join Keys

- `trade_spec_id` joins Task929 specs, Task941 features, Task961-970 decisions, replay trades, and replay summaries.
- `candidate_bundle_id` joins Task941 features to Task919 candidate bundles.
- `supporting_evidence_ids` joins Task919 bundles to Task917 L1 evidence.
- `supporting_relation_ids`, `contradicting_relation_ids`, `invalidation_relation_ids`, and `source_gap_relation_ids` join Task919 bundles to Task919 relation edges.
- Market prices are joined by exact `symbol` and session `timestamp`; no proximity fallback is used.

### Leakage Audit

Task962 computes `newest_available_to_brain_ts` and `leakage_state`.

Validation requires `leakage_state == pass` for the freshness panel. The policy explicitly excludes future outcome fields through `does_not_use`: `future_return`, `realized_return`, `pnl`, `post_entry_price_change`, and `outcome_rank`.

### Split/OOS Metrics

This task is a single diagnostic replay over the frozen 2021-01-01 through 2026-03-31 harness period. It inherits the existing controlled replay setup and does not promote a new accepted split result.

### Failure Decomposition

Baseline selected entries exposed the following diagnostic weaknesses:

- `source_gap_heavy`: 450 selected baseline entries.
- `duplicate_thesis`: 435 selected baseline entries.
- `thin_packet`: 433 selected baseline entries.
- `low_independent_evidence`: 433 selected baseline entries.
- `stale_source`: 242 selected baseline entries.

The policy selected only 337 entries and rejected 3352 entries. That suppression removed too much participation while failing to reduce drawdown. Result: lower return, worse MDD, and no QQQ beat.

### Cost/Slippage

Replay keeps the established diagnostic cost configuration:

- Initial capital: 1000.0.
- Entry slippage: 5 bps.
- Exit slippage: 5 bps.
- Round trip cost: 10 bps.
- Slot cap: 10 concurrent holdings.

### Remaining Blockers

- The system still lacks a profitable, source-backed trading decision rule that reaches 30% CAGR with tolerable MDD.
- Freshness and duplicate concepts are useful diagnostics, but the current hard-block policy is too blunt.
- The next work should turn these panels into ranked entry timing and thesis quality features, not broad exclusion filters.

## No-Background Decision-Maker Report

Task961-970 tried to make the brain more trader-like by asking whether an idea was fresh, duplicated, independently supported, catalyst-valid, contradicted, or crowded.

The test did not improve trading. It cut trades too aggressively and made results worse than the current Task941 slot10 baseline.

This does not change capital or deployment readiness. The project remains diagnostic only.

The useful output is not the new strategy. The useful output is the set of panels showing where the current brain is weak: too many thin, duplicated, stale, source-gap-heavy ideas are entering the replay.

## Artifact Manifest

### Inputs

- `data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv`
- `data/artifacts/task_941_950_slot_capped_selection_replay/task941_selection_feature_panel.csv`
- `data/artifacts/task_941_950_slot_capped_selection_replay/task942_slot_capped_selection_ledger.csv`
- `data/artifacts/task_941_950_slot_capped_selection_replay/task946_slot_capped_summary.csv`
- `data/artifacts/task_917_920_multifamily_relation_adapter/task917_multifamily_l1_evidence.csv`
- `data/artifacts/task_917_920_multifamily_relation_adapter/task919_l4_candidate_bundles_contradiction.csv`
- `data/artifacts/task_917_920_multifamily_relation_adapter/task919_relation_edges_9primitive.csv`
- `data/artifacts/task_880_theme_universe_10x7_replay/canonical_daily/`
- `data/artifacts/task_880_theme_universe_10x7_replay/calendar/data_derived_qqq_sessions_v1.csv`

### Outputs

- `data/artifacts/task_961_970_trading_judgment_upgrade/task961_baseline_weakness_decomposition.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task962_thesis_freshness_panel.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task963_duplicate_thesis_clusters.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task964_independent_evidence_quality.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task965_catalyst_validity_expiry.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task966_contradiction_severity_panel.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task967_thesis_exposure_map.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task968_entry_cohort_stability_audit.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task969_fresh_duplicate_replay_decisions.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task969_fresh_duplicate_replay_trades.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task969_fresh_duplicate_replay_equity.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task969_fresh_duplicate_replay_summary.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task970_source_manifest.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/task970_governance_closeout.csv`
- `data/artifacts/task_961_970_trading_judgment_upgrade/artifact_manifest.csv`

### Row Counts

- Ready input trade specs: 3689.
- Upgraded selected entries: 337.
- Upgraded rejected entries: 3352.
- Upgraded closed trades: 334.
- Skipped orders: 3.

### Validation Commands

- `python scripts/trader_brain_961_970_trading_judgment_upgrade.py`
- `python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_961_970_trading_judgment_upgrade`
- `python scripts/trader_brain_961_970_trading_judgment_upgrade_validate.py`
- `python -m unittest tests.test_trader_brain_961_970_trading_judgment_upgrade`
- `python scripts/trader_brain_941_950_slot_capped_selection_replay_validate.py`

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
