# Task623 Big Event Interpretation Scoring Sidecar

## Decision Summary

- Verdict: `IMPLEMENT_BIG_EVENT_SCORING_SIDECAR_NOT_TRADING_SIGNAL`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Big events are scored by content interpretation, not source existence.
- Scores are evaluation-only and are not order, assignment, or sizing inputs.
- Large events scored: 273 / 2291
- Recent aerospace support-entry candidates: 0
- Recent aerospace risk-off candidates: 74
- Recent aerospace sector-support watch candidates: 0

## Quant Expert Report

### Scoring Fields

| Field | Purpose |
|---|---|
| `event_scope` | big-event interpretation scoring field |
| `event_interpretation_category` | big-event interpretation scoring field |
| `transmission_channel` | big-event interpretation scoring field |
| `directional_score` | big-event interpretation scoring field |
| `transmission_strength_score` | big-event interpretation scoring field |
| `company_relevance_score` | big-event interpretation scoring field |
| `event_timestamp_quality_score` | big-event interpretation scoring field |
| `priced_in_risk_score` | big-event interpretation scoring field |
| `evidence_quality_score` | big-event interpretation scoring field |
| `materiality_score` | big-event interpretation scoring field |
| `interpretation_confidence_score` | big-event interpretation scoring field |
| `composite_interpretation_score` | big-event interpretation scoring field |
| `score_action` | big-event interpretation scoring field |
| `scoring_reason_code` | big-event interpretation scoring field |
| `support_entry_certified_flag` | big-event interpretation scoring field |
| `risk_off_certified_flag` | big-event interpretation scoring field |
| `sector_support_watch_flag` | big-event interpretation scoring field |
| `source_presence_only_used_flag` | big-event interpretation scoring field |
| `gpt_score_used_as_source_flag` | big-event interpretation scoring field |

### Score Summary

| Lane | Category | Action | Events | Avg Score | Support | Risk-Off | Sector Watch |
|---|---|---|---:|---:|---:|---:|---:|
| `institution_investment_actions` | `ownership_or_insider_filing_only` | `hold_until_confirmed` | 9650 | 0.0000 | 0 | 0 | 0 |
| `ceo_ir_transcripts_and_presentations` | `generic_company_filing_uninterpretable` | `source_gap` | 1044 | 0.0000 | 0 | 0 | 0 |
| `trump_major_person_political_statements` | `broad_political_statement` | `hold_until_confirmed` | 668 | 0.0000 | 0 | 0 | 0 |
| `war_geopolitical_conflict_events` | `geopolitical_sanctions_or_conflict_risk` | `risk_off_candidate` | 216 | -1.0000 | 0 | 216 | 0 |
| `trump_major_person_political_statements` | `low_materiality_statement` | `hold_until_confirmed` | 203 | 0.0000 | 0 | 0 | 0 |
| `war_geopolitical_conflict_events` | `geopolitical_background` | `hold_until_confirmed` | 68 | 0.0000 | 0 | 0 | 0 |
| `institution_investment_actions` | `ownership_or_insider_filing_only` | `source_gap` | 58 | 0.0000 | 0 | 0 | 0 |
| `trump_major_person_political_statements` | `macro_policy_background` | `hold_until_confirmed` | 35 | 0.0000 | 0 | 0 | 0 |
| `trump_major_person_political_statements` | `policy_restriction_or_tariff_risk` | `risk_off_candidate` | 26 | -1.0000 | 0 | 26 | 0 |
| `war_geopolitical_conflict_events` | `geopolitical_sanctions_or_conflict_risk` | `hold_until_confirmed` | 23 | -0.8500 | 0 | 0 | 0 |
| `trump_major_person_political_statements` | `sector_policy_catalyst_watch` | `sector_support_watch` | 7 | 1.0000 | 0 | 0 | 7 |
| `trump_major_person_political_statements` | `sector_policy_catalyst_watch` | `risk_off_candidate` | 1 | -1.0000 | 0 | 1 | 0 |

### Recent Aerospace Score Attachment

| Metric | Value |
|---|---:|
| recent aerospace trades | 29 |
| support-entry candidate count | 0 |
| risk-off candidate count | 74 |
| sector-support watch count | 0 |

### GPT Review

- Captured status: `CAPTURED_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT recommended scoring big events by direction, transmission strength, company relevance, timing validity, priced-in risk, evidence quality, and confidence while forbidding source-presence or LLM-score direct trading.

## No-Background Decision-Maker Report

- We no longer treat Trump, war, policy, CEO, or IR as yes/no signals.
- Each event gets direction, transmission strength, company relevance, evidence quality, materiality, confidence, and priced-in risk.
- Broad events can become risk-off or sector-watch, but not direct support-entry.
- Recent aerospace still has no company-direct support-entry candidate, so entry restoration remains blocked.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `scoring_schema_complete` | 1 | event_scope,event_interpretation_category,transmission_channel,directional_score,transmission_strength_score,company_relevance_score,event_timestamp_quality_score,priced_in_risk_score,evidence_quality_score,materiality_score,interpretation_confidence_score,composite_interpretation_score,score_action,scoring_reason_code,support_entry_certified_flag,risk_off_certified_flag,sector_support_watch_flag,source_presence_only_used_flag,gpt_score_used_as_source_flag | all big-event scoring fields present |
| `large_events_are_scored` | 1 | large_events=2291 nonzero_scored=273 | Trump war policy CEO events receive deterministic interpretation scores when content keywords exist |
| `broad_events_not_support_entry` | 1 | broad_support_entry_count=0 | macro or sector events cannot become direct support_entry without company-direct evidence |
| `source_presence_not_used` | 1 | source_presence_only_used=0 | event existence alone cannot drive score action |
| `recent_aerospace_company_direct_support` | 0 | support_entry_candidate_count=0 | recent aerospace needs pre-entry company-direct support before entry restoration |
| `trading_promotion` | 0 | scoring sidecar only; no assignment or order input | must pass source timing OOS cost and account gates before strategy use |

## Artifact Manifest

### Inputs

- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `event_interpretation_scores.csv`
- `recent_aerospace_event_score_attachment.csv`
- `event_score_summary.csv`
- `task_623_pass_fail_matrix.csv`
- `task_623_gpt_big_event_scoring_review_status.csv`
- `task_623_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task623_big_event_interpretation_scoring_sidecar`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`