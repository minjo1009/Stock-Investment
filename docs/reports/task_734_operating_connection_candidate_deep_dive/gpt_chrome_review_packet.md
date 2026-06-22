# GPT/Chrome Review Packet

## Intake

- task_id: `task_734_operating_connection_candidate_deep_dive`
- review_date: `2026-06-10`
- lane: `strategy`
- objective: Institutional source-text review of the 9 Task733 operating connection candidates before any candidate bundle promotion
- owner_team: Regime Research
- reviewer_team: Research Governance
- output_class: `review_notes` or `ideation_notes`

## Source Artifacts To Provide

- docs/reports/task_733_circuit_quality_operating_connection
- docs/reports/task_722_source_attached_review_packets

## Validation Commands To Preserve

- python -m unittest tests.test_task734_operating_connection_candidate_deep_dive
- python scripts/task_registry_validate.py

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
