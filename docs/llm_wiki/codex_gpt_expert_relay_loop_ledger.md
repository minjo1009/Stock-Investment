# Codex GPT Expert Relay Loop Ledger

This ledger records captured GPT-Codex work cycles for the current frontend/governance sequence.

## Purpose

The user requested that the next work proceed through approximately ten GPT-Codex loops. A loop means a captured GPT-Codex interaction cycle, not a validator, checklist item, file count, or internal reasoning pass.

## Non-Authorization Rule

A ranked queue candidate is not implementation authorization. Only the selected loop may be implemented. Product screen implementation requires explicit selection in a future loop and its own GPT-Codex prompt/review cycle.

## User Clarification

- `SUPERSEDED_BY_USER_CLARIFICATION`: Task3811 is not active next-work direction.
- The phrase "10 loops" means approximately ten captured GPT-Codex work cycles.
- The phrase does not authorize ten validators or a pre-screen validator program.

## Safety Boundaries

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Broker mutation: `FORBIDDEN`
- Live order: `FORBIDDEN`
- Paper promotion: `FORBIDDEN`
- Missing/stale/unknown remains `UNKNOWN/BLOCKER`.
- GPT is planner/reviewer evidence, not source of truth.

## Ranked Next 10 Loop Candidates

1. Task3811 supersession + GPT-Codex 10-loop ledger correction.
2. Loop ledger schema + next-loop queue formalization.
3. Screenshot QA preflight plan, not product screen implementation.
4. Maestro smoke-flow preflight plan.
5. Read-model fixture authority boundary audit.
6. Domain component story coverage gap audit.
7. Candidate Detail screen-readiness checklist.
8. HOME screen-readiness checklist.
9. NativeWind deferral revalidation.
10. iOS dev build validation plan.

These candidates are planning order only. They do not authorize product screen implementation, DB/runtime connection, broker access, paper/live promotion, deployment readiness, or real-capital use.

## Required Ledger Row Schema

Each loop ledger row must include these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `loop_id` | yes | Stable loop id, such as `LOOP-0001`. |
| `task_id` | yes | Linked task id, or `UNASSIGNED` before task registration. |
| `status` | yes | One of `candidate`, `selected`, `active`, `completed`, `blocked`, `superseded`, `cancelled`, or `deferred`. |
| `user_goal` | yes | User's original goal. |
| `selected_goal` | yes | The small loop goal selected for implementation. |
| `task_type` | yes | Governance, frontend, QA, research, backend, DB, or mixed. |
| `expert_roles` | yes | GPT expert roles used for the loop. |
| `gpt_mode` | yes | Normal, Agent, Deep Research, or Agent + Deep Research. |
| `selection_reason` | yes | Why this loop was selected before others. |
| `scope_boundary` | yes | Files/directories and behavior allowed to change. |
| `forbidden_scope` | yes | Files/directories and behavior forbidden for the loop. |
| `gpt_prompt_artifact` | nullable | Path to prompt artifact. |
| `gpt_response_artifact` | nullable | Path to response artifact. |
| `codex_patch_summary` | nullable | Codex implementation summary. |
| `changed_files` | nullable | Changed file list or report path. |
| `validation_summary` | nullable | Validation evidence summary. |
| `commit_hash` | nullable | Commit hash or `none`. |
| `review_result` | nullable | GPT review result. |
| `next_loop_recommendation` | nullable | Recommended next loop. |
| `safety_confirmation` | yes | Hard state preservation summary. |

## Loop Status Lifecycle

Primary lifecycle:

```text
candidate -> selected -> active -> completed
```

Alternate terminal states:

- `blocked`: cannot proceed because of missing context, failing validation, environment issue, or safety boundary.
- `superseded`: replaced by later clarification or a better direction.
- `cancelled`: stopped by user or governance.
- `deferred`: valid but intentionally delayed.

## Status Definitions

| Status | Meaning |
| --- | --- |
| `candidate` | Potential next work. Not authorized for implementation. |
| `selected` | Chosen by GPT/user as the next loop. Not yet implemented. |
| `active` | Codex is implementing this loop. |
| `completed` | Implemented, validated, reported, and committed or explicitly marked no-commit-needed. |
| `blocked` | Cannot proceed because of context, validation, environment, or safety blockers. |
| `superseded` | Replaced by clarification or better direction. |
| `cancelled` | User or governance stopped the loop. |
| `deferred` | Valid but intentionally delayed. |

## Next-Loop Queue Semantics

Each queue item must include:

| Field | Required |
| --- | --- |
| `rank` | yes |
| `queue_id` | yes |
| `candidate_goal` | yes |
| `task_type` | yes |
| `expert_roles` | yes |
| `recommended_gpt_mode` | yes |
| `reason` | yes |
| `allowed_scope` | yes |
| `forbidden_scope` | yes |
| `promotion_condition` | yes |
| `status` | yes |
| `linked_loop_id` | nullable |

## Current Next-Loop Queue

| Rank | Queue ID | Status | Candidate Goal | Mode | Promotion Condition |
| ---: | --- | --- | --- | --- | --- |
| 1 | Q-0001 | completed | Task3811 supersession + GPT-Codex loop ledger correction | Agent | Completed as `LOOP-0001` / Task3814. |
| 2 | Q-0002 | completed | Loop ledger schema + next-loop queue formalization | Agent | Completed as `LOOP-0002` / Task3815. |
| 3 | Q-0003 | selected | Screenshot QA preflight plan | Agent | Recommended next as `LOOP-0003`, unless user/GPT selects a different candidate. |
| 4 | Q-0004 | candidate | Maestro smoke-flow preflight plan | Agent | Select only after screenshot QA preflight or explicit user override. |
| 5 | Q-0005 | candidate | Read-model fixture authority boundary audit | Agent | Select before real screen implementation. |
| 6 | Q-0006 | candidate | Domain component story coverage gap audit | Agent | Select before Candidate/HOME screen implementation. |
| 7 | Q-0007 | candidate | Candidate Detail screen-readiness checklist | Agent | Select only after Q-0005/Q-0006 or explicit override. |
| 8 | Q-0008 | candidate | HOME screen-readiness checklist | Agent | Select only after Q-0005/Q-0006 or explicit override. |
| 9 | Q-0009 | candidate | NativeWind deferral revalidation | Agent, or Agent + Deep Research if current external docs are needed | Select only if styling path becomes blocker. |
| 10 | Q-0010 | candidate | iOS dev build validation plan | Agent | Select when native QA evidence is available. |

## Ledger Rows

| loop_id | task_id | status | user_goal | selected_goal | task_type | expert_roles | gpt_mode | selection_reason | scope_boundary | forbidden_scope | gpt_prompt_artifact | gpt_response_artifact | codex_patch_summary | changed_files | validation_summary | commit_hash | review_result | next_loop_recommendation | safety_confirmation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LOOP-0001 | Task3814 | completed | Proceed through next work using GPT skill for about 10 loops | Task3811 supersession + GPT-Codex loop ledger correction | Governance / frontend governance | Principal Frontend Platform Architect; Expo/React Native Architect; Trading Governance Reviewer; Repository Governance Auditor | Agent | User clarified Task3811 was based on a wrong interpretation | Docs, package script cleanup, Task3811 supersession notes | No product screens, DB/runtime/KIS/Alpaca/broker connection, paper/live promotion, or real-capital change | `docs/reports/task_3814_codex_gpt_loop1_supersede_task3811/loop1_gpt_prompt.md` | `docs/reports/task_3814_codex_gpt_loop1_supersede_task3811/loop1_gpt_response_summary.md` | Superseded Task3811 active direction and installed loop ledger | See Task3814 report | Frontend typecheck/lint/test/storybook smoke/safety/fixtures, registry, and diff check passed | `6eed77e` | `PASS_WITH_P1_CONDITION_PATCHED` | Loop 2: ledger schema + queue formalization | Hard state unchanged: NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN |
| LOOP-0002 | Task3815 | completed | Proceed through next work using GPT skill for about 10 loops | Formalize loop ledger schema and next-loop queue semantics | Governance | Repository Governance Auditor; Codex-GPT Relay Workflow Architect; Frontend Governance Reviewer | Agent | GPT review selected formalization before more implementation loops | `docs/llm_wiki/codex_gpt_expert_relay_loop_ledger.md` and Task3815 report/index docs only | No frontend runtime code, screens, components, QA validators, package scripts, DB/runtime/broker/KIS/Alpaca, paper/live promotion, or real-capital change | `docs/reports/task_3815_loop_ledger_schema_formalization/loop2_gpt_prompt.md` | `docs/reports/task_3815_loop_ledger_schema_formalization/loop2_gpt_response_summary.md` | Formalized ledger schema, lifecycle, queue fields, and non-authorization rule | See Task3815 report | Content check, registry validation, and diff check passed | See Task3815 git commit | Not requested for this docs-only loop | Loop 3: Screenshot QA preflight plan | Hard state unchanged: NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN |
