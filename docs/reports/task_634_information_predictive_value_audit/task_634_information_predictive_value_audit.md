# Task634 Information Predictive Value Audit

## Decision Summary

- Verdict: `FAIL_INFORMATION_PRESENCE_NOT_PREDICTIVE_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Stable predictive information features: 0
- Strict kept: 331 trades at 10.29% average
- Strict missed: 302 trades at 16.78% average

## Quant Expert Report

This audit tests whether the information columns predict price outcomes. The current strict strategy is not accepted because it uses presence-like information fields that do not prove stable predictive value across validation and recent OOS.

### Strict Filter Damage

| Bucket | Count | Avg Return | Sum Return | Win Rate | Entry-Reduce | Top10 Winners | Bottom10 Losers |
|---|---:|---:|---:|---:|---:|---:|---:|
| `task617_original_all` | 633 | 13.39% | 8474.20% | 63.03% | 32.23% | 1603.10% | -297.54% |
| `task632_strict_kept` | 331 | 10.29% | 3407.07% | 62.24% | 33.53% | 866.36% | -290.40% |
| `task617_missed_by_strict` | 302 | 16.78% | 5067.14% | 63.91% | 30.79% | 1571.90% | -270.26% |

### Stable Predictive Feature Test

| Feature | Stable Pass | Validation Lift | Recent Lift | Validation Entry-Reduce Delta | Recent Entry-Reduce Delta |
|---|---:|---:|---:|---:|---:|
| `p0_source_event_density_ge2_flag` | 0 | nan | nan | nan | nan |
| `source_density_high_flag` | 0 | -3.49 | -13.27 | 8.15 | 21.62 |
| `source_time_gap_high_flag` | 0 | 11.64 | 1.82 | -28.54 | 3.01 |
| `temporal_ceo_ir_proxy_pre14d_flag` | 0 | -3.65 | 1.14 | 4.27 | -14.39 |
| `temporal_geopolitical_fresh_pre72h_flag` | 0 | nan | nan | nan | nan |
| `temporal_insider_form4_or_144_pre30d_flag` | 0 | 28.70 | nan | -52.45 | nan |
| `temporal_institution_pre30d_flag` | 0 | nan | nan | nan | nan |
| `temporal_passive_13g_pre30d_flag` | 0 | -12.01 | -4.38 | 25.00 | -7.23 |
| `temporal_political_fresh_pre72h_flag` | 0 | 6.10 | -11.20 | -0.98 | 55.91 |

### Missed Winners

| Symbol | Split | Return | Lifecycle |
|---|---|---:|---|
| `RKLB` | `train_design` | 287.75% | `TASK617|RKLB|20240911T133000Z` |
| `RKLB` | `train_design` | 234.39% | `TASK617|RKLB|20240912T173000Z` |
| `RKLB` | `train_design` | 214.61% | `TASK617|RKLB|20240925T133000Z` |
| `RKLB` | `train_design` | 160.57% | `TASK617|RKLB|20241024T133000Z` |
| `RKLB` | `train_design` | 153.21% | `TASK617|RKLB|20241028T141500Z` |
| `PLTR` | `train_design` | 123.57% | `TASK617|PLTR|20240930T141500Z` |
| `PLTR` | `train_design` | 115.84% | `TASK617|PLTR|20240926T153000Z` |
| `PLTR` | `train_design` | 101.26% | `TASK617|PLTR|20240916T134500Z` |
| `PLTR` | `train_design` | 91.57% | `TASK617|PLTR|20240923T133000Z` |
| `PLTR` | `train_design` | 89.14% | `TASK617|PLTR|20241008T133000Z` |

### Retained Losers

| Symbol | Split | Return | Lifecycle |
|---|---|---:|---|
| `TEAM` | `train_design` | -31.50% | `TASK617|TEAM|20250212T153000Z` |
| `TEAM` | `train_design` | -31.39% | `TASK617|TEAM|20250218T170000Z` |
| `RKLB` | `validation` | -30.35% | `TASK617|RKLB|20251020T133000Z` |
| `RKLB` | `validation` | -30.32% | `TASK617|RKLB|20251029T134500Z` |
| `ASTS` | `recent_oos` | -28.70% | `TASK617|ASTS|20260128T144500Z` |
| `MDB` | `train_design` | -28.15% | `TASK617|MDB|20241125T153000Z` |
| `ASTS` | `validation` | -28.11% | `TASK617|ASTS|20251015T134500Z` |
| `ASTS` | `recent_oos` | -27.56% | `TASK617|ASTS|20260203T151500Z` |
| `PLTR` | `train_design` | -27.19% | `TASK617|PLTR|20250219T160000Z` |
| `CEG` | `train_design` | -27.12% | `TASK617|CEG|20250123T144500Z` |

## No-Background Decision-Maker Report

- More information did not mean better prediction.
- The strict filter threw away a better bucket and kept enough losers to underperform Task617.
- Information must be connected to a stock-specific expected price move before it can affect entries.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `information_features_have_predictive_value` | 0 | stable_predictive_features=0 | at least one information feature must improve validation and recent OOS return without worse entry-reduce |
| `strict_filter_does_not_discard_better_trades` | 0 | kept_avg=10.29%; missed_avg=16.78% | strict information filter should not discard a higher-return bucket |
| `strict_filter_reduces_entry_reduce` | 0 | kept_entry_reduce=33.53%; missed_entry_reduce=30.79% | strict information filter should lower entry-reduce failure |
| `presence_based_information_scoring` | 0 | current strict score still rewards source/event presence | replace presence scoring with relevance and predictive validation gates |

## Artifact Manifest

- `task_634_feature_predictive_value_audit.csv`
- `task_634_strict_filter_damage_audit.csv`
- `task_634_missed_winners.csv`
- `task_634_retained_losers.csv`
- `task_634_pass_fail_matrix.csv`
- `task_634_decision.csv`
- `artifact_manifest.csv`