# Task3866 GPT Relay Chrome Tab Cleanup

## Decision Summary

Task3866 updates the Codex-GPT expert relay skill so GPT Chrome tabs used by a
relay or single consult are closed after the run is captured and reported.

The cleanup applies only to tabs Codex opened for the relay or clearly
identified as dedicated GPT relay tabs. Unrelated user Chrome tabs must not be
closed.

## Quant Expert Report

This is a skill workflow cleanup change only.

No strategy, replay, selector, sizing, source acquisition, broker mutation,
paper/live order, deployment readiness, or real-capital workflow changed.

## No-Background Decision-Maker Report

Before this task, the skill did not say what to do with Chrome GPT tabs after a
loop or consult ended.

After this task:

1. Codex records the relay GPT tab identity as `relay_tab_id`.
2. Codex closes the GPT Chrome tab after prompt/response artifacts and ledger or
   report evidence are captured.
3. Codex does not close unrelated user tabs.
4. If cleanup is unsafe or impossible, Codex reports `tab_cleanup_status`.

## Artifact Manifest

| Artifact | Purpose |
| --- | --- |
| `skills/codex-gpt-expert-relay-loop/SKILL.md` | Adds Chrome GPT tab cleanup contract |
| `skills/codex-gpt-expert-relay-loop/references/prompt-templates.md` | Adds cleanup status to loop log |
| `skills/codex-gpt-expert-relay-loop/agents/openai.yaml` | Updates UI-facing default prompt |
| `docs/reports/task_3866_gpt_relay_chrome_tab_cleanup/task_3866_decision.csv` | Decision record |
| `docs/reports/task_3866_gpt_relay_chrome_tab_cleanup/artifact_manifest.csv` | Artifact index |

## Validation

- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/codex-gpt-expert-relay-loop`
- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/minjo/.codex/skills/codex-gpt-expert-relay-loop`
- `python scripts/task_registry_validate.py`
- `git diff --check -- skills/codex-gpt-expert-relay-loop docs/reports/task_3866_gpt_relay_chrome_tab_cleanup docs/operating_system/project_operating_state.md tasks/task_registry.csv`

## Status

Strategy remains `NOT_ACCEPTED`.
Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
Real capital remains `FORBIDDEN`.
