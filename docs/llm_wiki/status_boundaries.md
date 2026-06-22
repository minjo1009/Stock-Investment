# Status Boundaries

Standing status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

These statuses cannot be changed by:

- a passing test
- a strong backtest
- a source acquisition run
- a GPT/Chrome review
- an Obsidian note
- this LLM wiki

## What PASS Does Not Mean

Validator PASS does not mean:

- strategy accepted
- deployment ready
- broker truth complete
- source completeness
- strict raw/as-of complete
- paper/live trading approved
- real capital allowed

## Required Wording

When reporting project state, include:

```text
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

