# Subagent Roster And Routing

## Purpose

This document tells Codex which team, subagent style, and skill should handle each kind of work.

It prevents:

- duplicate exploration
- write-scope conflicts
- GPT output becoming source-of-truth
- one task silently changing another team's domain

## Required Packet

Every delegated subagent task must follow:

```text
Objective:
Owner Team:
Reviewer Team:
Read Scope:
Write Scope:
Inputs:
Required Outputs:
Forbidden Actions:
Validation Command:
Validation Authority:
Report Requirement:
```

Use `docs/ownership/subagent_packet_standard.md` as the exact packet standard.

## Roster

| Work Type | Owner Team | Reviewer Team | Subagent Mode | Primary Skill/Doc |
| --- | --- | --- | --- | --- |
| Project governance, registry, artifact policy | Research Governance | Relevant owner team | Governance worker | `skills/subagent-artifact-governance/SKILL.md` |
| Codex-GPT expert relay | Research Governance | Relevant owner team | External prompt/review relay | `skills/codex-gpt-expert-relay-loop/SKILL.md` |
| Legacy GPT/Chrome review | Research Governance | Relevant owner team | Retired external reviewer | Historical Task605/Task606 artifacts only; no active skill |
| Raw data/source/timestamp audit | Data & Market Microstructure | Research Governance | Data explorer first, worker second | `docs/operating_system/goal_operating_cycle.md` |
| Microstructure collection | Data & Market Microstructure | Backtest & Simulation Infra | Data worker | Task646 reports and raw data contracts |
| Strategy regime research | Regime Research | Backtest & Simulation Infra | Research explorer | `docs/architecture/canonical_workstream_map.md` |
| Intraday continuation research | Intraday Continuation Research | Regime Research | Research worker | latest intraday task report |
| Economic meaning / relation brain | Research Governance + Regime Research | Backtest & Simulation Infra | Research architecture worker | `docs/architecture/brain_layer_map.md` |
| Backtest/replay/cost/OOS | Backtest & Simulation Infra | Research Governance | Simulation worker | latest accepted backtest contract |
| Execution/broker truth/risk | Execution & Risk | Data & Market Microstructure | Execution worker | `docs/ownership/current_operating_model.md` |
| Frontend trader terminal | Frontend/UI | Research Governance | UI worker | `docs/frontend_data_contract.md` |
| Slack/EOD reporting | Research Governance | Execution & Risk | Reporting worker | Slack safety tests and Task589 reports |

## Write Scope Rules

- One worker owns one write scope.
- Two workers must not write to the same directory in parallel.
- Explorer packets are read-only.
- GPT/Chrome packets are review-only.
- Governance can write registry/report/policy files but must not alter research logic without owner review.

## Retired GPT Review Rules

The previous GPT/Chrome review skill is retired. Do not delegate new work to it.
Use the Codex-GPT expert relay skill for new non-trivial expert-prompt routing.

Historical GPT review notes may still be read as review-only artifacts. They may
include:

- project structure
- missing evidence
- interpretation logic
- firm-grade critique
- wording and narrative

GPT cannot decide:

- strategy acceptance
- deployment readiness
- broker truth
- raw source correctness
- PnL validity
- buy/sell/sizing

Any historical GPT finding that is reused must be converted into repo-native work:

```text
finding -> owner -> artifact path -> validation command -> registry/report update
```

## Validation Authority Rules

Use `docs/architecture/test_validation_canonicalization_map.md` before claiming a validation result.

- `PACKAGE_HEALTH` and `GOVERNANCE_HEALTH` may be fast local gate candidates.
- `EVIDENCE_ONLY`, `RESEARCH_ONLY`, and `SUPPORT_ONLY` are not current quality gates.
- `EXECUTION_HEALTH` and `ACCEPTANCE_EVIDENCE_REVIEW` must not be mixed into fast unit gates.
- `DATA_HEALTH` does not mean source coverage is complete.
- `REPORTING_HEALTH` does not mean trading is healthy.

Every subagent handoff must say what a PASS means and what it does not mean.

## Canonicalization Packets

When the project feels unmanaged, create a canonicalization packet instead of another feature task:

```text
Objective: Select the current canonical source for <domain>.
Owner Team: Research Governance
Reviewer Team: domain owner
Read Scope: registry, latest reports, code, tests
Write Scope: docs/architecture, docs/contracts, docs/reports/<task_id>, tasks/task_registry.csv
Required Outputs: canonical map update, supersession note, validation command
Forbidden Actions: no deletion, no artifact moves, no strategy acceptance change
Validation Command: python scripts/task_registry_validate.py
```

## Handoff Output

Every subagent must return:

```text
changed files:
artifacts:
classification:
validation:
validation authority:
not run:
next actions:
```
