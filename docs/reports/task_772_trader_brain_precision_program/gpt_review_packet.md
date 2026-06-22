# GPT Review Packet For Task772-781

## Role

External institutional strategy and backend engineering reviewer.

GPT/Chrome status: review-only.

## Sanitized Input

```yaml
program_context: Task756-771 completed as research-only brain contracts
current_gap: future controlled adapter needs a more trader-like reasoning spine before implementation
design_goal: make the brain more like an experienced trader without excessive source ingestion
current_status:
  strategy: NOT_ACCEPTED
  deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
  real_capital: FORBIDDEN
hard_boundaries:
  - no buy/sell output
  - no rank or alpha score
  - no actual sizing
  - no backtest execution
  - no GPT facts as source-of-truth
  - no missing data as negative label
  - no inferred lifecycle matching
review_questions:
  - What reasoning stages are missing after Task771?
  - Where can overengineering or input sprawl enter?
  - How should a backend adapter boundary be protected?
  - What should subagents own separately?
explicit_redactions:
  - secrets
  - broker data
  - private Slack or email
  - cookies
  - account information
```

## Prompt Contract

Use only supplied project facts. Do not invent performance results, market data, source claims, broker facts, or acceptance status.

Review the 10-step plan as a Goldman Sachs / Morgan Stanley / Citadel / Millennium / Two Sigma style institutional strategy and backend engineering panel.

Return:

1. strongest design improvements
2. overengineering risks
3. backend boundary risks
4. subagent allocation critique
5. explicit do-not-do list

Label every item as `interpretation`, `inference`, or `source_gap`.

## Authority

GPT review can improve wording, decomposition, and missing-evidence checks.

GPT review cannot certify facts, strategy validity, PnL validity, deployment readiness, broker truth, or real-capital permission.
