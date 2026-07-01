# Task625 Big Event Perfection Criteria And Source Certification

## Decision Summary

- Verdict: `LOCK_PERFECTION_CRITERIA_AND_BUILD_SOURCE_CERTIFICATION_LAYER`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Source text certified: 273 / 273
- Recent aerospace high-impact linked events: 13
- This locks the perfection standard and adds the first source-certification layer.

## Quant Expert Report

### Perfection Criteria

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `perfect_criteria_defined` | 1 | source integrity, timing integrity, semantic action integrity, OOS integrity, cost/account integrity | firm-grade perfection gates are explicit and testable |
| `nonzero_scores_have_source_urls` | 1 | nonzero_events=273 | every nonzero event score must have a source URL |
| `nonzero_scores_have_certified_source_text` | 1 | certified=273/273 | every nonzero event score must have official source text and hash |
| `linked_recent_aerospace_high_impact_certified` | 1 | certified=13/13 | all high-impact events attached to recent aerospace risk-off must be source certified |
| `broad_events_not_direct_support_entry` | 1 | broad_support_entry_count=0 | macro and sector events cannot become direct support-entry |
| `trading_promotion` | 0 | perfection criteria and source certification layer only | source-certified scoring must be rerun through OOS, cost, and account gates before trading use |

### Implementation Plan

| Priority | Work Item | Implementation | Acceptance Gate |
|---|---|---|---|
| `P0` | `official_source_text_certification` | certify every nonzero big-event score with source_url, final_url, http_status, source_text_hash, raw_text_path, and title-token evidence | `nonzero_scores_have_certified_source_text` |
| `P0` | `high_impact_linked_event_certification` | separately certify events actually linked to recent aerospace risk-off trades | `linked_recent_aerospace_high_impact_certified` |
| `P1` | `source_text_semantic_rescore` | rescore direction, transmission, directness, materiality, and evidence quality from certified text rather than title only | `same input yields deterministic score and action` |
| `P2` | `cost_account_rerun` | rerun Task624-style action validation under cost stress and same-capital account simulation | `full, validation, and recent OOS gates pass without direct support leakage` |

### Certification Sample

| Event Date | Lane | Certified | Text Chars | Title Hits | Action | Title |
|---|---|---:|---:|---:|---|---|
| 2024-09-10 | `war_geopolitical_conflict_events` | 1 | 21771 | 7 | `risk_off_candidate` | Russia-related, Iran-related, Counterterrorism, Non-Proliferation, and Counter Narcotics Designation |
| 2024-09-11 | `war_geopolitical_conflict_events` | 1 | 8964 | 19 | `risk_off_candidate` | Counterterrorism Designations; Publication of Updated Syria Shipping Advisory; Publication of Interi |
| 2024-09-12 | `war_geopolitical_conflict_events` | 1 | 8097 | 12 | `risk_off_candidate` | Global Magnitsky, Non-Proliferation, and Venezuela-related Designations; Issuance of Global Magnitsk |
| 2024-09-13 | `war_geopolitical_conflict_events` | 1 | 5691 | 15 | `risk_off_candidate` | Russia-related Designations; Issuance of Russia-related General Licenses and Amended FAQ; Publicatio |
| 2024-09-16 | `war_geopolitical_conflict_events` | 1 | 3223 | 4 | `risk_off_candidate` | Cyber-related Designations; Global Magnitsky Designations |
| 2024-09-18 | `war_geopolitical_conflict_events` | 1 | 5784 | 5 | `risk_off_candidate` | Iran-related Designations; Counter Terrorism Designation Update |
| 2024-09-19 | `war_geopolitical_conflict_events` | 1 | 9857 | 7 | `risk_off_candidate` | North Korea Designations and Designations Updates; Russia-related Designations and Designations Upda |
| 2024-09-24 | `war_geopolitical_conflict_events` | 1 | 3590 | 8 | `risk_off_candidate` | Counter Narcotics Designations; Issuance of New Russia-related Frequently Asked Questions |
| 2024-09-25 | `war_geopolitical_conflict_events` | 1 | 6652 | 5 | `risk_off_candidate` | Counter Terrorism Designations; Global Magnitsky Designations |
| 2024-09-26 | `war_geopolitical_conflict_events` | 1 | 2210 | 4 | `risk_off_candidate` | Russia-related Designations; Cyber-related Designation |
| 2024-09-27 | `war_geopolitical_conflict_events` | 1 | 3348 | 6 | `risk_off_candidate` | Iran-related Designation; Foreign Interference in U.S. Election Designations |
| 2024-09-30 | `war_geopolitical_conflict_events` | 1 | 9257 | 9 | `risk_off_candidate` | Russia-related Designation Removals; Issuance of Russia-related General License; Russia-/Ukraine-rel |
| 2024-10-01 | `war_geopolitical_conflict_events` | 1 | 9620 | 8 | `risk_off_candidate` | Cyber-related, Russia-related, and West Bank-related Designations; Counter Narcotics and Russia-rela |
| 2024-10-02 | `war_geopolitical_conflict_events` | 1 | 8256 | 4 | `risk_off_candidate` | Counter Terrorism Designations; Iran-related Designations |
| 2024-10-07 | `war_geopolitical_conflict_events` | 1 | 9107 | 14 | `risk_off_candidate` | Counter Terrorism Designations; Issuance of Counter Terrorism General Licenses; Amendment of the Rep |
| 2024-10-08 | `war_geopolitical_conflict_events` | 1 | 1362 | 2 | `risk_off_candidate` | Sudan Designation |
| 2024-10-11 | `war_geopolitical_conflict_events` | 1 | 10707 | 4 | `risk_off_candidate` | Iran-related Designations; Publication of Iran-related Determination |
| 2024-10-15 | `war_geopolitical_conflict_events` | 1 | 1972 | 3 | `risk_off_candidate` | Counter Terrorism Designations |
| 2024-10-16 | `war_geopolitical_conflict_events` | 1 | 4897 | 4 | `risk_off_candidate` | Counter Terrorism Designations; Syria Designations |
| 2024-10-17 | `war_geopolitical_conflict_events` | 1 | 10084 | 7 | `risk_off_candidate` | Russia-related Designations; Counter Terrorism Designations and Removal; Iran-related Designation Re |

### GPT Review

- Captured status: `CAPTURED_CHROME_CHATGPT_PROJECT_TAB`
- Summary: GPT judged Task623/624 incomplete because title-based semantic scores are not source-certified; perfection requires source integrity, timing integrity, action integrity, OOS robustness, and cost/account reruns.

## No-Background Decision-Maker Report

- Task623/624 were not perfect because they scored mostly from titles.
- Perfect means every nonzero score has an official source text and hash.
- We started with source certification and separately track the high-impact aerospace-linked events.
- This still does not approve trading. It prepares the next source-certified rescore.

## Artifact Manifest

### Inputs

- `docs/reports/task_623_big_event_interpretation_scoring_sidecar/event_interpretation_scores.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_625_source_certification_matrix.csv`
- `task_625_perfection_criteria_matrix.csv`
- `task_625_implementation_plan.csv`
- `task_625_gpt_perfection_review_status.csv`
- `task_625_decision.csv`
- `artifact_manifest.csv`
- raw source text files under `data/raw/task_625_big_event_source_text`

### Validation Commands

- `python -m unittest tests.test_task625_big_event_perfection_criteria_source_certification`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`