# Brain Layer Map

## Purpose

This map keeps the research brain understandable before more strategy work is added.

The canonical flow is:

```text
Raw source evidence
-> Primitive fact extraction
-> Economic meaning
-> Relation edge
-> Candidate bundle
-> Slot decision
-> Backtest or deployment gate
```

No layer may skip directly from source text to buy/sell, ranking, sizing, or backtest eligibility.

## Current Layer Ownership

| Layer | Role | Current Tasks | Commit Policy |
| --- | --- | --- | --- |
| Source evidence | Preserve source identity, timestamps, raw trace, and filing/event family. | Task722, Task731, Task735 | Code and small contracts may be committed. Raw text and large panels stay out of Git. |
| Primitive fact extraction | Extract source-local facts without economic promotion. | Task730, Task740 | Extractor code and tests may be committed. Full extracted panels stay as artifacts. |
| Economic meaning | Convert primitives into interpretation objects, confidence, uncertainty, and confirmation needs. | Task736, Task741, Task742 | Code, tests, and summary reports may be committed. Large packets stay as artifacts. |
| Relation edge | Judge reinforcement, offset, prerequisite, blocker, and context attachment across layers. | Task727, Task728, Task729 | Contracts and engine code may be committed after leakage guard tests pass. |
| Candidate bundle | Attach source/economic/relation context to candidate lifecycle bundles. | Task737, Task738 | Bundle contracts may be committed. Full bundle panels stay as artifacts. |
| Resolver and QA | Define missing primitives, resolver states, review lanes, and engineering work orders. | Task733, Task734, Task739 | Workbench code and small summaries may be committed. Large traces stay as artifacts. |
| Slot decision | Compare same-timestamp candidates without outcome leakage. | Task723, Task724, Task725 | Decision contracts may be committed only when no outcome fields enter assignment. |

## Operating Brain Stack

The project now needs one continuous brain-to-runtime stack, not only a research map.

Use this stack when connecting backend, paper/shadow runtime, broker execution boundaries, and frontend cockpit surfaces:

```text
L0 raw sources and market data
-> L1 source evidence and point-in-time receipt
-> L2 primitive facts and source-local features
-> L3 economic meaning and relation edges
-> L4 candidate thesis bundle and invalidation state
-> L5 policy/action brain
-> L6 runtime, replay, paper/shadow, and broker-truth gates
-> L7 frontend cockpit and human review
-> governance feedback into reports, registry, validators, and source gaps
```

No layer may bypass the next gate:

- L0-L2 may not emit buy/sell, rank, size, reduce, re-risk, or exit.
- L3 may emit interpretation, uncertainty, and relation context, not trade instructions.
- L4 may emit candidate thesis, catalyst, blocker, and invalidation state, not orders.
- L5 is the first layer allowed to propose policy actions, but only under frozen policy and validation gates.
- L6 is the only layer that may interact with runtime, paper/shadow journals, broker-truth reconciliation, or order intent gates.
- L7 is read-only. It may display decisions, blockers, provenance, charts, and review context. It must not create selector, sizing, replay, paper order, live order, or broker mutation logic.

## Current Operating Chain

| Stack Area | Current Reference | Current Meaning | Boundary |
| --- | --- | --- | --- |
| L0-L3 source/meaning research | Task731/735/740/742 and later source programs | Evidence, primitive facts, and practical meaning remain source-aware and review-only. | Missing sources are gaps, not bearish evidence. |
| L4 thesis and challenger planning | Task2941-2980 | L4 thesis invalidation and baseline-vs-challenger compare plan are frozen for governed comparison. | No replay until blocker policy permits it. |
| L5 position/action brain | Task1518-1537, Task1668-1687 | Thesis state, hold/reduce/exit, replacement hurdle, and thesis-aware action logic exist as diagnostic policy research. | Not accepted; cannot directly drive live capital. |
| Source-attached L5 replay | Task1848-1867 | Rates/liquidity and SEC dilution were attached to policy replay with exact keys and cost stress. | Diagnostic only; earnings source and acceptance gates remain blocked. |
| Research-to-paper readiness | Task2401-2500 | Frozen diagnostic policy was structured for paper-mode review. | Acceptance conclusion remains `NO_GO`; strict raw/as-of complete rows remain 0. |
| Shadow runtime contract | Task2861-2900 | Shadow journal, runtime schema gates, quality flags, and atomic catalog publication exist. | Runtime quality is `PARTIAL`; no paper or live orders are created. |
| L0-L6 realtime operations | Task3401-3410 | Recommended runtime cadence is event-driven plus a 10-minute changed-candidate brain heartbeat, with 5-minute safety and 30-minute heavy-source refreshes. | Diagnostic-only; no full 5-minute trading loop, no paper eligibility, no broker mutation, and no real capital. |
| L0-L6 diagnostic orchestration | Task3411-3420 | Package guard now builds deterministic runtime state hashes, idempotency keys, duplicate-state skips, and cadence-specific allowed/forbidden operation sets. | No scheduler installed, no replay, no paper order, no live order, no broker mutation, no acceptance/deployment change. |
| Backend accelerator infra | Task3191-3195 | Polars and DuckDB are promoted to core backend acceleration for parity-checked artifact/query computation; Pandera remains validation-oriented. | They cannot rank trades, size positions, trigger replay, or create orders. |
| Frontend cockpit | Task3180 | Current iOS tactical console diagnostic UI displays scanner, chart, risk, analysis, market context, and blockers. | Read-only `REPORTING_HEALTH`; no execution or trading logic. |

## Backend Runtime Boundaries

Backend code should be organized by responsibility:

| Backend Area | Current Home | Allowed Role | Forbidden Role |
| --- | --- | --- | --- |
| Research builders and historical experiments | `src/backtest/`, `scripts/trader_brain_*` | Build diagnostic panels, reports, frozen policy candidates, and replay artifacts. | Become implicit production runtime without supersession and package review. |
| Stable package candidates | `src/app`, `src/strategy`, `src/risk`, `src/execution`, `src/state`, `src/market`, `src/reporting` | Provide small reusable interfaces and runtime services after owner review. | Claim strategy acceptance or deployment readiness by being importable. |
| Runtime loop and paper bridge | `src/app/run_trade_loop.py`, `src/app/run_trade_once.py`, Task588/600 family | Controlled paper/shadow operation, evidence capture, and safety gates. | Treat simulated SELL rows or proxy PnL as broker truth. |
| Broker/execution boundary | `src/execution`, `src/integration/kis_*`, broker-truth reports | Order/fill interfaces and reconciliation evidence. | Permit real capital without deployment and broker-truth gates. |
| Runtime state and catalogs | `src/state`, `scripts/build_*_catalog.py`, `frontend/*/catalog` | Publish versioned read models for UI and review. | Let UI read raw task artifacts directly or mutate trading decisions. |
| Backend acceleration | `src/infra/accelerators.py`, `src/infra/external_tools.py` | Speed up equivalent backend artifact/query computations with Polars or DuckDB after pandas parity checks. | Change trading semantics, source gaps, selector, sizing, replay, orders, acceptance, or deployment readiness. |

## Frontend Contract

Frontend is the cockpit, not the brain.

The read-only UI may display:

- selected policy and status
- candidate/trade rows
- thesis, catalyst, invalidation, and source freshness
- charts, markers, VWAP, volume, and risk readouts
- blockers and provenance
- shadow journal and runtime quality flags

The UI must not:

- run selector, sizing, replay, or broker mutation logic
- hide source gaps behind empty charts
- show diagnostic or proxy metrics as broker truth
- turn review-only fields such as MDD attribution, trade review, or outcome labels into assignment inputs

## Repeated Development Loop

Every brain improvement should follow this loop:

1. Pick the stack layer being changed.
2. Name the current report, code path, artifact path, and validator.
3. Freeze input contracts before changing policy logic.
4. Build task-scoped outputs under `docs/reports/<task_id>/` and `data/artifacts/<task_id>/`.
5. Run the task validator plus governance checks.
6. Update registry and this map only when the layer boundary or active reference changes.
7. Keep frontend changes read-only unless a separate execution contract permits mutation.

## Next Refactor Direction

Do not start with more alpha search.

The professional backend path is:

1. Maintain `src/brain/contracts.py` as the first small stable contract surface.
2. Keep historical `src/backtest/analysis_*` and `scripts/trader_brain_*` files as artifact builders until promoted.
3. Extend typed input/output contracts between L3/L4/L5/L6 only when a wrapper needs them.
4. Add package-health tests for every promoted contract.
5. Feed frontend only from versioned runtime catalogs.
6. Keep broker execution behind explicit paper/live gates.

Current contract implementation:

- `docs/contracts/brain_runtime_contract.md`
- `src/brain/contracts.py`
- `src/brain/meaning_adapter.py`
- `src/brain/relation_adapter.py`
- `src/brain/policy_adapter.py`
- `src/brain/runtime_decision_adapter.py`
- `src/brain/frontend_read_model_adapter.py`
- `src/brain/runtime_catalog.py`
- `tests/test_brain_meaning_adapter.py`
- `tests/test_brain_relation_adapter.py`
- `tests/test_brain_policy_adapter.py`
- `tests/test_brain_runtime_decision_adapter.py`
- `tests/test_brain_frontend_read_model_adapter.py`
- `tests/test_brain_runtime_contracts.py`
- `tests/test_brain_runtime_catalog_adapter.py`
- `scripts/trader_brain_3351_3360_task742_meaning_adapter_validate.py`
- `scripts/trader_brain_3361_3370_relation_thesis_bridge_validate.py`
- `scripts/trader_brain_3371_3380_policy_review_bridge_validate.py`
- `scripts/trader_brain_3381_3390_runtime_review_bridge_validate.py`
- `scripts/trader_brain_3391_3400_frontend_review_bridge_validate.py`
- `scripts/trader_brain_3164_runtime_catalog_adapter_validate.py`
- `scripts/trader_brain_3401_3410_l0_l6_realtime_ops_audit_validate.py`
- `scripts/trader_brain_3411_3420_l0_l6_diagnostic_orchestration_validate.py`

Current operating loop implementation:

- `docs/operating_system/brain_code_operating_loop.md`
- `scripts/trader_brain_3181_3190_brain_code_operating_loop_validate.py`
- `docs/reports/task_3181_3190_brain_code_operating_loop/task_3181_3190_brain_code_operating_loop.md`

Current backend accelerator implementation:

- `src/infra/accelerators.py`
- `tests/test_backend_accelerators.py`
- `scripts/trader_brain_3191_3195_backend_accelerator_promotion_validate.py`
- `docs/reports/task_3191_3195_backend_accelerator_promotion/task_3191_3195_backend_accelerator_promotion.md`

Current real-path accelerator migration:

- `scripts/trader_brain_3141_external_tool_helper_contract.py`
- `scripts/trader_brain_3196_3200_real_accelerator_migration_validate.py`
- `docs/reports/task_3196_3200_real_accelerator_migration/task_3196_3200_real_accelerator_migration.md`

## Active Brain Status

Task742 supersedes Task741 for practical economic interpretation.

Task741 remains useful as a denominator audit, but it should not be treated as the active economic meaning brain because it turns too many unavailable high-grade data sources into blockers.

Task742 is active only as a review-only economic meaning layer:

- It may emit direction hints.
- It may emit confidence bands.
- It may emit relation-readiness tiers.
- It may not emit buy/sell, score, rank, sizing, allocation, or backtest eligibility.

## Task756 Trader Brain 15-Step Program

Task756 defines the current research-only development path for rechecking and improving the Trader Brain.

| Step | Layer | Purpose |
| --- | --- | --- |
| Task757 | QA resolver | Dependency DAG and current/superseded audit for Task727-742. |
| Task758 | Source evidence | Good-enough L1 evidence contract and context retention. |
| Task759 | Primitive fact | Unified L2 primitive fact contract for Task730/740 outputs. |
| Task760 | Economic meaning | Task742 pragmatic economic meaning contract. |
| Task761 | Relation edge | Task742-to-Task729 adapter contract. |
| Task762 | Relation edge | Primitive fact gate repair design for the fixed gate path. |
| Task763 | Relation edge | Typed relation edge schema. |
| Task764 | Economic meaning | Good-enough source circuit interpreters. |
| Task765 | Relation edge | Regime, sector, and price modifier contracts. |
| Task766 | Relation edge | Compound interaction engine contract. |
| Task767 | Candidate bundle | Candidate thesis bundle contract. |
| Task768 | Slot decision | Same-timestamp slot competition framework. |
| Task769 | QA resolver | Resolver and conflict layer. |
| Task770 | QA resolver | Brain contract validation. |
| Task771 | QA resolver | Canonical brain registry and future backtest gate design. |

The program's core fix is:

```text
Task742 practical meaning
-> Task761 adapter
-> Task729 relation engine
-> Task767 candidate bundle
-> Task768 same-timestamp slot review
```

The program must not become a search for perfect information. It should use good-enough interpretation plus explicit uncertainty, then let later gates decide whether a packet can be reviewed further.

## Required Gates

Before any brain layer can feed a backtest:

1. `outcome_used_for_assignment_flag` must be zero.
2. Missing data must not become a negative label.
3. As-of source checks must pass.
4. Direction hints must remain separate from trade instructions.
5. Neutral or unknown context may not create directional edges.
6. Large generated panels must have a manifest instead of being committed directly.

## Repository Rule

Git should hold:

- Source code.
- Tests.
- Small contracts.
- Small summary reports.
- Artifact manifests.

Git should not hold:

- Raw market data.
- Full artifact panels.
- Large CSV/JSONL/PARQUET outputs.
- Runtime databases.
- Broker or account response archives.
