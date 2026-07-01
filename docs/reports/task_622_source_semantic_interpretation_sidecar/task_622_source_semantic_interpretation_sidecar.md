# Task622 Source Semantic Interpretation Sidecar

## Decision Summary

- Verdict: `IMPLEMENT_SEMANTIC_SOURCE_SIDECAR_FAIL_AEROSPACE_CERTIFICATION`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- This is evaluation-only. Semantic labels are not trading score inputs.
- Recent aerospace source certification pass: 0

## Quant Expert Report

### Semantic Schema Fields

| Field | Purpose |
|---|---|
| `company_specificity` | source interpretation field |
| `catalyst_economic_link` | source interpretation field |
| `market_timing_risk` | source interpretation field |
| `actionability` | source interpretation field |
| `evidence_quality` | source interpretation field |
| `timestamp_validity` | source interpretation field |
| `economic_direction` | source interpretation field |
| `materiality_level` | source interpretation field |
| `classification_confidence` | source interpretation field |
| `review_status` | source interpretation field |
| `reason_code` | source interpretation field |
| `source_gap_flag` | source interpretation field |

### Recent Aerospace Semantic Attachment

| Metric | Value |
|---|---:|
| recent aerospace trades | 29 |
| company-direct support-entry count | 0 |
| source gap count | 11 |

### Top Source Gaps

| Lane | Category | Actionability | Reason | Events | Gap Rate |
|---|---|---|---|---:|---:|
| `institution_investment_actions` | `insider_or_sale_notice` | `hold_until_confirmed` | `ownership_or_insider_filing_not_bullish_by_default` | 9105 | 0.00% |
| `ceo_ir_transcripts_and_presentations` | `company_ir_proxy` | `uninterpretable_do_not_trade` | `generic_8k_or_ir_proxy_title_without_content` | 1044 | 100.00% |
| `trump_major_person_political_statements` | `nan` | `hold_until_confirmed` | `broad_policy_context_not_stock_entry_support` | 940 | 0.00% |
| `institution_investment_actions` | `passive_13g` | `hold_until_confirmed` | `ownership_or_insider_filing_not_bullish_by_default` | 453 | 0.00% |
| `war_geopolitical_conflict_events` | `Sanctions List Updates` | `hold_until_confirmed` | `geopolitical_context_not_company_catalyst` | 208 | 0.00% |
| `institution_investment_actions` | `activist_13d` | `hold_until_confirmed` | `ownership_or_insider_filing_not_bullish_by_default` | 92 | 0.00% |
| `institution_investment_actions` | `institutional_13f_disclosure` | `uninterpretable_do_not_trade` | `sec_event_title_lacks_interpretable_economic_content` | 58 | 100.00% |
| `war_geopolitical_conflict_events` | `General Licenses` | `hold_until_confirmed` | `geopolitical_context_not_company_catalyst` | 41 | 0.00% |
| `war_geopolitical_conflict_events` | `Regulations and Guidance` | `hold_until_confirmed` | `geopolitical_context_not_company_catalyst` | 22 | 0.00% |
| `war_geopolitical_conflict_events` | `Enforcement Actions` | `hold_until_confirmed` | `geopolitical_context_not_company_catalyst` | 20 | 0.00% |
| `war_geopolitical_conflict_events` | `Miscellaneous` | `hold_until_confirmed` | `geopolitical_context_not_company_catalyst` | 16 | 0.00% |

### GPT Review

- Captured status: `CAPTURED_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT agreed binary source presence is insufficient and recommended evidence quality, timestamp validity, economic direction, materiality, confidence, and review status fields.

## No-Background Decision-Maker Report

- Source is no longer yes/no.
- Generic 8-K, Form 4, broad policy, and source density cannot support entry.
- If the content cannot be interpreted, it becomes source gap and cannot trade.
- Aerospace/space entry remains blocked until full source text proves a real company-specific catalyst.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `schema_fields_complete` | 1 | company_specificity,catalyst_economic_link,market_timing_risk,actionability,evidence_quality,timestamp_validity,economic_direction,materiality_level,classification_confidence,review_status,reason_code,source_gap_flag | all semantic schema fields present |
| `generic_filings_not_support_entry` | 1 | generic_support_count=0 | generic 8-K/Form4/title-only filings cannot be support_entry |
| `broad_policy_not_direct_stock_support` | 1 | broad_support_count=0 | broad policy/geopolitical events cannot be direct stock entry support |
| `recent_aerospace_source_certification` | 0 | company_direct_support_entry_count=0 | recent aerospace needs company-direct interpretable support before entry can be restored |
| `trading_promotion` | 0 | semantic sidecar only; not score input | semantic labels must pass OOS/cost/source gates before assignment use |

## Artifact Manifest

### Inputs

- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `source_semantic_labels.csv`
- `recent_aerospace_semantic_attachment.csv`
- `source_gap_report.csv`
- `task_622_pass_fail_matrix.csv`
- `task_622_gpt_semantic_schema_review_status.csv`
- `task_622_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task622_source_semantic_interpretation_sidecar`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`