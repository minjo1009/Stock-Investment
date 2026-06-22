# Subagent Packet Plan For Task792-801

## Packet A: Node Identity

Objective: Define graph node identity for existing Task773-791 objects.
Owner Team: Data & Market Microstructure
Reviewer Team: Research Governance
Read Scope: Task773, Task774, Task775, Task779 artifacts.
Write Scope: `docs/reports/task_793_information_node_identity_contract/`
Required Outputs: node identity contract, node schema, decision csv, manifest.
Expert Review Lenses: Deutsche Bank rates/credit for source timing; UBS risk office for confidence-cap ownership; Data model engineer for mechanism_id, predecessor_node_id, and edge_evidence_id.
Forbidden Actions: No inferred identity, no GPT-only node, no symbol/date/price/time fallback.
Validation Command: `python scripts/trader_brain_relationship_graph_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet B: Edges And Layer Links

Objective: Define relation edge taxonomy and cross-layer transition rules.
Owner Team: Regime Research
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task763 relation schema, Task776 hypothesis ladder, Task792 edge taxonomy.
Write Scope: `docs/reports/task_794_relationship_edge_taxonomy_contract/` and `docs/reports/task_795_cross_layer_link_contract/`
Required Outputs: edge catalog, layer link contract, decision csv files, manifests.
Expert Review Lenses: Goldman Sachs PM desk for coherence overclaim; Barclays derivatives for volatility noise; Two Sigma for score leakage; Validation engineer for transition checks.
Forbidden Actions: No total score, no hidden priority, no source-to-trade shortcut.
Validation Command: `python scripts/trader_brain_relationship_graph_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet C: Temporal And Mechanism Graph

Objective: Define temporal update chains and mechanism/theme graph.
Owner Team: Regime Research
Reviewer Team: Data & Market Microstructure
Read Scope: Task784-787 expert filters, Task779 journal trace, Task792 graph program.
Write Scope: `docs/reports/task_796_temporal_update_chain_contract/` and `docs/reports/task_797_mechanism_theme_graph_contract/`
Required Outputs: temporal chain contract, mechanism graph contract, decision csv files, manifests.
Expert Review Lenses: JPMorgan cross-asset macro; Citi global macro; political risk specialist; economist; semiconductor specialist; AI infrastructure specialist; space and defense industry specialist.
Forbidden Actions: No future leakage, no hindsight overwrite, no theme promotion.
Validation Command: `python scripts/trader_brain_relationship_graph_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet D: Conflict And Memory Integration

Objective: Define contradiction propagation and graph retention/eviction rules.
Owner Team: Research Governance
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task777, Task778, Task790, Task775 artifacts.
Write Scope: `docs/reports/task_798_conflict_invalidation_graph_contract/` and `docs/reports/task_799_attention_memory_graph_integration/`
Required Outputs: invalidation graph contract, retention rules, decision csv files, manifests.
Expert Review Lenses: Morgan Stanley equity strategist for downside invalidation; BofA positioning/liquidity for input sprawl; Platform reliability engineer for graph growth limits.
Forbidden Actions: No missing-as-negative, no source_gap rescue, no unlimited graph growth.
Validation Command: `python scripts/trader_brain_relationship_graph_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet E: Validator And Handoff Revision

Objective: Design graph validators and revise Task773 handoff.
Owner Team: Backtest & Simulation Infra
Reviewer Team: Research Governance
Read Scope: Task792-799 artifacts and Task791 handoff.
Write Scope: `docs/reports/task_800_relationship_graph_validator_design/` and `docs/reports/task_801_task773_validator_handoff_revision/`
Required Outputs: validator design, revised handoff, decision csv files, manifests.
Expert Review Lenses: Citadel market-structure desk for timestamp realism; Two Sigma for leakage and overfit checks; Validation engineer for deterministic failures.
Forbidden Actions: No production implementation, no backtest, no strategy selection.
Validation Command: `python scripts/trader_brain_relationship_graph_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.
