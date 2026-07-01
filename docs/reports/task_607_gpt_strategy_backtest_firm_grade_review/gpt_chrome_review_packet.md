# GPT/Chrome Review Packet

## Intake

- task_id: `task_607_gpt_strategy_backtest_firm_grade_review`
- review_date: `2026-06-06`
- lane: `backtest`
- objective: Review what the Task505/509/512 backtest strategy needs to become firm-grade professional quant trader real-money candidate without overclaiming acceptance
- owner_team: Backtest & Simulation Infra
- reviewer_team: Research Governance
- output_class: `review_notes` or `ideation_notes`

## Source Artifacts To Provide

- docs/reports/task_505_two_year_pnl_grid/task_505_two_year_pnl_grid.md
- docs/reports/task_508_cost_stress_validation/task_508_cost_stress_validation.md
- docs/reports/task_509_walk_forward_oos_validation/task_509_walk_forward_oos_validation.md
- docs/reports/task_512_backtest_correctness_overfit_audit/task_512_backtest_correctness_overfit_audit.md
- docs/ownership/current_operating_model.md
- docs/reports/task_599_strategy_acceptance_program/task_599_strategy_acceptance_program.md

## Validation Commands To Preserve

- python -m unittest tests.test_task512_backtest_correctness_overfit_audit
- python -m unittest tests.test_task508_511_task505_validation
- python validate_readiness_registry.py

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

## Forbidden Actions

- Do not declare the strategy accepted, profitable, or deployment-ready.
- Do not infer lifecycle identity by symbol/date/price/time proximity.
- Do not invent raw sources, labels, fills, metrics, or chart markers.
- Do not treat missing labels as negatives.
- Do not change registry, readiness, blocker, or acceptance status.
- Do not request secrets, tokens, cookies, passwords, or full private raw datasets.

## Return Format

```text
review_status: review_notes | ideation_notes | rejected
findings:
- severity:
  evidence_reference:
  issue:
  repo_native_validation:
  owner_team:
forbidden_output_detected:
- ...
next_action:
- ...
```
