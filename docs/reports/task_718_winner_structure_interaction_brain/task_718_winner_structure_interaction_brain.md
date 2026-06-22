# Task718 Winner Structure Interaction Brain

## Decision Summary

- Verdict: WINNER_STRUCTURE_INTERACTION_BRAIN_BUILT_DIAGNOSTIC_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: watch and review candidates are decomposed into expectation, absorption, narrative-conflict, convexity, lifecycle, and winner-structure states.
- Next action: Review winner-structure interactions before any allocation or backtest promotion.

## Quant Expert Report

- Data scope: 5,265 candidates and 2,445 event-linked candidates.
- Inputs: Task713 evidence, Task714 economics, Task715 pricing, Task716 slot context, and Task717 review state.
- Purpose: explain why a candidate could be watch/review but still have a winner-like structure, without promoting it to a trade.
- Assignment safety: outcome, future price, top-50 labels, ticker/theme protection, and outcome-tuned thresholds are all blocked from assignment.
- Evaluation safety: top/bottom winner/loser counts are computed only in guardrail artifacts.

## No-Background Decision-Maker Report

- This does not buy anything.
- It explains the hidden structure inside watch candidates.
- The key question is now: is this watch state a weak signal, or a delayed-absorption / convexity / conflict-resolution structure?
- Capital remains forbidden.

## Artifact Manifest

- Outputs: task718_winner_structure_panel.csv, task718_interaction_graph.csv, task718_watch_decomposition.csv, task718_convexity_audit.csv, task718_guardrail_audit.csv, task718_governance_audit.csv, task_718_decision.csv, task_718_pass_fail_matrix.csv.
- Row counts: task718_winner_structure_panel.csv=5265; task718_interaction_graph.csv=26325; task718_watch_decomposition.csv=358; task718_convexity_audit.csv=6; task718_guardrail_audit.csv=10; task718_governance_audit.csv=15; task_718_decision.csv=1; task_718_pass_fail_matrix.csv=8.
- Validation command: `python -m unittest tests.test_task718_winner_structure_interaction_brain`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| scope_5265 | PRIMARY_PASS | 1 | rows=5265 | 5265 |
| event_linked_2445 | PRIMARY_PASS | 1 | event=2445 | 2445 |
| winner_states_present | PRIMARY_PASS | 1 | states=10 | >=6 |
| watch_decomposition_present | PRIMARY_PASS | 1 | rows=358 | >0 |
| interaction_graph_present | PRIMARY_PASS | 1 | edges=26325 | 5 edges per row |
| guardrail_eval_present | PRIMARY_PASS | 1 | top=50; bottom=50 | 50/50 |
| governance_all_pass | PRIMARY_PASS | 1 | min=1 | 1 |
| real_capital_forbidden | PRIMARY_PASS | 1 | FORBIDDEN | FORBIDDEN |
