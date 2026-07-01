# TASK-4149 L3 Local Context Packet

## Purpose

This packet is for a GPT Pro consult. GPT must review how to define and build Layer 3 from the current local project state.

The requested role is: Professional Backend Engineer.

GPT must not rely on GitHub as current state. The local working tree has important uncommitted work and dirty/deleted files. Use this packet as the source of project-state facts.

## Hard Boundaries

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation.
- No live order.
- No paper promotion.
- Missing or stale data is `UNKNOWN/BLOCKER`, never negative evidence.
- L3 may produce diagnostic economic meaning and relation review state only.
- L3 must not produce BUY/SELL, ranking, sizing, order intent, paper eligibility, live eligibility, broker mutation, strategy acceptance, or deployment readiness.

## Layer Map

Current intended stack:

```text
L0 raw sources and market data
-> L1 source evidence and point-in-time receipt
-> L2 primitive facts and source-local features
-> L3 economic meaning and relation edges
-> L4 candidate thesis bundle and invalidation state
-> L5 policy/action brain
-> L6 runtime, replay, paper/shadow, and broker-truth gates
-> L7 read-only frontend cockpit
```

L0-L2 may not emit buy/sell, rank, size, reduce, re-risk, exit, order intent, broker mutation, paper/live permission, or strategy acceptance.

## Current L0 State

Latest L0 worker recovery task: `TASK-4148`.

Facts:

- `public_newswire_backfill`: `RUNNING`.
- `public_market_macro_news_backfill`: `RUNNING`.
- Both critical lanes have live PIDs.
- PID ownership is verified against expected collector scripts.
- Incomplete dead lanes: `0`.
- Stale progress lanes: `0`.
- Windows Task Scheduler guard: `TraderBrainL0BackfillWorkerRecovery4148`, 15-minute recovery guard, last result `0`.
- L0 current status is written to `data/artifacts/l0_collection_status/current_status.json`.
- The guard updates `pid_alive`, `pid_owner_verified`, `worker_gate_state`, and authority flags.

Important caveat:

- Backfill coverage is still incomplete for public newswire and public market/macro news. L3 must treat missing/incomplete coverage as explicit coverage/blocker state, not as a negative signal.

## Current L1/L2 State

Latest L0-L2 wide handoff: `TASK-4146`.

Facts:

- L0 batch rows: `1944`.
- L0 raw item rows reported: `390391`.
- L1 packet rows: `1944`.
- L1 ready packet rows: `916`.
- L1 blocked packet rows: `1028`.
- L2 rows: `1944`.
- L2 admitted or review rows: `916`.
- Diagnostic feature candidate materialization rows: `916`.
- Feature candidate count: `375534`.
- Trading authority rows opened: `0`.
- Paper/live/broker/order rows opened: `0`.

Latest L0-L2 hardening: `TASK-4147`.

Facts:

- L1 article packets: `1093`.
- L1 article ready packets: `1093`.
- Raw article packet blockers: `0`.
- Newswire mapping queue rows: `198`.
- Newswire L0 mapped rows: `2909`.
- L2 diagnostic feature rows: `1842`.
- Backfill proof rows: `5`.
- Critical incomplete dead backfill lanes: `0`.
- Trading eligible rows: `0`.
- Signal/order export allowed rows: `0`.
- Broker mutation permitted rows: `0`.
- Realtime operational safe config exists at `configs/l0_realtime_operational_safe_config_4147.json`.
- 15-minute L1/L2 hardening scheduler exists as `TraderBrainL0L2Hardening4147`.

Current L2 contract:

- L2 is a safe primitive/admission/read layer, not a signal layer.
- News, macro, and newswire are swing feature candidates.
- Minute/second precision is not the main bottleneck for a roughly one-month swing holding period.
- Mapping, dedup, stale, effect-window, lineage, source-time, and leakage guards are first-class.
- L2 must not create sentiment score, alpha score, ranking, realized/forward return, sizing, signal, order intent, broker mutation, paper/live, or feature promotion.
- L3 read view must use whitelisted columns only.
- UNKNOWN mapping must go to review queue, not active L3 candidate.
- Duplicate non-canonical rows must not be independent L3 candidates.

## Existing L3 Design

Active L3 architecture document:

- `docs/architecture/l3_economic_meaning_engine_architecture.md`

Existing design says:

```text
L2PrimitiveFact
-> L3EconomicMeaningV2
-> L3EvidenceEdge
-> L3RelationGraph
```

L3 may emit:

- Direction review states: `SUPPORTIVE`, `RISK`, `MIXED`, `NEUTRAL`, `UNKNOWN`.
- Confidence components: raw band, static weight, calibration status, optional calibrated probability.
- Source reliability score.
- Event prior score.
- Freshness decay score.
- Evidence completeness score.
- Contradiction flags.
- Critical blocker flags and noncritical gap flags.
- Evidence-edge graph scores: support, risk, context, blocker, coverage, net direction.
- Review-only relation graph state.

L3 graph states:

- `SUPPORT_DOMINANT_REVIEW`
- `RISK_DOMINANT_REVIEW`
- `MIXED_REVIEW`
- `CONTEXT_ONLY`
- `BLOCKED_CRITICAL`
- `INSUFFICIENT_EVIDENCE`

These are review states only. They are not buy/sell/signal/order states.

Static confidence is not empirical probability:

```text
high -> 0.85
medium -> 0.60
low -> 0.35
insufficient/unknown -> 0.00
```

`calibrated_probability` must remain `None` unless calibration status is `CALIBRATED`.

## Existing L3 Code Status

Important dirty-worktree fact:

- `TASK-4139` found many dirty files, including L2/L3 code deletion rows.
- Current `git status` shows many tracked `src/brain/l3/*` and `src/l2/*` files as deleted in the working tree.
- Do not assume the current working tree has a stable L3 code surface.
- The old Git HEAD had L3 modules such as:
  - `src/brain/l3/contracts.py`
  - `src/brain/l3/canonical_diagnostic_engine.py`
  - `src/brain/l3/evidence_edge.py`
  - `src/brain/l3/graph_aggregator.py`
  - `src/brain/l3/source_gaps.py`
  - `src/brain/l3/source_reliability.py`
  - `src/brain/l3/adapters/l2_primitive_adapter.py`
  - `src/brain/l2_to_meaning_adapter.py`
- Those old modules should not be blindly restored without checking compatibility with the new L0-L2 packet/read-view work.

Old L3 contract shape from Git HEAD:

- `L3Confidence`
- `L3EconomicMeaningV2`
- `L3EvidenceEdge`
- `L3RelationGraph`
- `L3CalibrationStatus`
- `L3EvidenceEdgeState`
- `L3RelationGraphState`

Old adapter shape:

- `adapt_l2_primitive_to_l3_meaning(primitive, direction=UNKNOWN, confidence_band=unknown, economic_dimension=None, reason_codes=())`
- It expects canonical `L2PrimitiveFact`.

Current mismatch risk:

- Recent L2 work is artifact/read-view oriented and wide packet oriented.
- Old L3 adapter expects package-level canonical `src.l2.contracts.L2PrimitiveFact`, but many `src/l2/*` tracked files are currently deleted in the worktree.
- L3 must either restore a minimal canonical contract surface or build a task-scoped bridge from current L2 read artifacts into L3 diagnostic objects.

## What We Need GPT To Review

Please answer as a Professional Backend Engineer.

Design the first practical L3 development task from the current local state.

Questions:

1. What should Layer 3's goal be now, in plain operational terms?
2. What are the core L3 functions we should implement first?
3. Should we restore old `src/brain/l3` modules, create a new task-scoped L3 bootstrap, or do a hybrid?
4. How should L3 consume current L0-L2 outputs without bypassing L1/L2 gates?
5. How should L3 handle incomplete backfill, blocked L1 packets, UNKNOWN mapping, stale rows, and coverage gaps?
6. How should news, macro, and newswire become diagnostic trading-feature candidates without becoming signals/orders?
7. What are the minimum output artifacts for L3?
8. What validators should Codex implement?
9. What implementation sequence is safest and highest-impact?
10. What should Codex avoid as overengineering or unsafe scope creep?

## Expected Output

Return:

1. L3 goal definition.
2. L3 core feature/function list.
3. Recommended architecture and file/artifact plan.
4. Implementation steps for `TASK-4149`.
5. Validator checklist.
6. Explicit cut list: what not to build now.
7. Risk list with severity.
8. Final Codex patch prompt.
