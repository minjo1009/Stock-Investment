# Task609 Realtime Intelligence Trading Layer

## Decision Summary

- Verdict: `BUILD_INTELLIGENCE_LAYER_BEFORE_REFINEMENT`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Key metrics: 5 source contracts, 21 event fields, 5 paper-trading gates
- What changed: news, key-person statements, filings, company releases, and institution reports are defined as evidence-gated inputs.
- Next action: build Task609A/Task609B capture and no-direct-trade controls, then run Task610 historical replay against Task608 failures.

## Quant Expert Report

### Data Source And Source Readiness

- Current state: contract only. No new live source is certified by this task.
- Source readiness: `CONTRACT_ONLY_SOURCE_NOT_CONNECTED` for every listed source type.
- LLM role: extraction/review helper only. LLM output is not a source of truth and cannot trade directly.

### Exact Join Keys

- Required join keys: `intelligence_event_id`, `source_id`, `published_at_utc`, `captured_at_utc`, `symbol`, `theme_id`, `evidence_hash`.
- Forbidden joins: symbol/date/price/time proximity fallback.
- Missing evidence: reported as missing, never converted into positive or negative signal.

### Leakage Audit

- Future returns, final trade outcome, and Task608 failure labels cannot enter intelligence event assignment.
- Events can affect a replay decision only after `captured_at_utc` and inside the declared tradable window.
- Institution reports must not be redistributed; only metadata, derived labels, and allowed summaries may be stored.

### Split/OOS Metrics

- Not applicable yet. This task defines the layer. Task610 must test historical replay before any strategy claim.

### Failure Decomposition

- Task608K's 35 failures are now linked to missing information hypotheses.
- Opening traps map to fresh-catalyst and fade checks.
- Late followthrough maps to stale-catalyst and exit/trailing review.
- Market/theme drag maps to macro, sector, and leader narrative checks.

### Cost/Slippage Stress

- Not applicable until Task611 paper gate simulations change entry, size, wait, or exit timing.

### Remaining Blockers

- Real-time source credentials and raw archive are not connected.
- Historical event windows are not replayed yet.
- Strategy remains `NOT_ACCEPTED`; real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

- Chart alone tells us what happened, but not why.
- This task adds the missing why-layer: news, public statements, filings, company releases, and institution reports.
- The system must not buy or sell just because an LLM says so.
- First use this layer to block bad entries, wait for confirmation, reduce candidate rank, and explain trade decisions.
- This does not make the strategy accepted yet.

## Artifact Manifest

### Inputs

- Existing Task608 failure taxonomy and project governance rules.
- No external live news feed is consumed in this task.

### Outputs

- `intelligence_source_contract.csv`
- `intelligence_event_schema.csv`
- `intelligence_trading_gate_policy.csv`
- `task608_failure_intelligence_linkage.csv`
- `task_609_implementation_plan.csv`
- `task_609_decision.csv`
- `artifact_manifest.csv`

### Row Counts

- source_contract_rows: 5
- event_schema_rows: 21
- trading_gate_rows: 5
- task608_failure_linkage_rows: 5
- implementation_plan_rows: 5

### Validation Commands

- `python -m unittest tests.test_task609_realtime_intelligence_trading_layer`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`

### Source Hashes

- See `artifact_manifest.csv` after generation.
