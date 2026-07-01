# Canonical Workstream Map

## Purpose

This map prevents the project from becoming a pile of task files.

Each workstream must have:

- one owner team
- one current canonical source
- one validation route
- one artifact rule
- a clear promotion gate

## Workstreams

| Workstream | Owner | Current Canonical Source | Current State | Promotion Gate |
| --- | --- | --- | --- | --- |
| Project governance | Research Governance | `docs/operating_system/project_context_bootstrap.md`, `tasks/task_registry.csv` | Active cleanup required | Registry, artifact, report, and validation checks pass |
| Brain architecture | Research Governance + Regime Research | `docs/architecture/brain_layer_map.md` | Active research architecture | Layer outputs remain separated and leakage-free |
| Source evidence | Data & Market Microstructure | Task722, Task731, Task735 reports and code | Diagnostic/source routing | Raw source trace, timestamp, hash, and source path certified |
| Primitive fact extraction | Data & Market Microstructure + Research Governance | Task730, Task740 | Review-only extraction | Extracted facts are source-local and not promoted to trading |
| Economic meaning | Research Governance + Regime Research | Task742 active, Task741 audit-only | Review-only | Direction hints remain non-trading and uncertainty is explicit |
| Relation edge | Regime Research + Backtest & Simulation Infra | Task727, Task728, Task729 | Design/review-only | Edge types are validated without outcome leakage |
| Candidate bundle | Research Governance + Backtest & Simulation Infra | Task723, Task737, Task738 | Review-only | Same lifecycle identity and source trace pass |
| Slot decision | Backtest & Simulation Infra | Task723, Task690-696 family where applicable | Not accepted | Same-timestamp comparison only, no global hindsight rank |
| Backtest/replay | Backtest & Simulation Infra | Task512, Task617-646 family, current registry rows | Diagnostic only unless accepted | Split/OOS, leakage, cost/slippage, account capacity pass |
| Microstructure data lake | Data & Market Microstructure | Task646 | Raw data lake build in progress | Partition integrity and coverage pass |
| Paper execution | Execution & Risk | `docs/ownership/current_operating_model.md`, Task600-604 family | Controlled paper readiness, not deployment | Broker-truth BUY/SELL lifecycle and replay acceptance pass |
| Runtime intelligence sidecar | Data & Market Microstructure + Execution & Risk | Task615 | Collection-only | Source readiness and no-order-impact gate pass |
| Frontend trader terminal | Frontend/UI | `docs/frontend_data_contract.md`, catalog scripts | Catalog-backed UI | No raw task CSV reads from React, visual QA passes |
| Slack/EOD reporting | Research Governance | Task587, Task589, Slack safety tests | Reporting only | Delivery safety and duplicate guard pass |

## Canonical Selection Rule

When several tasks exist in one workstream:

1. Pick the latest task that has a report, decision artifact, validation command, and registry row.
2. If a newer task explicitly supersedes an older one, use the newer task.
3. If a task is diagnostic-only, do not treat it as strategy acceptance.
4. If a task creates large output panels, commit only the report/decision/manifest by default.
5. If two tasks conflict, Research Governance must write a supersession note before downstream work uses either.

## Current Brain Canonical Decision

| Layer | Active Candidate | Important Caveat |
| --- | --- | --- |
| Source evidence | Task731/735 | Router/classifier only; not operating catalyst support by itself |
| Primitive fact | Task740 | Source-semantic only; denominator joins remain separate |
| Economic meaning | Task742 | Practical review-only; no trading permission |
| Relation edge | Task728/729 | Needs renewed integration with Task742 tiers |
| Candidate bundle | Task737/738 | Attachment and requirement objects only |
| Slot decision | Task723 and later slot studies | Same-timestamp only; no global hindsight rank |

## Trader Brain Program Overlay

Task756 is the current research-only overlay for rechecking and developing the Trader Brain without changing acceptance status.

| Program Area | Step Range | Current State | Promotion Gate |
| --- | --- | --- | --- |
| Brain dependency and supersession | Task757 | Planned | Current/superseded map exists before implementation reuse |
| L1/L2/L3 contracts | Task758-Task760 | Planned | Evidence, primitive, and economic meaning contracts remain non-trading |
| Task742-to-Task729 bridge | Task761-Task762 | Planned | Adapter and primitive gate are explicit and research-only |
| Relation/modifier interactions | Task763-Task766 | Planned | Node plus modifier rules pass leakage and layer-jump checks |
| Bundle/slot/review gate | Task767-Task771 | Planned | Bundles and slot review remain same-timestamp and no acceptance claim is made |

## Commit Eligibility

Commit first:

- canonical maps
- contracts
- source code for active canonical candidates
- tests for active canonical candidates
- small reports and decisions

Hold local:

- raw source data
- full generated panels
- runtime DBs
- exploratory one-off scripts until selected
- large `docs/reports` CSV/JSONL files
