# TASK-4170 GPT Review Prompt

You are a professional backend/data platform engineer, SRE-style operations reviewer, and institutional trading-data infrastructure reviewer.

Important instruction:
- Do NOT read GitHub for this review.
- The local repository state is newer than GitHub.
- Use only the current local facts pasted below.
- The task is NOT to solve L0/L1/L4 blockers directly.
- The task is to review how Codex's operating harness should evolve so that future work is designed, executed, and reviewed as blocker burn-down instead of repeated status reporting.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence.

User concern:
For about a week, the same issue types keep repeating:
- L0 incomplete
- failed/retryable
- unmapped
- unsupported relation

The user is rightfully frustrated because Codex keeps spending tokens on diagnosis, reports, GPT reviews, and summaries, but the same blocker families keep appearing.

Current blocker facts:
- L3 coverage gap rows: 4,627
- All 4,627 rows are TRACE_OK
- L3 gap subreasons:
  - L1_BLOCKED_UNMAPPED_ROWS_PRESENT: 3,999
  - RECALL_AND_ENTITY_REVIEW_PENDING: 447
  - NEWSWIRE_ENTITY_OR_ARTICLE_FEATURE_MISSING: 181
- L4 blocker taxonomy:
  - UNSUPPORTED_RELATION_FAMILY: 18,610
  - CONTRADICTION_NOT_SCANNED: 11,079
  - L0_INCOMPLETE_COVERAGE: 11,079
  - PROTO_EVENT_IDENTITY: 6,913
  - L3_COVERAGE_GAP: 4,630
- L0 public newswire: RUNNING, 52.5482%, failed 0, partial 63
- BusinessWire: pending 1,821
- PRNewswire: pending 125, partial 11
- public market/macro news: FAILED_RETRYABLE
- public context news: Federal Register 2020-10 pending offset 32

Current problematic operating pattern:
1. Codex reports L0-L4 status.
2. GPT reviews direction.
3. Codex writes a task report and validators pass.
4. But blocker counts do not necessarily decrease.
5. The next user question asks why the same incomplete/failed/unmapped/unsupported problems remain.
6. Codex repeats status analysis and consumes more tokens.

Desired operating pattern:
Future Codex tasks should be designed as blocker burn-down tasks.

That means:
- Each task has a target blocker family.
- Each task has before_count and target_after_count.
- Completion is not just validator PASS.
- Completion must include blocker count delta, terminal status transitions, or explicit blocker reclassification.
- Reports must lead with "burn-down result", not broad L0-L4 state.
- GPT review must judge whether the task actually reduces or properly terminalizes blockers.
- If a task only explains blockers, it should be labeled diagnostic-only and should not be presented as progress.
- If backfill is still running, Codex should not keep re-litigating L2/L3/L4 blocker families that are upstream-blocked by L0.

Questions for GPT:

1. Root cause
Why structurally did the same issue classes keep repeating?

2. Harness design
What exact harness changes should Codex adopt so every future task is blocker burn-down oriented?

3. Required task template
Design a mandatory task template with fields like:
- blocker_family
- layer
- before_count
- target_after_count
- affected_artifacts
- allowed_actions
- forbidden_actions
- terminal_status_options
- validator_commands
- closeout_criteria
- stop_conditions
- report_format

4. Required report format
Design a concise Korean report format that always shows:
- What number changed
- What was terminalized
- What remained
- Why it remained
- Next concrete burn-down target

5. Required validators
What validators or audit scripts should exist to prevent "report-only progress"?

6. GPT review rubric
How should GPT review Codex work so GPT itself does not encourage repeated diagnosis?

7. Immediate next Codex implementation
Recommend the next bounded task to implement this harness in the repo.
Should it be a new validator, a task template, a burn-down ledger, registry rule, closeout rule, or all of these?

Output in Korean, easy and direct.

Avoid abstract management advice. Give a concrete implementable harness design.
