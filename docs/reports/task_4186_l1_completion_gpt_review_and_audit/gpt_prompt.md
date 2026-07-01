# TASK-4186 L1 Completion GPT Pro Review Prompt

You are a professional backend/data-platform engineer and trading-data infrastructure reviewer.

Important context:
- Do not read GitHub for this review. The latest local work is not committed and GitHub is stale.
- Use only the local state summary below.
- This is diagnostic-only infrastructure. Do not propose trading signals, ranking, sizing, orders, paper/live promotion, broker mutation, deployment readiness, or strategy acceptance.
- Project hard state:
  - Strategy: NOT_ACCEPTED
  - Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  - Real Capital: FORBIDDEN
  - No broker mutation
  - No live order
  - No paper promotion
  - Missing/stale/incomplete data = UNKNOWN/BLOCKER, never negative evidence

User goal:
Starting from TASK-4182, define the remaining critical L1 problems, get GPT Pro review, and actually harden L1 article/entity/feature materialization, source recall review, and validator operating standards so the project does not move to L2/L3/L4 while leaving L1 errors unresolved.

Local implementation summary:

1. TASK-4182 L1 Article Entity Feature Hardening
- L1 article packets: 1,093 -> 6,036
- L1 READY article packets: 1,093 -> 6,036
- Article source families: 3
- Article source keys: 15
- Diagnostic feature rows: 1,842 -> 4,959
- Feature materialization gap rows: 181 -> 0, represented in deterministic wide materialization ledger
- Source recall review queue rows explicitly identified: 447
- Forced ticker mapping: 0
- LLM entity inference: 0
- Negative evidence conversion: 0
- Trading/action authority rows: 0
- Remaining warning: upstream L0 public_newswire_backfill worker blocker, not hidden
- Validator: PASS_WITH_WARNINGS only because of upstream L0 worker warning

2. TASK-4184 L1 Source Recall Parser Burn-down
- Source recall review rows before: 447
- Source recall review unresolved after: 0
- Decision status: all 447 = RECALL_RECOVERABLE_ARTICLE_READY
- Raw/wide/hash/JSON parsing evidence: all pass
- Article rows scanned: 163,869
- Mapped article rows found: 27,112
- Forced ticker mapping: 0
- LLM entity inference: 0
- Negative evidence conversion: 0
- Validator: PASS

3. TASK-4185 L1 Insufficient Context Terminalization
- Residual insufficient-context rows before: 5
- Non-terminal insufficient-context rows after: 0
- Terminal blockers recorded: 5
- Terminal status: TERMINAL_CONTEXT_OR_NON_CURRENT_UNIVERSE_ENTITY_BLOCKER
- Article rows scanned: 155
- Context/unmapped article rows: 155
- Forced ticker mapping: 0
- LLM entity inference: 0
- Negative evidence conversion: 0
- Validator: PASS

4. Governance and registry state
- TASK-4182, TASK-4184, TASK-4185 task registries updated
- doc registry updated
- artifact manifests exist
- required validators pass
- closeout validators pass with only scope warnings from pre-existing dirty files outside each task manifest
- doc registry validation: PASS
- task registry validation: PASS

Known remaining issue:
- L0 public_newswire_backfill worker blocker remains an upstream L0 operational warning.
- This is not being claimed as solved by L1 hardening.
- L1-specific unresolved source recall and insufficient-context blockers are now resolved or terminalized.

Please review:
1. Is this enough to say the L1 article/entity/feature materialization and source recall blocker work requested by the user is complete at the L1 level?
2. Are there any P0/P1 issues that would make the L1 closeout misleading?
3. Is it correct to keep the L0 public_newswire_backfill worker blocker as an upstream L0 warning rather than a L1 blocker?
4. Are there any overclaims, especially around feature materialization, trading features, or layer progression?
5. What should Codex report as the remaining risk, if any?

Output format:
- Verdict: PASS / CONDITIONAL PASS / FAIL
- P0 issues
- P1 issues
- Overclaim risks
- Required corrections before closeout
- Final closeout wording in simple Korean
