# Task897-906 Vertical Slice Backtest Front-Gate Correction

## Decision Summary

- Verdict: corrected to front-gate no-go.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Current conclusion: no valid brain-slice backtest result exists yet.
- Reason: the prior L1 rows were internal Task372 trade/lifecycle event captures, not attached raw external source evidence.
- L1 in-universe seed rows reviewed: 69.
- L2-admitted seed rows: 0.
- L2-rejected seed rows: 69.
- Raw source linkage rate: 0.0.
- Primitive fact rows: 0.
- Economic meaning rows: 0.
- Relation snapshot rows: 0.
- Candidate packet rows: 0.
- Dry trader decision rows: 0.
- Diagnostic trade specs: 0.
- Executed diagnostic replay rows: 0.
- Replay status: `not_run_front_gate_no_go`.
- Prior provisional replay result `1000 -> 1282.79` versus QQQ `1000 -> 1847.03` is invalidated and must not be used as strategy evidence.

## Quant Expert Report

The corrected chain is now:

```text
L1 seed/local lineage
-> source admission audit
-> raw external source gate
-> L2 only if admitted
-> L3/L4/L5 only if L2 exists
-> replay only if L2-L5 exists
```

The previous implementation allowed internal lifecycle events such as setup, invalidation, probe, and add events to become primitive facts. That was not acceptable for the Trader Brain objective, because those rows are downstream trade-state artifacts. They can document local lineage, but they cannot stand in for source evidence such as filings, transcripts, policy events, or timestamped news.

The new front gate rejects every current in-universe seed row because:

- `raw_external_document_state=missing`.
- `source_family=internal_source_event_capture`.
- `attachment_authority=LOCAL_LINEAGE_ATTACHMENT_ONLY_NOT_EXTERNAL_SOURCE`.

This means the correct current state is not "brain underperformed QQQ." The correct current state is "brain backtest not run because source admission failed."

## No-Background Decision-Maker Report

You were right. The front was wrong.

The system was pushing internal trade/lifecycle rows into the brain as if they were source evidence. That is now blocked.

So the next real work is not backend result analysis. The next real work is raw external source attachment and source-time admission. Until that passes, L2-L5 and backtest must stay empty.

## Artifact Manifest

- Script: `scripts/trader_brain_897_906_vertical_slice_backtest.py`.
- Validator: `scripts/trader_brain_897_906_vertical_slice_backtest_validate.py`.
- Test: `tests/test_trader_brain_897_906_vertical_slice_backtest.py`.
- Source admission audit: `data/artifacts/task_897_906_vertical_slice_backtest/task897_source_admission_audit.csv`.
- Front gate status: `data/artifacts/task_897_906_vertical_slice_backtest/task897_906_front_gate_status.csv`.
- Source-time contract: `data/artifacts/task_897_906_vertical_slice_backtest/task902_source_time_provider_contract.csv`.
- Raw source reality check: `data/artifacts/task_897_906_vertical_slice_backtest/task903_raw_source_reality_check.csv`.
- Empty L2-L5/replay panels: `data/artifacts/task_897_906_vertical_slice_backtest/`.
- Summary: `data/artifacts/task_897_906_vertical_slice_backtest/task897_906_vertical_slice_backtest_summary.json`.
- Validation command: `python scripts/trader_brain_897_906_vertical_slice_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
