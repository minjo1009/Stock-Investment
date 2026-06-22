# Loop 2 GPT Prompt

The prompt asked Chrome GPT to formalize the loop ledger schema and next-loop queue semantics after Loop 1 was implemented and pushed as commit `6eed77e`.

Requested output:

- Loop 2 Decision
- Minimal Patch Scope
- Required Ledger Schema
- Required Queue Semantics
- Codex Patch Prompt
- Validation Checklist
- Safety Boundaries

Hard constraints included:

- No product screen implementation.
- No frontend runtime code change.
- No new validators.
- No package script changes.
- No DB/runtime/KIS/Alpaca/broker connection.
- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
