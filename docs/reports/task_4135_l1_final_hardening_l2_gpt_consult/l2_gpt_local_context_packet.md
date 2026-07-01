# TASK-4135 GPT Local Context Packet

## Important Instruction For GPT

Do not read GitHub for this consult. The local worktree contains recent L0/L1 work that has not been committed or pushed. Treat this packet as the source of current project state for L0/L1. If you need more context, ask Codex to provide local file excerpts rather than using GitHub.

## User Goal

We rebuilt and hardened L0/L1 source acquisition locally. The user now wants to move toward L2, but first wants GPT's expert opinion using detailed local L0/L1 context.

## Hard State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data is UNKNOWN/BLOCKER, never negative evidence
- GPT is advisory only; repo files and validators remain source of truth

## Current L0 Summary

- L0 background collection lanes include daily bars, 5-minute bars, public context news, public newswire, and public market/macro news.
- Daily raw CSVs exist at `data/raw/us_daily_alpaca_full_universe/<SYMBOL>.csv`.
- 5-minute bars exist in `trading.db#market_bars_5m`.
- Public context/news/macro raw files exist under `data/raw/l0_public_*`.
- Backfills may still be incomplete, but missing rows are blockers, not negative labels.

## Current L1 Summary

- L1 is an evidence checkpoint, not a trading layer.
- Normalized packet required columns include task_id, source_packet_id, candidate_id, symbol, decision_asof_ts, provider, endpoint_or_source_family, source_ts, available_to_brain_ts, source_time_basis, source_time_certified, raw_path, raw_sha256, strict_gate_pass, proxy_feature_allowed, missing_source_is_negative, assignment_uses_future_outcome, outcome_used_for_assignment, authority.
- Gates are source_time, raw_integrity, mapping, authority.
- Classifications are STRICT_SOURCE_TIME_CERTIFIED, CONTEXT_ONLY_CERTIFIED, DISCOVERY_ONLY, and BLOCKED_* classes.
- TASK-4134 fixed a false daily-bars gap: daily bars now produce strict L1 packets from the real raw CSV path.
- Legacy direct L0-to-L2 news ingest is blocked by default.

## Handoff Contract

- public_context_news_feeds: CONTEXT_ONLY_CERTIFIED -> L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
- public_newswire_feeds: DISCOVERY_ONLY -> L2_REVIEW_QUEUE_ONLY_NOT_FEATURE
- public_market_macro_news_feeds: CONTEXT_ONLY_CERTIFIED -> L2_CONTEXT_INPUT_ALLOWED_NOT_TRADING_FEATURE
- market_bars_5m: STRICT_SOURCE_TIME_CERTIFIED -> L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY
- daily_bars: STRICT_SOURCE_TIME_CERTIFIED -> L2_PRIMITIVE_INPUT_ALLOWED_MARKET_OBSERVATION_ONLY

## Coverage Snapshot

- daily_bars: evidence=data/raw/us_daily_alpaca_full_universe, files/rows=11964, status=DATA_PRESENT_L1_GATE_READY
- market_bars_5m: evidence=trading.db#market_bars_5m, files/rows=31648964, status=DATA_PRESENT_L1_GATE_READY
- public_context_news_feeds: evidence=data/raw/l0_public_context_news_backfill, files/rows=941, status=CONTEXT_ONLY_L1_GATE_READY
- public_market_macro_news_feeds: evidence=data/raw/l0_public_market_macro_news_backfill, files/rows=320, status=CONTEXT_ONLY_L1_GATE_READY
- public_newswire_feeds: evidence=data/raw/l0_public_newswire_backfill, files/rows=189, status=DISCOVERY_ONLY_L1_GATE_READY

## TASK-4135 Local Summary

```json
{
  "coverage_rows": 5,
  "gap_count": 0,
  "generated_at": "2026-06-29T23:42:57Z",
  "gpt_github_forbidden": true,
  "handoff_contract_rows": 5,
  "l1_packet_count": 5,
  "l2_materialization_written": false,
  "strict_gate_pass_count": 2,
  "task_id": "TASK-4135",
  "trading_authority_opened": false
}
```

## Existing L2 Situation

- Visible `src/l2/builders/news_event_primitives.py` exists but imports modules that may be missing in visible source (`src.l2.contracts`, `freshness`, `lineage`, `runtime_context`, `news_runtime`).
- `src/l2/builders/microstructure_primitives.py` is effectively empty.
- Therefore L2 should begin with a small intake contract and validator, not broad production materialization.

## Question For GPT

Given this local L0/L1 state, recommend the safest, highest-leverage L2 development sequence. Please answer:

1. What should L2 be responsible for, and what must remain in L1?
2. What is the first minimal L2 artifact/schema/contract to implement?
3. Which source families should be consumed first: daily bars, 5-minute bars, macro/context, public newswire discovery, or something else?
4. What validators should block L2 if L1 gates are missing or stale?
5. How should we handle the existing broken/legacy L2 news builder/import surfaces?
6. What should explicitly not be built yet?
7. Provide a small Codex-executable TASK-4136 plan.
