# Task907-916 SEC Source-Backed L1-L5 Pipeline

## Decision Summary

- Verdict: implemented as research-only L1-L5 positive path.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Purpose: recover from the Task897-906 front-gate failure by attaching real external SEC source files and rebuilding L1 through L5 without internal lifecycle contamination.
- Source family implemented now: `sec_companyfacts`, under the broader `company_filings_ir` family.
- Universe symbols: 70.
- SEC raw source files attached: 70.
- L1 source evidence rows: 618.
- L2 admitted rows: 618.
- Source span rows: 618.
- Primitive fact rows: 618.
- Economic meaning rows: 618.
- L3 relation snapshot rows: 4,041.
- L4 candidate bundle rows: 4,041.
- L5 dry decision rows: 4,041.
- Replay status: `not_run_l5_trade_spec_no_go`.

## Quant Expert Report

The repaired chain is:

```text
SEC raw companyfacts JSON
-> L1 source evidence
-> source admission audit
-> source span panel
-> L2 source-backed primitive facts
-> L2 economic meanings
-> L3 as-of relation snapshots
-> L4 candidate bundles
-> L5 dry decisions
-> replay gate no-go
```

Key controls:

- Internal lifecycle events are not allowed into the positive path.
- Every current L1 row has `raw_source_uri`, `raw_storage_path`, and `raw_source_hash`.
- Validator checks raw file existence and hash.
- `available_to_brain_ts` is conservatively set after filed date.
- L2 primitives require source span, extraction rule, reproducibility hash, and raw evidence.
- L3 relation snapshots are as-of bounded.
- L4 candidate bundles include `weakest_layer` and `unresolved_source_gaps`.
- L5 dry decisions keep `trade_spec_allowed=0` and `diagnostic_replay_allowed=0`.

This is not a final source corpus. The expert review constrained the first production-like pass to six source families:

```text
company_filings_ir
earnings_guidance
macro_policy_official
supply_chain_customer_capex_cross_read
positioning_liquidity_volatility
sector_specialist_official_docs
```

Task907-916 completes only the first family through SEC companyfacts. The remaining five families must be added before the project claims full L1 source coverage.

The relation vocabulary is bounded to the existing nine primitives:

```text
reinforces
weakens
invalidates
conditions
sequences
explains
contradicts
source_gap_for
noise_for
```

The current SEC relation implementation uses conservative source-backed context edges such as revenue-to-profitability and liquidity-to-obligation. These are research relation edges, not trade signals.

## No-Background Decision-Maker Report

The earlier mistake is fixed in the right direction.

Now L1-L5 is no longer empty. It runs from real SEC raw files, not internal trade events.

But it is still not a tradable strategy. It is a research-only brain path. We now have a working source-backed brain skeleton. Next, we add the other source families and only then consider adapter/backtest.

## Artifact Manifest

- Script: `scripts/trader_brain_907_916_sec_l1_l5_pipeline.py`.
- Validator: `scripts/trader_brain_907_916_sec_l1_l5_pipeline_validate.py`.
- Test: `tests/test_trader_brain_907_916_sec_l1_l5_pipeline.py`.
- Source corpus manifest: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task907_source_corpus_manifest.csv`.
- L1 evidence: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task908_l1_sec_companyfacts_evidence.csv`.
- Source admission audit: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task909_source_admission_audit.csv`.
- Source spans: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task910_source_span_panel.csv`.
- L2 primitive facts: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task911_l2_primitive_facts.csv`.
- L2 economic meanings: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task912_l2_economic_meanings.csv`.
- L3 relations: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task913_l3_relation_snapshots.csv`.
- L4 candidates: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task914_l4_candidate_bundles.csv`.
- L5 dry decisions: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task915_l5_dry_decisions.csv`.
- Replay gate: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task916_replay_gate.csv`.
- Summary: `data/artifacts/task_907_916_sec_l1_l5_pipeline/task907_916_summary.json`.
- Validation command: `python scripts/trader_brain_907_916_sec_l1_l5_pipeline_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
