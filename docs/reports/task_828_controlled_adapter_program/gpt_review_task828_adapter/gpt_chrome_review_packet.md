# GPT/Chrome Review Packet

## Intake

- task_id: `gpt_review_task828_adapter`
- review_date: `2026-06-13`
- lane: `backtest`
- objective: Review controlled adapter design for overclaim, leakage, and forbidden backtest execution risk
- owner_team: Backtest & Simulation Infra
- reviewer_team: Research Governance
- output_class: `review_notes` or `ideation_notes`

## Source Artifacts To Provide

- docs/reports/task_823_candidate_bundle_adapter_contract
- docs/reports/task_826_backtest_adapter_readiness_checklist
- docs/reports/task_828_controlled_adapter_program

## Validation Commands To Preserve

- python scripts/trader_brain_828_839_program_validate.py

## Validation Authority Boundary

Use `docs/architecture/test_validation_canonicalization_map.md`.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN

## GPT/Chrome Prompt

You are a skeptical reviewer for a governed quant trading repository.
Review only the supplied excerpts, screenshots, and artifact paths.
Return findings that can be mapped back to repo-native evidence.

Answer these questions:

1. Which statement sounds stronger than the supplied evidence?
2. Which raw source, exact ID, manifest, or validation command is missing?
3. Could this be mistaken for strategy acceptance or deployment readiness?
4. Is any proxy PnL, runtime synthetic SELL, Slack success, UI polish, or screenshot success being promoted as broker truth?
5. What repo-native validation should run next?
6. What validation authority lane applies, and what does PASS not mean?

## Forbidden Actions

- Do not declare the strategy accepted, profitable, or deployment-ready.
- Do not infer lifecycle identity by symbol/date/price/time proximity.
- Do not invent raw sources, labels, fills, metrics, or chart markers.
- Do not treat missing labels as negatives.
- Do not change registry, readiness, blocker, or acceptance status.
- Do not request secrets, tokens, cookies, passwords, or full private raw datasets.
- Do not treat passing tests as strategy acceptance, deployment readiness, broker truth completion, or real-capital permission.

## Return Format

```text
review_status: review_notes | ideation_notes | rejected
findings:
- severity:
  evidence_reference:
  issue:
  repo_native_validation:
  validation_authority:
  owner_team:
  pass_does_not_mean:
forbidden_output_detected:
- ...
next_action:
- ...
```
