# Task3812 Codex GPT Relay Trigger Evidence Contract

## Decision Summary

- Verdict: `CODEX_GPT_RELAY_TRIGGER_EVIDENCE_CONTRACT_CORRECTED`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: no trading, replay, source, broker, or runtime metrics changed.
- What changed: corrected the GPT relay skill so GPT use, single consult, and explicit N-loop execution are separate modes.
- Next action: require loop ledger evidence before claiming a GPT-Codex loop completed.

## Quant Expert Report

### Data Source And Source Readiness

No raw market, broker, runtime, source, or DB data changed.

Updated skill artifacts:

- `skills/codex-gpt-expert-relay-loop/SKILL.md`
- `skills/codex-gpt-expert-relay-loop/references/prompt-templates.md`
- `skills/codex-gpt-expert-relay-loop/agents/openai.yaml`

The local Codex skill mirror was refreshed at:

- `C:/Users/minjo/.codex/skills/codex-gpt-expert-relay-loop`

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

The previous wording still allowed a model to confuse three separate ideas:

| Request | Correct Mode |
| --- | --- |
| `use GPT` / `use GPT skill` / `get GPT review` | `single_gpt_consult` |
| explicit N-loop / repeat / GPT-Codex ping-pong | `autonomous_chrome_relay` |
| trivial or urgent no-relay work | `direct_codex` |

Task3812 adds the rule that an N-loop means N captured GPT-Codex interaction cycles. It cannot be replaced by N validators, gates, files, commits, or internal reasoning passes.

For broad `next work` requests, loop 1 must discover and rank next task candidates from repo state before implementation starts.

### Cost/Slippage Stress

Not applicable. No PnL or execution-cost result changed.

### Remaining Blockers

- Actual autonomous Chrome relay still depends on available browser/Chrome control tools and a responsive logged-in GPT session.
- If GPT capture is blocked, the loop must be marked `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`.

## No-Background Decision-Maker Report

The GPT skill now says what the user meant.

Using GPT is not automatically a loop. A loop happens only when the user asks for loops or repeated GPT-Codex ping-pong.

If a loop is claimed, there must be evidence for each GPT-Codex interaction.

## Artifact Manifest

See `artifact_manifest.csv`.
