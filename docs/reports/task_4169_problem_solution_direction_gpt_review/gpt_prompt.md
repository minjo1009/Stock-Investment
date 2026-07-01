# TASK-4169 GPT Review Prompt

You are a professional backend/data platform engineer and institutional trading-data infrastructure reviewer.

Important instruction:
- Do NOT read GitHub for this review.
- The local repository state is newer than GitHub.
- Use only the current local facts pasted below.
- Do not recommend broad rewrites, vector DB, graph DB, LLM thesis generation, trading signal, ranking, sizing, broker integration, paper/live promotion, deployment readiness, or real-capital workflow.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence.

User goal:
The user wants the solution direction for each currently identified L0-L4 problem. They want a practical GPT review, in easy Korean, focused on what should be fixed next and why.

Current local facts from TASK-4168:

1. L3 coverage gap triage
- L3 coverage gap rows: 4,627
- All rows are TRACE_OK, meaning L0/L1/L2 references are linked.
- Gap subreasons:
  - L1_BLOCKED_UNMAPPED_ROWS_PRESENT: 3,999
  - RECALL_AND_ENTITY_REVIEW_PENDING: 447
  - NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING: 181
- L4 L3_COVERAGE_GAP blockers: 4,630
- Difference of 3 is explained by coverage-gap graph-level blockers. This is not a count bug.

2. L4 blocker taxonomy
- UNSUPPORTED_RELATION_FAMILY: 18,610
- CONTRADICTION_NOT_SCANNED: 11,079
- L0_INCOMPLETE_COVERAGE: 11,079
- PROTO_EVENT_IDENTITY: 6,913
- L3_COVERAGE_GAP: 4,630

3. L0 status snapshot
- public newswire: RUNNING, progress 52.5482%, completed 2,155 / 4,101, pending 1,946, failed 0, partial 63
- BusinessWire: completed 2,013 / 3,834, pending 1,821, partial 52
- GlobeNewswire: completed 126 / 126, pending 0
- PRNewswire: completed 16 / 141, pending 125, partial 11
- public context news: federal_register_documents has one pending unit, 2020-10, page offset 32. Explicit blocker: FEDERAL_REGISTER_2020_10_PENDING_OFFSET_EMPTY_RESPONSE
- public market/macro news: FAILED_RETRYABLE

4. Validators
- L0-L2 wide handoff validator: PASS
- L3 relation graph validator: PASS
- L3 quality guard: PASS
- L4 thesis bundle validator: PASS
- TASK-4168 validator: PASS
- Closeout: PASS_WITH_WARNINGS only because many pre-existing dirty files are outside the TASK-4168 manifest. TASK-4168 scoped files passed.

Questions to answer:

For each problem below, review the solution direction:

A. 3,999 L1 blocked unmapped rows
B. 447 recall/entity review pending rows
C. 181 newswire mapped but no article/entity feature
D. 18,610 unsupported relation family blockers
E. 11,079 contradiction not scanned blockers
F. 11,079 L0 incomplete coverage blockers
G. 6,913 proto event identity blockers
H. BusinessWire/PRNewswire backfill still incomplete
I. public market/macro news FAILED_RETRYABLE
J. public context news Federal Register 2020-10 pending offset

Output in Korean, easy and direct.

Required output format:

1. 한줄 결론

2. 문제별 해결 방향 표
Columns:
- 문제
- 현재 의미
- 해결 방향
- 우선순위
- 지금 하면 안 되는 것
- 검증 방법

3. 실행 순서
Give a P0/P1/P2 ordered list.

4. Overengineering cut
List what Codex should explicitly avoid.

5. Codex next-task recommendation
Recommend the next 1-3 task IDs/titles and exact scope.

Keep the answer practical. Do not over-defend. If something should be deferred, say why.
