# Task3813 Codex GPT GitHub Agent Mode Default

## Decision Summary

Task3813 tightened the Codex-GPT expert relay skill so project work defaults to
GPT Agent Mode with GitHub enabled for `minjo1009/Stock-Investment`.

The rule now distinguishes:

- Project/code/docs/task planning/review work: default `Agent Mode` with repo context.
- Repo plus current external facts: `Agent Mode + Deep Research`.
- External-research-only work: `Deep Research`.
- Pure language/prompt/brainstorming work: `Normal GPT`.

This task changes only skill routing and prompt wording.

## Quant Expert Report

No strategy, replay, selector, sizing, paper/live order, broker mutation,
deployment readiness, or real-capital workflow was changed.

GPT remains review/context only. GPT output is not source of truth unless
independently verified against repo SSOT or external primary/high-quality
sources.

## No-Background Decision-Maker Report

Before this task, the skill mentioned GitHub and Agent Mode, but it did not
force project work to use GitHub-backed Agent Mode by default.

After this task:

1. GPT project work must ask Chrome GPT to enable GitHub and read
   `minjo1009/Stock-Investment`.
2. Deep Research is added only when current external facts are needed.
3. Normal GPT is limited to non-repo language or brainstorming tasks.
4. Loop rules remain unchanged: loops require explicit N-loop/repeat/ping-pong
   wording.

## Artifact Manifest

| Artifact | Purpose |
| --- | --- |
| `skills/codex-gpt-expert-relay-loop/SKILL.md` | Default mode and routing contract |
| `skills/codex-gpt-expert-relay-loop/references/prompt-templates.md` | Chrome GPT prompt contract |
| `skills/codex-gpt-expert-relay-loop/agents/openai.yaml` | UI-facing skill prompt |
| `docs/reports/task_3813_codex_gpt_github_agent_mode_default/task_3813_decision.csv` | Machine-readable decision |
| `docs/reports/task_3813_codex_gpt_github_agent_mode_default/artifact_manifest.csv` | Task artifact index |

## Validation

- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/codex-gpt-expert-relay-loop`
- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/minjo/.codex/skills/codex-gpt-expert-relay-loop`
- `python scripts/task_registry_validate.py`
- `git diff --check -- skills/codex-gpt-expert-relay-loop docs/reports/task_3813_codex_gpt_github_agent_mode_default docs/operating_system/project_operating_state.md tasks/task_registry.csv`

## Status

Strategy remains `NOT_ACCEPTED`.
Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
Real capital remains `FORBIDDEN`.
