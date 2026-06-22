# Subagent Packet Plan For Task807-811

## Packet A: Relationship Graph Validator

Objective: Implement relationship graph CSV validation.
Owner Team: Backtest & Simulation Infra
Reviewer Team: Research Governance
Read Scope: Task792, Task803, Task805, Task806 artifacts.
Write Scope: `scripts/trader_brain_relationship_graph_packet_validate.py`
Required Outputs: schema, edge evidence, layer transition, temporal predecessor, and forbidden-output checks.
Forbidden Actions: No runtime integration, no broker integration, no strategy selection, no backtest execution.
Validation Command: `python -m unittest tests.test_trader_brain_relationship_graph_packet_validator`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet B: Negative Fixture Harness

Objective: Implement failure-first tests for the seven negative cases from Task805.
Owner Team: Data & Market Microstructure
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task805 negative fixture catalog.
Write Scope: `tests/test_trader_brain_relationship_graph_packet_validator.py`
Required Outputs: tests that fail for missing edge evidence, missing as-of, missing predecessor, missing-to-negative, expert-to-signal drift, missing mechanism id, and cross-layer jump.
Forbidden Actions: No market fixtures, no labels, no PnL, no order or fill data.
Validation Command: `python -m unittest tests.test_trader_brain_relationship_graph_packet_validator`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet C: Attention Packet Validator

Objective: Implement Task773 attention packet validator.
Owner Team: Backtest & Simulation Infra
Reviewer Team: Data & Market Microstructure
Read Scope: Task773 and Task789 artifacts.
Write Scope: `scripts/trader_brain_attention_packet_validate.py`
Required Outputs: packet schema, state, source-gap preservation, and forbidden-output checks.
Forbidden Actions: No source crawling, no missing-to-negative conversion, no trading output.
Validation Command: `python -m unittest tests.test_trader_brain_relationship_graph_packet_validator`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.

## Packet D: Cross-Layer And Temporal Guards

Objective: Ensure graph validator blocks source-to-adapter jumps and unsafe temporal chains.
Owner Team: Research Governance
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task795 and Task796 artifacts.
Write Scope: `scripts/trader_brain_relationship_graph_packet_validate.py` and tests.
Required Outputs: cross-layer jump and temporal predecessor checks.
Forbidden Actions: No L1 to L5/L6/L7 shortcut, no future leakage, no hindsight overwrite.
Validation Command: `python -m unittest tests.test_trader_brain_relationship_graph_packet_validator`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY.
Report Requirement: Follow `docs/report_standard.md`.
