# TASK-4150 Validation Results

status: PASS

## Passes
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_input_manifest.json
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_meanings.jsonl
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_evidence_edges.jsonl
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_relation_graph.json
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_blocker_gap_ledger.csv
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_validator_report.json
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_review_summary.csv
- exists: data\artifacts\task_4150_l3_diagnostic_strategy_view_bootstrap\l3_rejected_or_review_queue.csv
- meaning_rows: 2780
- edge_rows: 2780
- row reconciliation balanced
- coverage gaps include incomplete backfill
- UNKNOWN/missing gaps are not negative evidence
- UNKNOWN mapping rows not active
- active L3 rows keep lineage and calibration closed
- edges keep authority closed
- graph states and authority valid
- L3 input manifest does not directly consume L0 raw

## Failures
- none
