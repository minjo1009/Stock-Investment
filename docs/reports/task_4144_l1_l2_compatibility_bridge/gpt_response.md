# TASK-4144 GPT Pro Response Capture

Chrome clipboard capture timed out, so this file records the final response content captured from the visible DOM snapshot.

## Core Diagnosis

GPT agreed with the user diagnosis:

> The current bottleneck is not that L2 is conceptually wrong. The bottleneck is that L1 has not materialized enough L2-compatible packets. This is an L1/L2 compatibility and handoff gap.

## Main Recommendation

The next task should be:

`TASK-4144 - L1/L2 Compatibility Bridge v1`

Success criteria:

| Rule | Meaning |
|---|---|
| L2 must not read L0 directly | No raw/headlines parsing in L2 |
| L1 must classify broader bounded rows | ready / review / archive / blocked |
| capture time is availability only | never actual publication time |
| source-time missing rows are not over-promoted | no forced certification |
| L2 remains admission/read only | no score, signal, return, order |

## Recommended Statuses

| Status | Meaning |
|---|---|
| `L2_CONTEXT_ACTIVE_READY` | L3 active research read is allowed |
| `L2_CONTEXT_ARCHIVE_READY` | L3 archive/context read is allowed |
| `L2_DISCOVERY_REVIEW_READY` | discovery row, review queue only |
| `L2_MAPPING_REVIEW_READY` | mapping review queue only |
| `BLOCKED_SOURCE_TIME_FOR_L2` | source-time is not sufficient for L2 |
| `BLOCKED_RAW_INTEGRITY_FOR_L2` | raw path/hash evidence is insufficient |
| `BLOCKED_L1_SCOPE_NOT_MATERIALIZED` | L0 shows possible data, but L1 packet/handoff is not materialized |

## Capture Time Guidance

| Case | Treatment |
|---|---|
| real source/publication time present | can support L2 timing |
| day-level publication date | can be enough for swing, mark precision |
| Wikimedia nominal noon | allowed only as imputed nominal time |
| capture time only | availability evidence only, not publication/event time |
| missing source time | block or review; do not source-time certify |

## Overengineering Cut

| Proposal | Decision |
|---|---|
| L2 parses L0 raw/headlines directly | HARD CUT |
| promote all L0 rows to source-time certified | HARD CUT |
| use capture time as publication time | HARD CUT |
| DB migration | CUT |
| LLM sentiment/entity resolution | CUT |
| embedding dedup | CUT |
| return/alpha/signal/ranking | HARD CUT |
| solve stopped backfill lanes in L2 | CUT |

## Practical Implementation

Create a task-local artifact-first bridge:

- `l1_l2_compatibility_matrix.csv`
- `l1_l2_compatibility_handoff.csv`
- `l1_l2_scope_gap_report.csv`
- `l1_l2_timestamp_basis_audit.csv`
- `l2_from_compatibility_handoff.csv`
- validator and QA report

The bridge should use L1 packets when present and L0 audit only as evidence of scope gaps or blocked candidates, not as direct L2 input.
