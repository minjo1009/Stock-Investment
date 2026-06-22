---
name: codex-gpt-expert-relay-loop
description: Standing expert relay workflow for the Stock-Investment project. Use when a non-trivial user goal should be classified before implementation, routed to the right Chrome GPT expert role and mode, and run through an autonomous Codex-Chrome GPT ping-pong loop when browser/Chrome tools are available or when the user asks for repeated loops, a 10-loop pass, autonomous iteration, or GPT-Codex back-and-forth. Fall back to a user-sendable prompt only when automation is unavailable or blocked. Covers UI/UX, frontend, backend/DB, quant/backtest, portfolio/risk/execution, company research, macro, political/geopolitical, semiconductor/AI infrastructure, power/energy, and mixed tasks.
---

# Codex GPT Expert Relay Loop

## Purpose

Use this skill to make Codex the implementation node in an expert relay system:

```text
user goal -> classify -> choose expert role and GPT mode -> generate Chrome GPT prompt
-> send prompt to Chrome GPT directly when tools are available -> implement small patch
-> validate -> send review prompt to Chrome GPT directly when tools are available
-> patch or stop on PASS/BLOCKED
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

- `autonomous_chrome_relay`: use when Chrome/browser tools are available, or the user asks for repeated loops, a 10-loop pass, autonomous ping-pong, GPT-Codex back-and-forth, or equivalent wording.
- `manual_user_relay`: use only when Chrome/browser automation is unavailable, login/captcha/user-session state blocks automation, a tool times out repeatedly, or the user explicitly wants to carry prompts manually.
- `direct_codex`: use only for trivial tasks, urgent best effort, or explicit user override to skip GPT.

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

In autonomous mode:

1. Load the appropriate browser/Chrome control skill before controlling Chrome.
2. Open or reuse the project ChatGPT conversation when available.
3. Send the expert prompt directly to Chrome GPT.
4. Capture or summarize GPT's response.
5. Convert the response into a bounded Codex patch plan.
6. Implement one small loop.
7. Validate.
8. Send a review prompt directly to Chrome GPT when useful.
9. Patch P0/P1 review issues or stop if GPT says PASS/BLOCKED.
10. Continue until the requested loop count, a natural completion point, or a blocker.

Do not ask the user to manually paste anything during autonomous mode unless:

- Chrome/GPT login, captcha, rate limit, upload, or response extraction blocks progress.
- The browser-control tool is unavailable or repeatedly times out.
- The next action would require secrets, broker mutation, live order, paper promotion, real-capital permission, destructive file operations, or scope expansion beyond the user goal.
- GPT output conflicts with repo SSOT and a human decision is needed.

If autonomous Chrome relay is blocked, report the blocker and provide the prompt
as a fallback. Do not pretend GPT reviewed the work if the response was not
captured.

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

- `Normal GPT`: simple prompt writing, small patch planning, already-known context.
- `Agent Mode`: GitHub repo context, file inspection, implementation review, SSOT comparison.
- `Deep Research`: current external facts, official docs, company IR/SEC/transcripts, latest library compatibility, macro/political/industry research.
- `Agent Mode + Deep Research`: both repo inspection and current external research.

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
- autonomous_chrome_relay | manual_user_relay | direct_codex

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
1. Chrome GPT review captured, skipped, blocked, or generated below.
```

## References

- Read `references/prompt-templates.md` when generating the initial Chrome GPT
  prompt, the post-implementation review prompt, or the loop-state log.
