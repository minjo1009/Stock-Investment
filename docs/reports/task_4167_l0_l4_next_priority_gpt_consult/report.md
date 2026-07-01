# TASK-4167 L0-L4 Next Priority GPT Consult

## Summary

GPT Pro review was requested for the next L0-L4 priority after TASK-4166.

The review agreed that the next work should not be a broad rewrite, graph DB, vector DB, LLM thesis writer, trading signal, ranking, sizing, order, broker, paper/live, deployment, or strategy acceptance task.

The recommended next task is:

`TASK-4168 L3 Coverage Gap Reason Narrowing & Newswire Recall Traceability`

## GPT Priority Verdict

| Priority | Task | Codex Judgment |
|---:|---|---|
| P0 | Keep L0 backfills running and preserve status snapshots | Accept, background operation only |
| P0 | Close or explicitly block `public_context_news_backfill` 149/150 | Accept, small L0 ops task if still open |
| P0 | Narrow L3 coverage gap reasons | Accept as next implementation task |
| P0 | Reconcile L3 coverage gaps 4,627 vs L4 `L3_COVERAGE_GAP` blockers 4,630 | Accept as part of TASK-4168 |
| P0 | Triage 447 newswire recall pending rows | Accept as part of TASK-4168 |
| P0 | Continue existing validators after each rebuild | Accept |
| P1 | Stable deterministic event identity for proto clusters | Later, after gap triage |
| P1 | Minimal `MACRO_SECTOR` / `SECTOR_THEME` relation support | Later, bounded only |
| P1 | L4 blocker taxonomy: global vs local blockers | Later, reporting improvement |
| P2 | Contradiction scanner | Defer; high overengineering risk before event identity |
| P2 | Collector speed/concurrency retuning | Defer while failed=0 and alerts=0 |

## Codex Cut

The next most useful work is not more collector code and not L4 thesis writing. The best next task is to make the existing blockers more actionable:

1. Explain every L3 coverage gap with narrower subreason.
2. Trace each gap back to L0/L1/L2 references when available.
3. Reconcile the small L3/L4 gap-count mismatch.
4. Specifically analyze:
   - `L2_BLOCKED_CANDIDATES_PRESENT`
   - `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE`
   - `NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING`
5. Keep all blockers as blockers unless evidence actually resolves them.

## Recommended Next Task

`TASK-4168 L3 Coverage Gap Reason Narrowing & Newswire Recall Traceability`

Bounded scope:

- Read current L1/L2/L3/L4 local artifacts only.
- Do not change L0 collector behavior.
- Do not create signals, scores, rankings, sizing, order intent, broker logic, paper/live promotion, deployment readiness, or strategy acceptance.
- Produce deterministic gap triage artifacts.
- Run L1/L2, L3, and L4 validators.
- Confirm trading authority and paper/live/broker/order rows remain `0`.

## Safety

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale/incomplete remains `UNKNOWN/BLOCKER`.
