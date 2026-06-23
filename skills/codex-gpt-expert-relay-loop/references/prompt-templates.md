# Prompt Templates

Use these templates with the `codex-gpt-expert-relay-loop` skill.

## Relay Mode Rule

- "Use GPT" means one consult or review pass.
- "Run N loops", "repeat", or "GPT-Codex ping-pong" means autonomous loop mode.
- N loops means N captured GPT-Codex interaction cycles, not N validators, gates, files, commits, or internal reasoning passes.
- Project, code, docs, task planning, implementation, validation, and review work defaults to Agent Mode with GitHub repo context.
- Use Agent Mode + Deep Research when repo context and current external facts are both required.
- Use Normal GPT only when repo context is not needed.
- An explicit N-loop request is standing authorization to continue selected,
  bounded GPT-Codex loops until the requested count, user stop, automation
  blocker, validation/SSOT/safety blocker, or `PAUSED_RESOURCE_LIMIT`.
- A selected next-loop item should be promoted to active in the same run; do not
  stop only because unselected queue candidates are not authorization.
- After a Chrome GPT consult or loop run finishes, close the GPT Chrome tab used
  for the relay when the prompt/response artifacts and ledger/report are
  captured. Do not close unrelated user tabs.
- If Chrome automation is blocked, mark the loop `BLOCKED_AUTOMATION_NO_GPT_CAPTURE` and do not claim GPT reviewed the work.

## Loop Ledger

For autonomous loops, write or update a ledger with:

```text
loop_id,user_goal,task_candidate,expert_role,gpt_mode,prompt_artifact,gpt_response_artifact,codex_action,validation_result,review_prompt_artifact,review_response_artifact,status,stop_reason
```

When requested loops remain, the next selected row is a continuation target.
Return `continue_to_next_loop` unless there is a real stop condition.

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
[Agent Mode / Agent Mode + Deep Research / Deep Research / Normal GPT]

GitHub context:
- Use the Chrome GPT project for coding/investing work.
- Enable GitHub.
- Enable minjo1009/Stock-Investment.
- Inspect the repository before answering Codex for any project, code, docs,
  planning, validation, review, or implementation request.
- Base internal project-state claims on repo files, SSOT docs, current code,
  tests, and task reports visible through GitHub.

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

If the user asked for "next work" or "tasks to do next", first rank next task
candidates from current repo state. Do not jump directly to one narrow
validator, checklist, or implementation unless it is selected by the evidence.

Output format:
1. Task Diagnosis
2. Required Expert Lens
3. Required Context
4. Source Requirements
5. GitHub Files Inspected
6. Constraints / Forbidden Changes
7. Codex Final Prompt
8. Validation Checklist
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
6. Continue / Stop decision with stop reason if any
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

## Chrome GPT Tab Cleanup
closed / skipped_preexisting_user_tab / already_closed / failed / not_applicable

## Next Loop
```
