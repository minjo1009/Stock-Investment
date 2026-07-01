# TASK-4167 GPT Pro Prompt

You are a professional backend engineer, data platform architect, quant data infrastructure reviewer, and institutional swing trader.

Important: Do not read GitHub. The GitHub repository is stale relative to the local Codex workspace. Base your answer only on the current local state summarized below. If you need repository details that are not provided, mark them as unavailable and propose a bounded local validation step.

User goal:
Prioritize the next L0-L4 work after recent operational/linkage hardening. Avoid code for code's sake, defensive guardrails with no practical value, broad rewrites, graph DB/vector DB/LLM thesis writer, trading signal/order logic, broker mutation, paper/live promotion, deployment readiness, or strategy acceptance.

Hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence
- All L4 output is diagnostic draft only, not final investment thesis

Current local state after TASK-4166:

L0 operational status:
- L0 current reliability alerts: 0
- daily lane: COMPLETE, 12040 / 12040 request units, progress 100.0%
- daily raw CSV files: 11966
- daily empty provider response units: 74
- five_min lane: RUNNING, progress about 28.9%
- public_newswire_backfill: RUNNING, sharded launcher PID 16236, progress about 52.55%, completed 2155 / 4101, failed 0
- public_market_macro_news_backfill: RUNNING, progress about 64.93%, completed 1705 / 2626
- public_context_news_backfill: RUNNING, progress 99.3333%, completed 149 / 150

L1/L2 status:
- L1/L2 wide handoff validator PASS
- L0 batch rows about 10.4k+
- L1 packet rows match L0 rows
- L2 rows match L1 rows
- Feature materialization candidates are diagnostic only
- Trading authority opened rows: 0
- Paper/live/broker/order opened rows: 0
- L1/L2 now read sharded newswire event ledgers and recall overlays

L3 current state after rebuild:
- relation_edges: 17,276
- event_clusters: 6,913
- relation_graphs: 11,079
- coverage_gaps: 4,627
- validator PASS
- L3 now consumes previously unrepresented L2 wide candidates as SOURCE_EVENT_CLUSTER, MACRO_FACTOR, or explicit COVERAGE_GAP rows.
- Coverage gap reasons:
  - L2_BLOCKED_CANDIDATES_PRESENT: 3,999
  - NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE: 181
  - NEWSWIRE_RECALL_REVIEW_ENTITY_FEATURE_PENDING: 447
- Unsupported relation families still declared:
  - CONTRADICTION
  - MACRO_SECTOR
  - SECTOR_THEME

L4 current state after rebuild:
- bundle_count: 11,079
- evidence_link_count: 17,276
- blocker_count: 52,311
- bundle_status_counts:
  - DRAFT_BLOCKED: 3
  - DRAFT_MIXED: 11,076
- institutional_quality_status_counts:
  - BLOCKED: 3
  - MIXED: 11,076
- blocker_type_counts:
  - CONTRADICTION_NOT_SCANNED: 11,079
  - L3_COVERAGE_GAP: 4,630
  - L0_INCOMPLETE_COVERAGE: 11,079
  - UNSUPPORTED_RELATION_FAMILY: 18,610
  - PROTO_EVENT_IDENTITY: 6,913
- L4 validator PASS

Recent fixes already completed:
1. Newswire failed units reduced to 0.
2. Legacy public newswire runtime/status confusion replaced with sharded runtime path.
3. Daily bar 99.3854% false incomplete state fixed by separating request completion from raw CSV file coverage.
4. L3/L4 rebuilt against current L1/L2 wide artifacts; input hash mismatch eliminated.
5. L3 widened to include previously unrepresented L2 wide candidates as diagnostic proto relations/gaps.

Question:
What are the next priority tasks?

Please produce:
1. A ranked P0/P1/P2 table of next tasks.
2. For each task, explain why it matters operationally or for L0-L4 data linkage.
3. Clearly separate:
   - must do now
   - useful but later
   - do not do yet
4. Identify which tasks are code implementation, which are validator/reporting, and which are background collection operations.
5. Avoid overengineering. Prefer small, effective improvements.
6. Do not propose trading signal/order/ranking/sizing/strategy acceptance work.
7. End with a recommended next Codex task id/title and exact bounded scope.
