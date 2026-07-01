---
tags:
  - research-governance
  - diagnostic-only
---

# Quant Research Map

## Navigation Principle

Use this map to find current research lanes. Treat it as a pointer layer only; every claim must still be verified through reports, decision CSVs, artifact manifests, and tests.

Latest state pointer: [Project Operating State](../../operating_system/project_operating_state.md).

As of the latest operating state, Task2581-2600 joined SEC financing/dilution and liquidity/rates regime into L2/L3 selector-only diagnostics. It did not run replay and did not change selector deployment. Verify the current row in the operating state before acting.

## Core Lanes

| Lane | Primary Source | Typical Reviewer |
|---|---|---|
| Paper / Shadow Trading Prep | [Project Operating State](../../operating_system/project_operating_state.md) | Research Governance |
| MDD Attribution | [docs/reports](../../reports) | Execution & Risk |
| Brain Layer Development | [Brain Layer Map](../../architecture/brain_layer_map.md) | Research Governance |
| Data & Market Microstructure | [Task Registry](../../../tasks/task_registry.csv) | Research Governance |
| Regime Research | [docs/reports](../../reports) | Backtest & Simulation Infra |
| Backtest & Simulation Infra | [docs/reports](../../reports) | Research Governance |
| Execution & Risk | [docs/reports](../../reports) | Data & Market Microstructure |
| Research Governance | [Operating System Map](Operating System Map.md) | Relevant owner team |

## Discovery Aids

- [Graphify Report](../../../graphify-out/GRAPH_REPORT.md)
- [Graphify Context Packs](../../graphify/context_packs.json)
- [Graphify Community Labels](../../graphify/community_labels.json)
- [Graphify God Nodes](../../graphify/god_nodes_top20_local.json)

Graphify outputs were generated on 2026-04-25 and are stale for current paper-ops governance until regenerated.

## Current Blocker Themes To Search

```text
"receive timestamp"
"broker truth"
"full depth"
"blocked-source"
"diagnostic-only"
"walk-forward"
"entry-reduce"
"paper/shadow"
"selector-only"
"MDD"
```

## Report Review Order

1. Read the registry row for task status and current reference paths.
2. Read the task report's decision summary.
3. Check decision CSV and artifact manifest.
4. Open the linked validation command or test.
5. Only then follow graph/backlink discoveries.
