# Task768 Same-Timestamp Slot Competition Framework

## Decision Summary

- Verdict: `SAME_TIMESTAMP_SLOT_CONTRACT_DEFINED_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Brain layer: `slot_decision`
- Owner team: Backtest & Simulation Infra
- Reviewer team: Research Governance + Regime Research
- Key metrics: 1 slot contract defined; 16 input catalog fields; 0 allowed global ranks, scores, sizes, portfolio optimizer outputs, buy/sell outputs, future PnL fields, or backtest eligibility outputs.
- What changed: Replaced the Task768 placeholder report, added the same-timestamp slot input contract, added the slot input catalog, refreshed the decision row, and regenerated the artifact manifest.
- Next action: Task769 can define resolver/conflict states for bundles that fail same-timestamp comparability, source readiness, or uncertainty rules.

Task768 is a research-only future input contract. Same timestamp slot comparison is not a rank, score, sizing model, backtest gate, trade permission, portfolio optimizer, or global top5 selector.

## Quant Expert Report

### Objective

Task768 defines how a future slot-decision layer may compare candidate thesis bundles only inside a same-timestamp cohort. It consumes review-only bundle quality and as-of-safe metadata, then emits only research review state for future downstream inspection.

The intended flow is:

```text
L1 source evidence
-> L2 PrimitiveFact
-> L3 MeaningObject and RelationEdge
-> L4 CandidateBundle
-> Task768 same-timestamp slot input contract
-> future resolver or gate review
```

The contract deliberately stops before selection, trading, sizing, optimization, or backtest eligibility.

### Data Source And Source Readiness

Task768 creates no new data source and performs no joins. It defines fields that future implementations may accept only when upstream artifacts already provide explicit identifiers and timestamps.

Required upstream readiness:

- candidate bundle exists as an L4 review object
- bundle trace points back to evidence, primitive facts, meanings, relation edges, modifiers, confirmations, contradictions, invalidations, and weakest layer
- `entry_ts` and `asof_ts` are present and as-of safe
- `cohort_id` is derived from explicit split/session context plus exact `entry_ts` and contract version
- uncertainty and source gaps remain explicit

### Exact Join Keys

Allowed identity and comparison keys:

- `candidate_bundle_id`
- `cohort_id`
- exact `entry_ts`
- exact `asof_ts`
- `split_name` or future supplied evaluation partition
- explicit upstream `lifecycle_id` only when already supplied by the bundle
- upstream trace ids: `evidence_id`, `primitive_fact_id`, `meaning_object_id`, `edge_id`, `modifier_id`

Forbidden matching:

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback matching.
- No same-symbol shortcut when bundle ids differ.
- No price reaction or future outcome matching.
- No missing label to negative conversion.

### Contract Summary

The canonical contract is `same_timestamp_slot_contract.md`.

Required concepts:

- `cohort_id`: exact same timestamp comparison group, not a strategy universe rank.
- `entry_ts`: timestamp that defines comparability.
- `asof_ts`: latest information timestamp allowed for the candidate before comparison.
- comparable candidates: bundles with the same `cohort_id`, same exact `entry_ts`, compatible `asof_ts`, and complete upstream ids.
- required bundle inputs: thesis, evidence trail, relation edges, modifier states, confirmation needs, contradiction states, invalidation links, weakest layer, and uncertainty flags.
- allowed comparison dimensions: source readiness, trace completeness, thesis clarity, relation coherence, contradiction load, confirmation burden, invalidation visibility, modifier support or cap, weakest layer severity, and uncertainty state.
- disqualifiers: missing cohort identity, timestamp mismatch, source gap, future/outcome field, forbidden output request, inferred matching, or bundle state that is context-only/not-ready.
- uncertainty handling: explicit `unclear`, `source_gap`, `timestamp_incomplete`, `stale_context`, `not_comparable`, or `review_needed`.
- forbidden outputs: buy/sell/hold, rank, score, slot score, global top5, actual sizing, allocation, portfolio optimizer, backtest eligibility, future PnL, win/loss, or trade permission.

### Allowed Comparison Dimensions

Task768 may compare only review quality within a same-timestamp cohort. Allowed dimensions are categorical or explanatory:

- source readiness: whether raw source trace and primitive facts are present
- bundle trace completeness: whether all required upstream ids are populated
- thesis clarity: whether the L4 bundle explains what is being reviewed
- relation coherence: whether relation edges reinforce, offset, block, cap, or require confirmation
- contradiction load: whether contradictions are explicit and reviewable
- confirmation burden: whether needed confirmations are small, medium, large, or blocking
- invalidation visibility: whether failure conditions are explicit
- modifier context: whether Task765-style modifiers support, cap, block, or require confirmation
- weakest layer: which layer blocks future review
- uncertainty state: whether ambiguity is low, capped, unclear, source gap, stale, or not comparable

These dimensions may produce review states such as `comparable_review_ready`, `comparable_but_capped`, `review_needed`, `not_comparable`, `source_gap`, or `timestamp_blocked`. They may not produce a numeric score, ordinal rank, trade action, size, or optimizer output.

### Leakage Audit

Task768 is document-only. It introduces no future price, return, PnL, realized outcome, win/loss label, target label, post-event feature, selection result, order, fill, size, allocation, or backtest permission field.

Same timestamp comparison is intentionally narrower than Task723's slot judgment examples. A future implementation may inspect relative review readiness inside the same cohort, but it cannot use global performance ranks, realized winners, future PnL, or a hidden score to choose trades.

### Split/OOS Metrics

Not applicable. Task768 is a research contract and artifact task. It does not run a strategy, split, OOS test, optimization, replay, simulation, or slot competition backtest.

### Failure Decomposition

The main failure modes are:

- `timestamp_blocked`: candidate does not share exact `entry_ts` or has invalid `asof_ts`
- `not_comparable`: candidate lacks the required bundle contract fields
- `source_gap`: upstream evidence or primitive source trace is missing
- `context_only`: bundle is explanatory context only
- `not_ready`: bundle lacks relation, confirmation, or invalidation readiness
- `forbidden_output_requested`: requested output is rank, score, size, optimizer, trade, backtest, or future PnL
- `inferred_matching_blocked`: comparability depends on lifecycle, symbol, date, price, or time fallback inference

### Cost/Slippage Stress Where PnL Changed

Not applicable. Task768 creates no trades, orders, fills, allocations, sizes, PnL, or backtest-eligible rows.

### Remaining Blockers

- Task767 is still a placeholder in this checkout, so Task768 defines required L4 bundle inputs without relying on completed Task767 detailed artifacts.
- Task766 is still a placeholder in this checkout, so compound interaction outputs remain future upstream inputs.
- Task769 still must define resolver and conflict handling for failed or uncertain slot inputs.
- No implementation exists for a same-timestamp comparison engine.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.

### Validation

Validation authority: diagnostic/research contract validation only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Changed files:

```text
docs/reports/task_768_same_timestamp_slot_competition/task_768_same_timestamp_slot_competition.md
docs/reports/task_768_same_timestamp_slot_competition/same_timestamp_slot_contract.md
docs/reports/task_768_same_timestamp_slot_competition/slot_input_catalog.csv
docs/reports/task_768_same_timestamp_slot_competition/task_768_decision.csv
docs/reports/task_768_same_timestamp_slot_competition/artifact_manifest.csv
```

Commands run:

```text
python -m unittest tests.test_task723_five_stage_decision_contract
python scripts/trader_brain_program_validate.py
```

Commands not run:

```text
None.
```

Inferred matching used:

```text
No.
```

## No-Background Decision-Maker Report

1. Done: Task768 now defines same timestamp slot comparison inputs.
2. Done: Candidates are comparable only inside the same exact `entry_ts` cohort.
3. Done: Bundle quality can be reviewed only as source readiness, trace completeness, relation coherence, uncertainty, and blocker state.
4. Done: The contract forbids global top5 rank, slot score, actual sizing, future PnL, buy/sell, portfolio optimizer, and backtest eligibility.
5. No change: Strategy remains `NOT_ACCEPTED`.
6. No change: Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
7. No change: Real capital remains `FORBIDDEN`.

## Artifact Manifest

| Artifact | Class | Purpose |
| --- | --- | --- |
| `task_768_same_timestamp_slot_competition.md` | report | Task768 decision and expert report. |
| `same_timestamp_slot_contract.md` | contract | Same timestamp cohort comparability and forbidden output contract. |
| `slot_input_catalog.csv` | catalog | Field catalog for allowed slot input dimensions and blocked shortcuts. |
| `task_768_decision.csv` | decision | Machine-readable Task768 decision record. |
| `artifact_manifest.csv` | manifest | File sizes and hashes for Task768 artifacts. |

Row counts:

- `slot_input_catalog.csv`: 16 data rows.
- `task_768_decision.csv`: 1 data row.
- `artifact_manifest.csv`: regenerated after artifact updates.

Validation commands:

```text
python -m unittest tests.test_task723_five_stage_decision_contract
python scripts/trader_brain_program_validate.py
```

Validation authority: diagnostic/research contract validation only. Passing tests do not change strategy acceptance, deployment readiness, or real-capital permission.

Inferred matching used: no.

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
