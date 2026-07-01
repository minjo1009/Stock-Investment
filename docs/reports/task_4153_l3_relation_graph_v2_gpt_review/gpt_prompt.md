# GPT Pro Prompt: TASK-4153 L3 Relation Graph V2 Review

You are reviewing a local working copy that may not be fully reflected in GitHub.

Act as:

1. Professional Backend Engineer
2. Quant Data Infrastructure Reviewer
3. Professional Trader
4. Systematic PM / Trading Research Reviewer

Do not assume GitHub has the latest TASK-4152 local changes. Use the detailed current-state packet below as the source of truth for the latest local work. You may use GitHub only for broader project context if available, but do not override the local packet with stale GitHub state.

Project hard state:

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`
- No broker mutation
- No live order
- No paper promotion
- Missing/stale/incomplete data is `UNKNOWN/BLOCKER`, never negative evidence
- L3 is diagnostic/relation infrastructure only
- Do not recommend BUY/SELL, ranking, sizing, order intent, paper/live eligibility, broker mutation, strategy acceptance, or deployment readiness.

User goal:

The user wants GPT Pro review of the current L3 relation graph after TASK-4152. The specific concern is whether the graph expansion from 27 graphs to 5,398 graphs is a real structural improvement or just count inflation.

Please review as if you are advising Codex before the project moves toward Layer 4 thesis bundles.

## Current Local State Packet

### Baseline Before TASK-4152

TASK-4150 L3 bootstrap output:

| item | count |
|---|---:|
| L3 meanings | 2,780 |
| L3 evidence edges | 2,780 |
| L3 relation graphs | 27 |
| L3 rejected/review queue | 0 |
| coverage gaps | 2 |
| validator | PASS |

Known issue:

- public newswire rows collapsed into `SOURCE_FAMILY/public_newswire_feeds` with `economic_dimension=UNKNOWN`.
- graph key was too coarse: `target_type|target_key|economic_dimension|swing_1m`.
- no event cluster artifact existed.
- no separate relation-edge table existed beyond basic evidence edges.
- macro/sector/theme/contradiction taxonomy was incomplete.

### TASK-4152 Current Output

Artifact directory:

`data/artifacts/task_4152_l3_relation_graph_v2`

Input lineage:

- `data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap/l3_meanings.jsonl`
- `data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap/l3_relation_graph.json`
- `data/artifacts/task_4150_l3_diagnostic_strategy_view_bootstrap/l3_rejected_or_review_queue.csv`
- `data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l2_diagnostic_feature_rows.csv`
- `data/artifacts/task_4147_l0_l2_hardening_gpt_review_and_implementation/l1_article_packets.csv`
- `data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l2_feature_materialization_candidates.csv`
- `data/artifacts/task_4146_l0_l2_wide_packetization_handoff/l1_wide_normalized_source_packets.csv`

Important: L3 v2 does not directly read raw L0 rows for graph creation.

TASK-4152 counts:

| artifact | count |
|---|---:|
| `l3_relation_edges.csv` | 7,150 |
| `l3_event_clusters.csv` | 1,850 |
| `l3_relation_graphs.csv` | 5,398 |
| `l3_coverage_gaps.csv` | 181 |

Graph family distribution:

| graph_family | graph count |
|---|---:|
| `SOURCE_EVENT_CLUSTER` | 1,850 |
| `ENTITY_EVENT` | 1,771 |
| `ENTITY_DIMENSION` | 947 |
| `MACRO_FACTOR` | 828 |
| `COVERAGE_GAP` | 2 |

Edge family distribution:

| graph_family | edge count |
|---|---:|
| `SOURCE_EVENT_CLUSTER` | 2,599 |
| `ENTITY_EVENT` | 1,771 |
| `ENTITY_DIMENSION` | 1,771 |
| `MACRO_FACTOR` | 828 |
| `COVERAGE_GAP` | 181 |

Coverage gap distribution:

| reason_code | count |
|---|---:|
| `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` | 181 |

TASK-4152 validator status: PASS.

Validator checks passed:

- required files exist
- edge rows: 7,150
- event cluster rows: 1,850
- graph rows: 5,398
- coverage gap rows: 181
- edge dedupe keys are unique
- graph keys are unique
- every edge has L1/L2 lineage
- no direct raw L0 bypass
- direction enum is valid
- no forbidden trading outputs
- graph family enum is valid
- coverage gaps are non-negative and reason-coded
- public newswire `SOURCE_FAMILY/UNKNOWN` collapse is routed out of normal relation graphs
- `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` gap is explicit
- price reaction/return/alpha fields are absent
- graph count expanded from 27 to 5,398

Core implementation summary:

- Build v2 relation graph from existing L3 meanings plus L1/L2 lineage artifacts.
- Do not use raw L0 rows directly.
- Convert normal symbol/entity rows into:
  - `SOURCE_EVENT_CLUSTER`
  - `ENTITY_EVENT`
  - `ENTITY_DIMENSION`
  - `MACRO_FACTOR`, when macro relevant
- Convert public newswire `SOURCE_FAMILY/UNKNOWN` collapse into `COVERAGE_GAP` instead of pretending it is a normal relation.
- Keep all outputs diagnostic-only.

## Review Questions

Please answer directly.

1. Is the 27 -> 5,398 graph expansion conceptually valid, or does it look like duplicate/noise inflation?
2. Are the graph families implemented so far useful enough for L3?
3. Is routing public newswire `SOURCE_FAMILY/UNKNOWN` into `NEWSWIRE_MAPPED_BUT_NO_ARTICLE_L2_FEATURE` coverage gaps the right interim treatment?
4. Is `SOURCE_EVENT_CLUSTER` currently too granular because it is based on `l1_packet_id|economic_dimension|event_time_bucket`, or is that acceptable until better event identity exists?
5. Are `MACRO_SECTOR`, `SECTOR_THEME`, and `CONTRADICTION` acceptable as not-yet-implemented, or should they be P0 before L4?
6. Is this L3 v2 good enough to feed Layer 4 thesis bundle as diagnostic input only?
7. What specific P0/P1 code or validation changes should Codex make next?

## Required Output

Use this exact structure:

1. Verdict
   - PASS / CONDITIONAL PASS / FAIL / BLOCKED
   - One plain-language conclusion

2. Is the graph expansion real or inflated?
   - Explain with evidence from the numbers above.

3. L3 role fit
   - Does this implementation match L3's role?

4. Graph family assessment
   - Table: family, current value, risk, recommendation

5. Newswire treatment assessment
   - Was coverage-gap routing correct?
   - What must happen next?

6. L4 readiness
   - Can Layer 4 consume this as diagnostic input?
   - What must Layer 4 avoid assuming?

7. P0/P1 Issues
   - Table: priority, issue, why it matters, concrete fix

8. Codex Patch Prompt
   - A bounded implementation prompt for Codex.
   - Avoid over-engineering.
   - Do not open trading authority.

