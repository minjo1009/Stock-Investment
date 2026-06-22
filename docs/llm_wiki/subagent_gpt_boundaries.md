# Subagent And GPT Boundaries

## GPT / Chrome

GPT/Chrome may review:

- overclaims
- missing evidence
- unclear architecture
- weak decomposition
- validation wording

GPT/Chrome may not decide:

- strategy acceptance
- deployment readiness
- broker truth
- raw source correctness
- PnL validity
- buy/sell/sizing

## Subagents

- Explorers are read-only.
- Workers need disjoint write scopes.
- Every packet must include read scope, write scope, validation command, validation authority, and forbidden actions.
- Subagent output is advisory until integrated and validated in repo artifacts.

