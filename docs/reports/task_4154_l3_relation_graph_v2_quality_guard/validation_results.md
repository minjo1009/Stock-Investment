# TASK-4154 Validation Results

status: PASS

## Passes
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_graph_quality_summary.csv
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_graph_quality_summary.json
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_event_clusters_with_limitations.csv
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_unsupported_relation_families.csv
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_coverage_gap_summary_by_reason_source_date.csv
- exists: data\artifacts\task_4154_l3_relation_graph_v2_quality_guard\l3_l4_diagnostic_handoff_manifest.json
- quality csv/json row counts reconcile
- quality graph total reconciles: 11079
- quality edge total reconciles: 17276
- quality summary required fields present
- event cluster limitation rows reconcile
- event clusters marked PROTO_BUCKET
- same_event_assertion is false for every cluster
- unsupported relation families declared
- unsupported families are marked NOT_IMPLEMENTED
- newswire article feature coverage gap remains visible
- coverage gap summary reconciles to source gaps
- handoff flag valid: diagnostic_only
- handoff flag valid: strategy_status
- handoff flag valid: deployment_status
- handoff flag valid: real_capital
- handoff flag valid: no_broker_mutation
- handoff flag valid: no_live_order
- handoff flag valid: no_paper_promotion
- handoff flag valid: event_identity_status
- handoff flag valid: same_event_assertion
- handoff forbidden assumptions present
- public newswire UNKNOWN collapse remains outside normal relation graphs
- no forbidden trading output values in TASK-4154 outputs

## Failures
- none
