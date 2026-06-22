# Task1238-1247 Raw Text Terminal Evidence Layer

## Decision Summary

- Verdict: `raw_text_terminal_evidence_layer_implemented_not_accepted`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: SEC filing metadata, raw filing cache, L1 terminal text evidence, L2 survival primitives, L3 invalidation edges, and expert audit upgrade rows were implemented.
- Key metrics: 310 selection rows, 1436 as-of filing metadata rows, 2477 L1 evidence rows, 241 selections with raw text evidence attached.
- Next action: review route audit and preregister a controlled policy before replay.

## Quant Expert Report

- Data source and source readiness: SEC bulk submissions metadata from `submissions.zip`; selected SEC Archives primary documents cached under `data/raw/task_1238_1247_sec_filing_text_cache`.
- Exact join keys: `symbol`, `cik`, `selection_id`, `decision_asof_ts`, `accession`, `primary_document`.
- Leakage audit: every L1 evidence row requires `available_to_brain_ts <= decision_asof_ts`; outcome, PnL, future return, and exit fields are not used for assignment.
- Split/OOS metrics: not applicable; no replay was executed.
- Failure decomposition: this task fixes raw SEC text binding for terminal-risk families, but official historical exchange deficiency feeds and non-SEC dynamic source extraction remain incomplete.
- Cost/slippage stress: not applicable because PnL did not change.
- Remaining blockers: PIT exchange listing event feed, richer section-level semantic parser, non-SEC source-time evidence.

## No-Background Decision-Maker Report

We moved from proxy-only volatility judgment toward actual filing-text evidence.

The brain can now see whether a selected stock had prior SEC text about going concern, dilution, listing deficiency, default, restructuring, or reverse split.

This does not make the strategy accepted. It makes the next replay less blind.

## Artifact Manifest

- Inputs: Task1201 slot5 selections, Task1171 public-filer pool, Task1228 route outputs, SEC bulk submissions zip.
- Outputs: expert packets, filing metadata, binding ledger, download ledger, L1 evidence, L2 primitives, L3 edges, independent distress audit, route transition audit, expert upgrade audit, closeout.
- Validation commands:
  - `python scripts/trader_brain_1238_1247_raw_text_terminal_evidence_validate.py`
  - `python -m unittest tests.test_trader_brain_1238_1247_raw_text_terminal_evidence`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
