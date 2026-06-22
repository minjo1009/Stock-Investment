# Subagent Packet Plan For Task772-781

Every packet is bounded by `docs/ownership/subagent_packet_standard.md`.

## Packet A: Attention And Source Budget

Objective: Define minimal source intake and stop states for Task773.
Owner Team: Data & Market Microstructure
Reviewer Team: Research Governance
Read Scope: Task758 L1 evidence contract; Task764 source circuit policy; Task771 future backtest gate; Task772 step registry.
Write Scope: `docs/reports/task_773_attention_budget_contract/`
Inputs: Existing research artifacts only.
Required Outputs: attention budget contract, decision csv, artifact manifest.
Forbidden Actions: No source crawling, no raw-source approximation, no missing data as negative, no buy/sell/rank/score/sizing.
Validation Command: `python scripts/trader_brain_precision_program_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet B: Salience And Working Memory

Objective: Define non-directional salience and bounded working memory for Task774-775.
Owner Team: Regime Research
Reviewer Team: Research Governance
Read Scope: Task759 primitive fact contract; Task760 meaning contract; Task765 modifier contracts; Task772 step registry.
Write Scope: `docs/reports/task_774_salience_triage_contract/` and `docs/reports/task_775_working_memory_state_contract/`
Inputs: Existing contract artifacts only.
Required Outputs: salience triage contract, working memory contract, decision csv files, artifact manifests.
Forbidden Actions: No score, no rank, no alpha, no outcome labels, no unlimited context store.
Validation Command: `python scripts/trader_brain_precision_program_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet C: Hypothesis And Contradiction

Objective: Define hypothesis ladder and contradiction pressure for Task776-777.
Owner Team: Regime Research
Reviewer Team: Backtest & Simulation Infra
Read Scope: Task763 relation edge schema; Task766 compound interaction contract; Task769 resolver conflict layer.
Write Scope: `docs/reports/task_776_hypothesis_ladder_contract/` and `docs/reports/task_777_contradiction_pressure_contract/`
Inputs: Existing contract artifacts only.
Required Outputs: hypothesis ladder contract, contradiction pressure contract, decision csv files, artifact manifests.
Forbidden Actions: No expected return, no target label, no netting contradictions into score, no source gap rescue.
Validation Command: `python scripts/trader_brain_precision_program_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet D: Disconfirmation And Journal Trace

Objective: Define minimal contrary evidence and review-state journal trace for Task778-779.
Owner Team: Research Governance
Reviewer Team: Data & Market Microstructure
Read Scope: Task767 candidate bundle contract; Task768 same-timestamp slot contract; Task770 validation catalog.
Write Scope: `docs/reports/task_778_disconfirming_evidence_minimal_pack/` and `docs/reports/task_779_decision_journal_trace_contract/`
Inputs: Existing contract artifacts only.
Required Outputs: disconfirming evidence minimal pack, decision journal trace contract, decision csv files, artifact manifests.
Forbidden Actions: No exhaustive collection, no trade instruction, no rank, no position sizing, no performance label.
Validation Command: `python scripts/trader_brain_precision_program_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.

## Packet E: Adapter Boundary And Closeout

Objective: Define controlled adapter boundary and closeout governance for Task780-781.
Owner Team: Backtest & Simulation Infra
Reviewer Team: Research Governance
Read Scope: Task771 future backtest gate; Task770 validation catalog; project status authority matrix.
Write Scope: `docs/reports/task_780_controlled_adapter_boundary_contract/` and `docs/reports/task_781_program_governance_closeout/`
Inputs: Existing governance and contract artifacts only.
Required Outputs: adapter boundary contract, closeout report, registry update, validation log, artifact manifests.
Forbidden Actions: No backtest execution, no strategy logic, no outcome assignment, no deployment readiness, no real capital.
Validation Command: `python scripts/trader_brain_precision_program_validate.py`
Validation Authority: GOVERNANCE_HEALTH and RESEARCH_ONLY. PASS does not mean strategy acceptance or deployment readiness.
Report Requirement: Follow `docs/report_standard.md`.
