# GPT/Chrome Review Packet

## Intake

- task_id: `gpt_review_task792_relationship_graph`
- review_date: `2026-06-12`
- lane: `governance`
- objective: Critically review the Task792 information relationship graph design with institutional trader, backend engineer, macro, politics, semiconductor, AI infrastructure, and space industry lenses without treating GPT as source of truth
- owner_team: Research Governance
- reviewer_team: Relevant owner team
- output_class: `review_notes` or `ideation_notes`

## Source Artifacts To Provide

- docs/reports/task_792_information_relationship_graph_program
- docs/reports/task_773_attention_budget_contract
- docs/reports/task_791_task773_execution_handoff/task773_handoff_packet.md

## Validation Commands To Preserve

- python scripts/trader_brain_relationship_graph_validate.py
- python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .

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

## Role Assignment

Act as a combined review panel. Each role may critique relationship logic, missing validation, and overclaim risk only.

Institutional roles:

- Goldman Sachs PM desk: portfolio-level causal coherence and risk framing.
- Morgan Stanley equity strategist: thesis quality, downside case, and invalidation clarity.
- JPMorgan cross-asset macro: rates, dollar, credit, and equity transmission coherence.
- BofA positioning and liquidity desk: crowding, liquidity, and input sufficiency.
- Citi global macro desk: macro-policy spillover and scenario discipline.
- UBS risk office: risk caveat and confidence-cap discipline.
- Barclays derivatives desk: volatility, convexity, and options-relevance discipline.
- Deutsche Bank rates/credit desk: funding, rates, and credit stress links.
- Citadel market-structure desk: timestamp, microstructure, and execution-realism boundaries.
- Two Sigma systematic research: leakage, overfit, graph identity, and validator failure modes.

Domain roles:

- Political risk specialist: election, regulation, sanctions, geopolitical transmission.
- Economist: cycle, inflation, employment, productivity, and liquidity mechanism.
- Semiconductor specialist: supply chain, capex, demand, and export-control mechanism.
- AI infrastructure specialist: compute, power, data center, software, and monetization mechanism.
- Space and defense industry specialist: launch, satellite, defense procurement, and industrial policy mechanism.

Backend roles:

- Data model engineer: node identity, edge schema, and compact packet design.
- Validation engineer: deterministic checks and failure messages.
- Platform reliability engineer: graph growth limits and reproducibility.

Answer these questions:

1. Which graph edge type is ambiguous or too broad?
2. Which node identity field is missing for exact linkage?
3. Which relationship could be mistaken for causality when it is only association?
4. Which edge needs temporal precedence or as-of proof?
5. Which relationship could accidentally become a score, rank, or trade signal?
6. Which expert lens would create input sprawl if not capped?
7. Which raw source, exact ID, manifest, or validation command is missing?
8. What repo-native validation should run next?
9. What validation authority lane applies, and what does PASS not mean?

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
