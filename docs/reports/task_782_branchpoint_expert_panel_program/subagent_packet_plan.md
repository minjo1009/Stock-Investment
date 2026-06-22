# Subagent Packet Plan For Task782-791

## Packet A: Institutional Panel Router

Objective: Convert the 10 institutional roles into bounded critique questions for Task783.
Owner Team: Research Governance
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task782 role matrix, Task772 precision program, Task770 validation catalog.
Write Scope: `docs/reports/task_783_institutional_trader_panel_contract/`
Inputs: Existing artifacts only.
Required Outputs: institution lens questions, blockers, decision csv, artifact manifest.
Forbidden Actions: No buy/sell/rank/score/sizing, no GPT facts as source-of-truth, no majority-vote decision.
Validation Command: `python scripts/trader_brain_branchpoint_panel_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet B: Macro Politics And Economy

Objective: Define political, geopolitical, economic, rates, inflation, and liquidity confidence caps for Task784-785.
Owner Team: Regime Research
Reviewer Team: Research Governance
Read Scope: Task760 meaning contract, Task765 modifier contracts, Task782 role matrix.
Write Scope: `docs/reports/task_784_macro_politics_filter_contract/` and `docs/reports/task_785_economic_cycle_liquidity_contract/`
Inputs: Existing artifacts only.
Required Outputs: confidence cap states, source-gap blockers, decision csv files, artifact manifests.
Forbidden Actions: No policy forecast as fact, no rate forecast trading rule, no future leakage.
Validation Command: `python scripts/trader_brain_branchpoint_panel_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet C: Specialist Theme Filters

Objective: Define semiconductor, AI infrastructure, space, defense, and industrial-policy minimal source requirements for Task786-787.
Owner Team: Data & Market Microstructure
Reviewer Team: Regime Research
Read Scope: Task758 evidence contract, Task764 source circuit policy, Task782 role matrix.
Write Scope: `docs/reports/task_786_semiconductor_ai_infra_contract/` and `docs/reports/task_787_space_defense_industrial_contract/`
Inputs: Existing artifacts only.
Required Outputs: source family requirements, noise filters, decision csv files, artifact manifests.
Forbidden Actions: No channel-check invention, no theme chasing, no ticker promotion, no backlog claim without source.
Validation Command: `python scripts/trader_brain_branchpoint_panel_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean source completeness or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet D: Backend Budget And Sufficiency State

Objective: Define backend schema limits and qualitative source sufficiency states for Task788-789.
Owner Team: Backtest & Simulation Infra
Reviewer Team: Data & Market Microstructure
Read Scope: Task771 future backtest gate, Task773 planned attention budget, Task782 role matrix.
Write Scope: `docs/reports/task_788_backend_data_budget_contract/` and `docs/reports/task_789_source_sufficiency_state_contract/`
Inputs: Existing artifacts only.
Required Outputs: max field set, required ids, timestamp boundaries, sufficiency states, decision csv files, artifact manifests.
Forbidden Actions: No inferred matching, no symbol/date/price/time fallback, no missing-to-negative conversion, no live runtime execution.
Validation Command: `python scripts/trader_brain_branchpoint_panel_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean backtest validity.
Report Requirement: Follow `docs/report_standard.md`.

## Packet E: Conflict And Handoff

Objective: Define cross-expert conflict routing and close the Task773 handoff for Task790-791.
Owner Team: Research Governance
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task769 conflict layer, Task770 validation catalog, Task782 role matrix.
Write Scope: `docs/reports/task_790_cross_expert_conflict_arbitration/` and `docs/reports/task_791_task773_execution_handoff/`
Inputs: Existing artifacts only.
Required Outputs: dissent routing, owner next check, bounded Task773 implementation packet, decision csv files, artifact manifests.
Forbidden Actions: No majority vote score, no GPT-only resolution, no source gap rescue, no implementation backtest.
Validation Command: `python scripts/trader_brain_branchpoint_panel_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance.
Report Requirement: Follow `docs/report_standard.md`.
