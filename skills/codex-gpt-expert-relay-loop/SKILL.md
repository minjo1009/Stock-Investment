---
name: codex-gpt-expert-relay-loop
description: Standing expert relay workflow for the Stock-Investment project. Use when a non-trivial goal should be classified before implementation, routed to the right Chrome GPT expert role and mode, and optionally reviewed by GPT. For project, code, docs, task planning, implementation, validation, or review work, GPT defaults to Agent Mode with GitHub enabled for minjo1009/Stock-Investment so GPT reads repo context before answering Codex. Add Deep Research only when current external facts are needed. "Use GPT skill" or "use GPT" does not start a loop. Start autonomous Codex-Chrome GPT loops only when the user explicitly requests N loops, repeated loops, autonomous iteration, or GPT-Codex back-and-forth. N-loop means N captured GPT-Codex interaction cycles, not N checklist items, validators, files, or internal reasoning passes. Fall back to a user-sendable prompt only when automation is unavailable or blocked.
---

# Codex GPT Expert Relay Loop

## Purpose

Use this skill to make Codex the implementation node in an expert relay system:

```text
user goal -> classify -> choose expert role and GPT mode -> generate Chrome GPT prompt
-> if explicit loop was requested, run captured Chrome GPT <-> Codex cycles until count/blocker/user stop
-> otherwise use at most one GPT consult/review when useful
-> implement small patch -> validate -> report
```

This replaces the retired `gpt-chrome-review-subagent` skill. Do not call the
deleted packet generator or reuse the old skill path.

## Hard State

Always preserve:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing or stale data is `UNKNOWN/BLOCKER`, never negative evidence
- Tests are health checks, not trading acceptance
- GPT is not source of truth unless it cites independently verified sources

When a task touches trading, portfolio, order, broker, acceptance, deployment, or
paper/live promotion, restate these boundaries before and after implementation.

## Default Behavior

For non-trivial goals, classify and choose the expert route before coding. Then
choose the relay mode:

- `single_gpt_consult`: use when the user asks to use GPT, asks for GPT review, or the task benefits from one external expert pass but does not explicitly request loops.
- `autonomous_chrome_relay`: use only when the user explicitly asks for N loops, repeated loops, autonomous ping-pong, GPT-Codex back-and-forth, or equivalent wording.
- `manual_user_relay`: use only when Chrome/browser automation is unavailable, login/captcha/user-session state blocks automation, a tool times out repeatedly, or the user explicitly wants to carry prompts manually.
- `direct_codex`: use only for trivial tasks, urgent best effort, or explicit user override to skip GPT.

For project, code, docs, task planning, implementation, validation, review, or
GitHub-related work, the default GPT mode is `Agent Mode` with GitHub enabled
for `minjo1009/Stock-Investment`. The prompt must tell GPT to inspect repo
context before answering Codex.

Use `Agent Mode + Deep Research` when the task needs both repo inspection and
current external facts, such as latest library compatibility, official docs,
company filings, news, macro/political updates, or industry research. Use
`Deep Research` without Agent Mode only when the task is external-research-only
and does not require repo state. Use `Normal GPT` only for pure language,
summarization, prompt wording, or brainstorming tasks that do not need repo
state.

Do not infer loop permission from these phrases by themselves:

- "use GPT skill"
- "use GPT"
- "get GPT review"
- "ask GPT once"
- "apply the GPT skill"

Those phrases mean `single_gpt_consult` unless the user also says to run N
loops, repeat, iterate, or ping-pong.

In `manual_user_relay`, first return:

```text
1. Task Classification

Task Type:
Required Expert Role:
Required GPT Mode:
Why this mode:
Required Context:
Expected Output:
Safety Boundaries:

2. Chrome GPT Prompt
```

Tell the user to run the prompt in the Chrome GPT project with GitHub enabled for
`minjo1009/Stock-Investment`. Wait for the user to paste back the Chrome GPT
result before implementation only in this manual fallback mode.

Proceed without GPT relay only when:

- the task is trivial, such as typo/copy/label updates or a short repo answer
- the user explicitly says to proceed without relay
- the task is urgent and best effort is safer than waiting

When skipping relay, state that the relay was skipped and preserve all hard
state boundaries.

## Autonomous Loop Mode

When the user requests N loops, a 10-loop pass, or says Codex and GPT should work
back and forth by themselves, treat that as permission to run the relay without
asking the user to paste prompts between steps.

An explicit N-loop request is standing authorization to continue through bounded
GPT-Codex work cycles until one of these stop conditions occurs:

- the requested loop count is completed
- the user tells Codex to stop, pause, or change direction
- Chrome/GPT automation is blocked and no capture is possible
- validation, repo SSOT, safety boundaries, secrets, destructive operations, or
  scope expansion require a human decision
- the runtime context or tool session must be checkpointed; report this as
  `PAUSED_RESOURCE_LIMIT`, not as completion or a safety blocker

Intermediate reports, commits, and pushes are checkpoints inside the loop. They
do not end the N-loop run by themselves.

An N-loop request means N captured GPT-Codex interaction cycles. It does not
mean N checklist items, N validators, N gates, N files, N commits, or N internal
reasoning passes. If fewer than N cycles run, report the exact stop reason.

When the user says "next work" or "tasks to do next", loop 1 must discover and
rank the next task candidates from repo state before implementation starts. Do
not silently replace the user's broad next-work request with a narrow validator
or pre-screen gate unless GPT/repo evidence selects that path and the loop ledger
records the selection.

In autonomous mode:

1. Load the appropriate browser/Chrome control skill before controlling Chrome.
2. Open or reuse the project ChatGPT conversation when available and record the
   relay GPT tab identity as `relay_tab_id`.
3. Send the expert prompt directly to Chrome GPT.
4. Capture or summarize GPT's response.
5. Convert the response into a bounded Codex patch plan.
6. Implement one small loop.
7. Validate.
8. Send a review prompt directly to Chrome GPT when useful.
9. Patch P0/P1 review issues or stop if GPT says PASS/BLOCKED.
10. Continue until the requested loop count, a natural completion point, or a blocker.

If a loop ledger or GPT response marks the next item as `selected`, promote it
to `active` and continue in the same autonomous run unless a stop condition
above applies. Do not ask the user for fresh permission merely because the item
was previously a queue candidate.

The rule "queue candidates are not implementation authorization" applies only
to unselected candidates, scope expansion, product-screen implementation,
DB/runtime connection, broker access, paper/live promotion, deployment
readiness, real-capital use, or other actions outside the selected loop scope.
It must not be used to stop an already requested N-loop run after a selected
safe planning/governance loop.

Every autonomous loop must produce a loop ledger row with:

```text
loop_id, user_goal, task_candidate, expert_role, gpt_mode,
prompt_artifact, gpt_response_artifact, codex_action,
validation_result, review_prompt_artifact, review_response_artifact,
status, stop_reason
```

Do not claim "GPT loop complete" unless the prompt and response artifacts exist
or the loop is explicitly marked `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`.

Do not ask the user to manually paste anything during autonomous mode unless:

- Chrome/GPT login, captcha, rate limit, upload, or response extraction blocks progress.
- The browser-control tool is unavailable or repeatedly times out.
- The next action would require secrets, broker mutation, live order, paper promotion, real-capital permission, destructive file operations, or scope expansion beyond the user goal.
- GPT output conflicts with repo SSOT and a human decision is needed.

If autonomous Chrome relay is blocked, report the blocker and provide the prompt
as a fallback. Do not pretend GPT reviewed the work if the response was not
captured.

## Chrome GPT Tab Cleanup

When Codex uses Chrome GPT in `autonomous_chrome_relay` or
`single_gpt_consult`, close the GPT Chrome tab used for the relay after these
conditions are met:

1. Prompt and response artifacts are captured or the run is marked blocked.
2. The loop ledger or consult report records the GPT capture status.
3. Any requested commit/push or no-commit decision is recorded.
4. The user-facing report can include the cleanup result.

Close only tabs that Codex opened for the relay or clearly identified as
dedicated relay GPT tabs. Do not close unrelated user Chrome tabs. If the tab was
pre-existing and may contain unrelated user work, leave it open and report
`tab_cleanup_status: skipped_preexisting_user_tab`.

If tab cleanup fails because Chrome automation is unavailable, the tab is already
closed, or the tab cannot be identified, report the exact status. Tab cleanup
failure must not change strategy, deployment, broker, paper/live, or
real-capital state.

## Single GPT Consult Mode

Use one GPT consult or review pass when GPT is requested but no loop count or
repeat instruction exists.

Required behavior:

1. Classify the task and choose expert roles/mode.
2. For project work, default to Agent Mode with GitHub repo context.
3. Send one prompt to Chrome GPT when tools are available.
4. Capture the response or mark `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`.
5. Implement only the bounded scope supported by repo evidence.
6. Close the GPT Chrome tab used for the consult when cleanup rules allow it.
7. Report the consult artifact, validation, and tab cleanup status.

Do not continue into loop 2 without an explicit user loop request.

## Task Classifier

Use one or more task types:

| Type | Use For |
| --- | --- |
| A. UI / UX / IA / Product Design | navigation, wireframes, design system, product flow |
| B. Frontend Implementation | Expo, React Native, TypeScript, Storybook, UI patches |
| C. Backend / DB / Data Pipeline | scheduler, freshness, lineage, SQLite, ingestion |
| D. Quant Strategy / Backtest / Research Methodology | OOS, leakage, factors, sizing, acceptance gates |
| E. Portfolio / Risk / Execution Control | exposure, order lifecycle, risk gates, kill switch |
| F. Company / Equity Research | single-name analysis, earnings, valuation, catalysts |
| G. Macro / Rates / FX / Liquidity | FOMC, rates, dollar, oil, liquidity, regimes |
| H. Political / Geopolitical / Policy Risk | elections, export controls, CHIPS, country risk |
| I. Semiconductor / AI Infrastructure | GPU, ASIC, CPO, datacenter capex, supply chain |
| J. Power Grid / Energy Infrastructure | grid, utilities, nuclear, transformers, power demand |
| K. Mixed | multi-domain work needing role separation |

## Expert And Mode Router

Choose expert roles from the task type:

- UI/Product: Principal Product Architect, Principal UI/UX Designer, Information Architect, Design System Engineer, React Native/Expo Architect, Vision QA Reviewer.
- Frontend: Senior React Native Engineer, Expo Architect, TypeScript Engineer, Storybook/Component-Driven Development Engineer, Mobile UI QA Reviewer.
- Backend/DB: Professional Backend Engineer, Data Platform Architect, DB Reliability Engineer, Scheduler/Pipeline Engineer, Quant Data Infrastructure Reviewer.
- Quant/Backtest: Institutional Quant Researcher, Systematic PM, Backtest Methodology Reviewer, Risk Model Reviewer, Execution-Aware Trader.
- Portfolio/Risk/Execution: Institutional Portfolio Risk Manager, Execution Trader, Order Lifecycle Architect, Trading Controls Reviewer, Compliance/Safety Gate Reviewer.
- Company Research: Institutional Equity Research Analyst, Earnings Revision Strategist, Valuation Analyst, Single-name Catalyst Trader, Equity L/S PM.
- Macro: Institutional Macro Strategist, Rates Strategist, Cross-Asset PM, Global Liquidity Analyst.
- Political/Geopolitical: Political Risk Analyst, Geopolitical Strategist, Policy Analyst, Country Risk Analyst.
- Semiconductor/AI: Semiconductor Industry Analyst, AI Infrastructure Analyst, Datacenter Capex Analyst, Hardware Systems Engineer, Supply Chain Analyst.
- Power/Energy: Power Grid Analyst, Energy Infrastructure Analyst, Utility Capex Analyst, Datacenter Power Analyst.
- Mixed: use a multi-role expert panel and separate outputs by role.

Choose GPT mode:

- `Agent Mode`: default for project, code, docs, task planning, implementation, validation, review, and SSOT comparison because GPT must read `minjo1009/Stock-Investment` through GitHub before answering Codex.
- `Agent Mode + Deep Research`: use when repo inspection and current external research are both required.
- `Deep Research`: use only for external-research-only tasks that do not require repo state.
- `Normal GPT`: use only for pure language, summary, prompt wording, or brainstorming tasks that do not require repo state.

## Source Priority

- Project/internal: GitHub repo files, approved SSOT docs, current code, current tests, prior task reports.
- Market/company: SEC, company IR, transcripts, presentations, official data, Reuters/Bloomberg/WSJ, exchange data, secondary summaries, social sentiment only as context.
- Technical/library: official docs, GitHub/release notes, changelog, issue discussions, reputable engineering posts.
- Politics/policy: official government/legislative sources, agency statements, primary speeches/docs, Reuters/AP/Bloomberg/WSJ/FT, think tanks, local media with caution.

Always separate `actual`, `estimate`, `inference`, `assumption`, and
`unavailable`.

## Implementation Rules

When the user returns a Chrome GPT prompt:

1. Extract objective, files to inspect, constraints, implementation steps, and validation commands.
2. Execute only the requested patch scope.
3. Keep changes small.
4. Reuse existing project patterns and components.
5. Do not add broker mutation, live-order paths, paper promotion, or real-capital paths.
6. Preserve fail-closed behavior, idempotency, freshness, lineage, and `UNKNOWN/BLOCKER` semantics.
7. Run available validations.
8. Commit and push only when the user requested it or the current workflow requires it.

## Report Format

After implementation, report:

```text
relay mode
- single_gpt_consult | autonomous_chrome_relay | manual_user_relay | direct_codex

loop evidence
- requested_loops:
- completed_loops:
- ledger_path:
- gpt_capture_status:
- continuation_status: continuing | completed_requested_count | blocked | paused_resource_limit | stopped_by_user
- next_loop_id:
- next_loop_action:
- tab_cleanup_status: closed | skipped_preexisting_user_tab | already_closed | failed | not_applicable

done
1. ...

failed
1. ...

blocked
1. ...

changed files
1. ...

validation
1. command: result

commit
- <hash or none>

safety boundary confirmation
1. Strategy remains NOT_ACCEPTED.
2. Deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
3. Real Capital remains FORBIDDEN.
4. No broker mutation added.
5. No live order path added.
6. No paper promotion added.
7. Missing/stale data remains UNKNOWN/BLOCKER.

next
1. If requested loops remain and no stop condition exists, continue to the next
   selected loop instead of ending with a final-style next item.
```

## References

- Read `references/prompt-templates.md` when generating the initial Chrome GPT
  prompt, the post-implementation review prompt, or the loop-state log.
