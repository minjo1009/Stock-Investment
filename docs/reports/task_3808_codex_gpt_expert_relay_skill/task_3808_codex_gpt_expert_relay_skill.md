# Task3808 Codex GPT Expert Relay Skill

## Decision Summary

- Verdict: `CODEX_GPT_EXPERT_RELAY_SKILL_INSTALLED`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: no trading, replay, source, broker, or runtime metrics changed.
- What changed: installed a new project skill for the Codex-GPT expert relay loop and wired active operating docs to it.
- Next action: use the new relay skill for non-trivial goals unless the user explicitly overrides the relay.

## Quant Expert Report

### Data Source And Source Readiness

No raw market, broker, runtime, source, or DB data changed.

New skill artifacts:

- `skills/codex-gpt-expert-relay-loop/SKILL.md`
- `skills/codex-gpt-expert-relay-loop/references/prompt-templates.md`
- `skills/codex-gpt-expert-relay-loop/agents/openai.yaml`

The retired Task606 GPT/Chrome packet workflow remains deleted and historical-only.

### Exact Join Keys

Not applicable. No lifecycle, order, fill, source, or replay joins were created or modified.

### Leakage Audit

- Inferred lifecycle matching used: no.
- Missing labels treated as negatives: no.
- Missing raw sources approximated: no.
- GPT output used as source truth: no.
- Strategy acceptance changed: no.

### Split/OOS Metrics

Not applicable. This task did not run a backtest or replay.

### Failure Decomposition

The new skill separates four responsibilities:

| Responsibility | Owner |
| --- | --- |
| task classification and mode routing | Codex |
| expert prompt design / review | Chrome GPT via user relay |
| implementation and validation | Codex |
| final approval | user |

It explicitly keeps GPT output away from source truth, strategy acceptance, broker truth, buy/sell/sizing, paper/live permission, and real-capital permission.

### Cost/Slippage Stress

Not applicable. No PnL or execution-cost result changed.

### Remaining Blockers

- The user still needs to paste Chrome GPT outputs back into Codex for the relay loop.
- Automatic browser response extraction was not added.

## No-Background Decision-Maker Report

The new GPT relay skill is installed.

For non-trivial requests, Codex should classify the task, choose expert roles and GPT mode, produce a Chrome GPT prompt, wait for the returned expert prompt unless overridden, implement the scoped patch, validate, report, and generate a review prompt.

This does not change trading readiness or capital permission.

## Artifact Manifest

See `artifact_manifest.csv`.
