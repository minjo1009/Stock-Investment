# Task3816 Codex GPT Loop Continuation Contract

## Decision Summary

Task3816 fixes the GPT relay skill issue that allowed a requested N-loop run to
stop after only two completed loops.

The skill now states that an explicit N-loop request is standing authorization
to continue selected, bounded GPT-Codex loops until the requested count, a user
stop, an automation blocker, validation/SSOT/safety blocker, scope expansion
approval need, or `PAUSED_RESOURCE_LIMIT`.

## Quant Expert Report

No strategy, replay, selector, sizing, source acquisition, broker mutation,
paper/live order, deployment readiness, or real-capital workflow changed.

The change is governance-only. It clarifies Codex-GPT loop control semantics and
does not authorize product screens, DB/runtime connection, broker access, paper
promotion, live deployment, or capital use.

## No-Background Decision-Maker Report

Problem:

1. The skill correctly said N-loop requests require explicit user wording.
2. It did not clearly say that once the user gives that wording, Codex should
   continue selected loops without asking again.
3. The ledger's non-authorization rule could be misread as "selected Loop 3
   still needs fresh permission."

Fix:

1. N-loop is now standing authorization for bounded selected loops.
2. `selected` rows must be promoted to `active` in the same run.
3. Commits, pushes, and reports are checkpoints, not stop reasons.
4. If the run must stop early, Codex must report the exact stop reason.

## Artifact Manifest

| Artifact | Purpose |
| --- | --- |
| `skills/codex-gpt-expert-relay-loop/SKILL.md` | Loop continuation contract |
| `skills/codex-gpt-expert-relay-loop/references/prompt-templates.md` | GPT prompt continuation instruction |
| `skills/codex-gpt-expert-relay-loop/agents/openai.yaml` | UI default prompt |
| `docs/llm_wiki/codex_gpt_expert_relay_loop_ledger.md` | Ledger continuation semantics |
| `docs/reports/task_3816_codex_gpt_loop_continuation_contract/task_3816_decision.csv` | Decision record |
| `docs/reports/task_3816_codex_gpt_loop_continuation_contract/artifact_manifest.csv` | Artifact index |

## Validation

- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/codex-gpt-expert-relay-loop`
- `python C:/Users/minjo/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/minjo/.codex/skills/codex-gpt-expert-relay-loop`
- `python scripts/task_registry_validate.py`
- `git diff --check -- skills/codex-gpt-expert-relay-loop docs/llm_wiki/codex_gpt_expert_relay_loop_ledger.md docs/reports/task_3816_codex_gpt_loop_continuation_contract docs/operating_system/project_operating_state.md tasks/task_registry.csv`

## Status

Strategy remains `NOT_ACCEPTED`.
Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
Real capital remains `FORBIDDEN`.
