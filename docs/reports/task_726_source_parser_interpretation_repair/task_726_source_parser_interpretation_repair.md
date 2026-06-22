# Task726 Source Parser Interpretation Repair

## Decision Summary

- Verdict: `SOURCE_PARSER_INTERPRETATION_REPAIRED_DIAGNOSTIC_ONLY`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Backtest permission: `FAIL`
- Main result: repaired parser removed the false cashflow queue. Task722 queue1 is now `0`.

## Quant Expert Report

This task repairs the source interpretation layer that fed Task722 through Task725. The previous parser let weak terms such as contract, order, purchase, agreement, sales, and RPO act like economic evidence before checking SEC filing family or local context.

Implemented changes:

- Added source family classification before interpretation: Form 4, Schedule 13D/13G, 13F, ownership/institutional filing, financing 8-K, generic 8-K, operational company source, and macro/policy source.
- Added hard blockers for ownership, insider, financing, governance/compensation, generic SEC boilerplate, and weak-keyword-only contexts.
- Added term-boundary matching so `rpo`, `sales`, `order`, or `contract` cannot match inside unrelated words or generic filing text.
- Added economic certification fields: `economic_evidence_certified_flag`, `interpretation_blocker`, `source_form_family`, `weak_keyword_only_flag`, `financing_contamination_flag`, and `boilerplate_noise_flag`.
- Rebuilt Task636, Task722, Task723, Task724, and Task725 outputs.

Key numbers:

| Metric | Before | After |
|---|---:|---:|
| Task722 cashflow-ready queue | 26 | 0 |
| Task725 queue1 deep review | 26 | 0 |
| Task636 economic evidence certified events | not separated | 1 |
| Institution/ownership economic evidence | inflated by certified source text | 0 |
| Stable predictive content features | previously looked positive | 0 |

GPT review was used as a code-review critic, not as a source of market truth. Its required repair sequence was: filing family -> context blocker -> keyword extraction -> certification -> interpretation. This sequence is now reflected in `score_event_text`.

## No-Background Decision-Maker Report

- We were reading many SEC filings wrong.
- Form4, 13G, 13D, 13F, board/compensation filings, and financing agreements were leaking into "good company event" logic.
- After repair, the fake cashflow candidates disappeared.
- That means the old backtest signal was not reliable.
- Next work is not backtest. Next work is fixing the remaining semantic/noise taxonomy gaps.

## Artifact Manifest

- `task_726_decision.csv`
- `task_726_pass_fail_matrix.csv`
- `task726_parser_repair_audit.csv`
- `task726_gpt_review_summary.csv`
- `task_726_source_parser_interpretation_repair.md`
- `artifact_manifest.csv`
