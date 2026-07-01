# Task606 GPT/Chrome Review Subagent Implementation

## Decision Summary

- Verdict: implemented a persistent GPT/Chrome review subagent skill and operating contract.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Key metrics: no strategy or trading metrics changed.
- What changed: added a reusable skill, packet generator, contract, ownership links, and task registry row.
- Next action: run the seed packet through Chrome/ChatGPT only as review notes, then convert any useful finding into normal repo work.

## Quant Expert Report

### Data Source And Source Readiness

This task does not add market data or broker evidence. It adds an operating layer for reviewing existing evidence.

Source-of-truth remains:

- raw/runtime source files
- broker/order/fill/lifecycle artifacts
- exact IDs
- readiness registry
- task registry
- validation command output

GPT/Chrome output is only `review_notes` or `ideation_notes`.

### Exact Join Keys

Not applicable for this task. The new skill explicitly forbids lifecycle matching by symbol/date/price/time proximity and requires exact IDs when reviewing lifecycle, replay, chart, or packet evidence.

### Leakage Audit

The skill and contract forbid:

- missing label to negative conversion
- unavailable raw source approximation
- GPT-generated metrics
- strategy/deployment acceptance from conversation alone
- chart/screenshot proximity as lifecycle evidence

### Split/OOS Metrics

Not applicable. This is an operating-system implementation, not a backtest result.

### Failure Decomposition

The prior risk was that Chrome-controlled GPT could become an informal authority. Task606 decomposes that risk into durable controls:

| Risk | Control |
|---|---|
| GPT becomes source-of-truth | Contract and skill classify it as review/ideation only |
| One-off chat cannot be reused | Packet generator creates repeatable review packets |
| Team ownership is unclear | Lane routing maps owner and reviewer teams |
| Strategy claims get inflated | Required prompt asks for overclaim and missing-evidence review |
| UI success gets mistaken for acceptance | Skill forbids UI/Slack/screenshot success as strategy evidence |
| Sensitive data leaks to ChatGPT | Skill requires bounded excerpts and secret removal before transmission |

### Seed Packet

Task606 generated the first persistent packet:

- `docs/reports/task_606_gpt_chrome_review_subagent_implementation/gpt_chrome_review_packet.md`

This packet is Pilsu-led and strategy-gate oriented. It has not been used to change any acceptance status. Any future Chrome/ChatGPT response must be recorded separately as `review_notes`.

### Cost / Slippage Stress

Not applicable. The skill requires cost/slippage review for strategy or backtest claims but does not itself claim PnL.

### Remaining Blockers

- The subagent is ready as a workflow, but it has not yet recorded live Chrome/ChatGPT review notes against a current dashboard or backtest artifact.
- The next real use should create a task-level packet and record GPT output as `review_notes`, not as a status change.

## No-Background Decision-Maker Report

We now have a project-native GPT/Chrome review subagent.

This means future GPT conversations should not be improvised. A team lead creates a packet, sends bounded evidence to GPT/Chrome, receives review notes, then converts useful findings into normal repo work with owner, artifact, and validation command.

The most important rule remains unchanged: GPT can help us think, but the repo decides.

## Artifact Manifest

See `artifact_manifest.csv`.
