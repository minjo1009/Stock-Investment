# TASK-4152 Validation Results

status: PASS

## Passes
- exists: data\artifacts\task_4152_l3_relation_graph_v2\l3_relation_edges.csv
- exists: data\artifacts\task_4152_l3_relation_graph_v2\l3_event_clusters.csv
- exists: data\artifacts\task_4152_l3_relation_graph_v2\l3_relation_graphs.csv
- exists: data\artifacts\task_4152_l3_relation_graph_v2\l3_coverage_gaps.csv
- exists: data\artifacts\task_4152_l3_relation_graph_v2\l3_relation_graph_v2_manifest.json
- edge_rows: 17276
- event_cluster_rows: 6913
- graph_rows: 11079
- coverage_gap_rows: 4627
- edge dedupe keys are unique
- graph keys are unique
- edges checked for lineage, no raw L0 bypass, direction enum, and forbidden outputs
- graphs checked for family enum, lineage, and forbidden outputs
- coverage gaps are non-negative and reason-coded
- newswire SOURCE_FAMILY/UNKNOWN collapse is routed out of normal relation graphs
- newswire mapped-but-not-article-feature gap is explicit
- price reaction/return/alpha fields absent
- graph count expanded from 27 to 11079

## Failures
- none
