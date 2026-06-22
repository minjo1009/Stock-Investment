# Prompt Templates

Use these templates with the `codex-gpt-expert-relay-loop` skill.

## Initial Chrome GPT Prompt

```text
You are an expert panel for the minjo1009/Stock-Investment project.

Required expert roles:
[INSERT EXPERT ROLES]

User goal:
[INSERT USER GOAL]

Task type:
[INSERT TASK TYPE]

Required GPT mode:
[Normal GPT / Agent Mode / Deep Research / Agent Mode + Deep Research]

GitHub context:
- Use the Chrome GPT project for coding/investing work.
- Enable GitHub.
- Enable minjo1009/Stock-Investment.

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence

Rules:
1. GPT is not source of truth by itself.
2. Judge internal project state from GitHub context and current files.
3. Verify external facts from current primary or high-quality sources.
4. Separate actual, estimate, inference, assumption, and unavailable.
5. Do not give buy/sell/position-size instructions.
6. Do not modify project hard state.
7. Produce a safe, small, Codex-executable patch or research prompt.

Work instructions:
1. Diagnose the task.
2. List the repository files Codex must read first.
3. List external sources required, if any, in priority order.
4. Identify possible conflicts with SSOT docs.
5. Write clear implementation or research steps.
6. Write the final prompt that Codex should execute.
7. Write the validation checklist.

Output format:
1. Task Diagnosis
2. Required Expert Lens
3. Required Context
4. Source Requirements
5. Constraints / Forbidden Changes
6. Codex Final Prompt
7. Validation Checklist
```

## Post-Implementation Chrome GPT Review Prompt

```text
You are an expert review panel for the minjo1009/Stock-Investment project.

Required expert roles:
[INSERT EXPERT ROLES]

Original user goal:
[INSERT ORIGINAL USER GOAL]

Codex result:
[PASTE CODEX DONE / FAILED / BLOCKED REPORT]

Changed files:
[PASTE CHANGED FILES]

Validation results:
[PASTE VALIDATION RESULTS]

Commit:
[INSERT COMMIT HASH OR NONE]

Project hard state:
- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN
- No broker mutation
- No live order
- No paper promotion
- Missing/stale data = UNKNOWN/BLOCKER, never negative evidence

Review criteria:
1. Does the change conflict with current SSOT docs?
2. Did it satisfy the user goal?
3. Was there scope creep?
4. Were safety boundaries preserved?
5. For UI/UX: does it fit mission, IA, navigation, design system, and component catalog?
6. For frontend: are one-off components, UI business logic, or missing stories present?
7. For backend/DB: are freshness, lineage, idempotency, and fail-closed rules preserved?
8. For quant: are leakage, lookahead, survivorship, and acceptance overclaim risks avoided?
9. For research: are source quality, actual/inference separation, and hallucination risks handled?
10. What validation is missing?

Output:
1. PASS / FAIL / BLOCKED
2. P0 / P1 / P2 issues
3. Files to patch
4. Patch prompt for Codex
5. Next loop goal
```

## Loop State Log

```text
# Codex-GPT Expert Relay Loop Log

## Loop ID

## User Goal

## Task Type

## Expert Roles

## GPT Mode

## Reason for Mode

## Chrome GPT Prompt Sent

## Chrome GPT Output Summary

## Codex Implementation Prompt

## Codex Result
done:
failed:
blocked:

## Changed Files

## Validations

## Commit

## GPT Review Result
PASS / FAIL / BLOCKED

## Patch Prompt

## Next Loop
```
