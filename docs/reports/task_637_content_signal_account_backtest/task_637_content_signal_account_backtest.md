# Task637 Content Signal Account Backtest

## Decision Summary

- Verdict: `PASS_CONTENT_SIGNAL_CANDIDATE_NEEDS_LIVE_RULE_LOCK`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Best 50bp content strategy: `content_negative_score` max5 = $5148.31

## Quant Expert Report

Content-derived signals were tested as trade-selection universes with $1000 initial capital, capacity caps, and 0/50/100bp round-trip cost stress.

### Source Audit

- Entries: 5265
- Entry period: 2024-01-02 to 2026-06-03
- Entries with content prediction: 2406

### 50bp Account Results

| Universe | Max Positions | Final $ | Beats QQQ | Beats Task617 Max5 |
|---|---:|---:|---:|---:|
| `content_any_stable_feature` | 5 | $5006.02 | 1 | 1 |
| `content_guidance_margin` | 5 | $2919.12 | 1 | 0 |
| `content_guidance_supply_combo` | 5 | $1332.53 | 0 | 0 |
| `content_negative_score` | 5 | $5148.31 | 1 | 1 |
| `content_supply_demand` | 5 | $3707.06 | 1 | 1 |
| `content_any_stable_feature` | 10 | $4981.17 | 1 | 1 |
| `content_guidance_margin` | 10 | $2107.88 | 1 | 0 |
| `content_guidance_supply_combo` | 10 | $1697.41 | 0 | 0 |
| `content_negative_score` | 10 | $3419.36 | 1 | 1 |
| `content_supply_demand` | 10 | $2847.64 | 1 | 0 |
| `content_any_stable_feature` | 20 | $3530.42 | 1 | 1 |
| `content_guidance_margin` | 20 | $1683.03 | 0 | 0 |
| `content_guidance_supply_combo` | 20 | $1463.66 | 0 | 0 |
| `content_negative_score` | 20 | $2263.87 | 1 | 0 |
| `content_supply_demand` | 20 | $2154.18 | 1 | 0 |
| `content_any_stable_feature` | 50 | $1882.17 | 1 | 0 |
| `content_guidance_margin` | 50 | $1470.76 | 0 | 0 |
| `content_guidance_supply_combo` | 50 | $1356.92 | 0 | 0 |
| `content_negative_score` | 50 | $1418.95 | 0 | 0 |
| `content_supply_demand` | 50 | $1552.28 | 0 | 0 |

### Recent OOS Split

| Universe | Selected | Lift | ER Delta |
|---|---:|---:|---:|
| `content_negative_score` | 150 | 1.55 | -13.22 |
| `content_guidance_margin` | 285 | 1.76 | -6.20 |
| `content_supply_demand` | 303 | 2.46 | -8.87 |
| `content_any_stable_feature` | 370 | 1.56 | -6.59 |
| `content_guidance_supply_combo` | 218 | 2.99 | -9.45 |

### OOS-Only Account Results

| Split | Universe | Max Positions | Final $ | QQQ $ | Beats QQQ |
|---|---|---:|---:|---:|---:|
| `recent_oos` | `content_any_stable_feature` | 10 | $1470.57 | $1140.89 | 1 |
| `recent_oos` | `content_guidance_supply_combo` | 5 | $1439.79 | $1140.89 | 1 |
| `recent_oos` | `content_supply_demand` | 5 | $1439.79 | $1140.89 | 1 |
| `recent_oos` | `content_guidance_margin` | 10 | $1358.74 | $1140.89 | 1 |
| `recent_oos` | `content_supply_demand` | 10 | $1357.30 | $1140.89 | 1 |
| `validation` | `content_guidance_supply_combo` | 5 | $1236.73 | $1020.64 | 1 |
| `validation` | `content_supply_demand` | 20 | $1192.68 | $1020.64 | 1 |
| `validation` | `content_guidance_supply_combo` | 20 | $1178.83 | $1020.64 | 1 |
| `validation` | `content_guidance_margin` | 20 | $1165.55 | $1020.64 | 1 |
| `validation` | `content_negative_score` | 20 | $1163.48 | $1020.64 | 1 |

## No-Background Decision-Maker Report

- We did not trade on information existence.
- We used source-text interpretation fields that survived validation/recent OOS screening.
- This is still not approved for trading until exact live-readable source interpretation rules and runtime source readiness are locked.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `full_period_through_june` | 1 | entry_end=2026-06-03 | entry panel must extend into June 2026 |
| `content_signal_recent_oos_stability` | 1 | recent_oos_stable_universes=5 | at least one content strategy must have positive recent OOS lift and no worse entry-reduce |
| `best_50bp_beats_qqq` | 1 | content_negative_score max5=$5148.31; qqq=$1751.31 | best content strategy at 50bp must beat QQQ |
| `best_50bp_beats_task617_original_max5` | 1 | content_negative_score max5=$5148.31; task617_max5=$3248.89 | content strategy must beat existing Task617 max5 before promotion |
| `best_100bp_still_beats_qqq` | 1 | content_negative_score max5=$4964.79; qqq=$1751.31 | best content strategy at 100bp must still beat QQQ |
| `validation_oos_50bp_account_beats_qqq` | 1 | content_guidance_supply_combo max5=$1236.73; qqq=$1020.64 | validation-only $1000 account must beat same-period QQQ |
| `recent_oos_50bp_account_beats_qqq` | 1 | content_any_stable_feature max10=$1470.57; qqq=$1140.89 | recent OOS-only $1000 account must beat same-period QQQ |
| `presence_fields_not_used` | 1 | presence fields not used | content interpretation only |
| `trading_promotion` | 0 | research candidate only | requires exact deployment rules and live source readiness before runtime use |

## Artifact Manifest

- `task_637_content_signal_account_summary.csv`
- `task_637_content_signal_accepted_trades.csv`
- `task_637_content_signal_split_audit.csv`
- `task_637_content_signal_oos_account_summary.csv`
- `task_637_source_audit.csv`
- `task_637_pass_fail_matrix.csv`
- `task_637_decision.csv`
- `task_637_gpt_review_packet.md`
- `artifact_manifest.csv`