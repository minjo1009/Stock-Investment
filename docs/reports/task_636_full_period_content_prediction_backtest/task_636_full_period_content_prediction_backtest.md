# Task636 Full Period Content Prediction Backtest

## Decision Summary

- Verdict: `FAIL_CONTENT_PREDICTION_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Entries: 5265
- Linked events: 3319
- Source text certified events: 3319
- Entries with certified content prediction: 1856
- Stable predictive content features: 0

## Quant Expert Report

This task reads linked source text and converts it into stock-specific content prediction fields. Presence fields are not used for assignment.

### Coverage

| Entries | Linked Entries | Unique Events | Source Text | Content Events | Entries With Content |
|---:|---:|---:|---:|---:|---:|
| 5265 | 2445 | 3319 | 3319 | 200 | 1856 |

### Predictive Feature Audit

| Feature | Stable Pass | Validation Lift | Recent Lift | Validation ER Delta | Recent ER Delta |
|---|---:|---:|---:|---:|---:|
| `content_contract_revenue_flag` | 0 | 4.66 | nan | 0.53 | nan |
| `content_guidance_margin_flag` | 0 | -7.92 | nan | 22.66 | nan |
| `content_insider_buy_flag` | 0 | 4.54 | -7.52 | -6.51 | 17.65 |
| `content_insider_sell_flag` | 0 | -19.86 | -29.90 | 33.21 | 55.07 |
| `content_low_priced_in_positive_flag` | 0 | -8.24 | -3.21 | 7.11 | 5.31 |
| `content_negative_score_flag` | 0 | 2.75 | -1.37 | -5.83 | -3.19 |
| `content_positive_score_flag` | 0 | 0.34 | 0.91 | 2.91 | 0.74 |
| `content_strong_positive_score_flag` | 0 | -35.07 | -2.18 | 66.14 | 9.17 |
| `content_supply_demand_flag` | 0 | nan | nan | nan | nan |

## No-Background Decision-Maker Report

- This task uses source text content, not information existence.
- It extracts direct bullish or bearish meaning and tests whether that meaning predicts returns.
- Trading remains forbidden until the content feature survives validation, recent OOS, and account comparison.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `full_period_linkage_built` | 1 | entries=5265; end=2026-06-03 | full refreshed period through June 2026 |
| `source_text_coverage` | 1 | source_text=3319/3319 | all linked events should have source text for full-quality interpretation |
| `content_prediction_coverage` | 1 | entries_with_prediction=1856 | at least 100 entries need certified content predictions before backtest use |
| `content_predictive_stability` | 0 | stable_predictive_features=0 | at least one content-derived feature must work in validation and recent OOS |
| `presence_fields_not_used` | 1 | presence fields not used | information presence fields remain forbidden |
| `trading_promotion` | 0 | content prediction research only | requires stable predictive content feature and account/QQQ rerun |

## Artifact Manifest

- `task_636_entry_event_links.csv`
- `task_636_linked_source_text_certification.csv`
- `task_636_event_content_predictions.csv`
- `task_636_entry_content_prediction_panel.csv`
- `task_636_content_predictive_feature_audit.csv`
- `task_636_source_and_prediction_coverage_audit.csv`
- `task_636_decision.csv`
- `artifact_manifest.csv`