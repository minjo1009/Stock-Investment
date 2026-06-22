# Task1896-1900 Watch Subtype Calibration

## Decision Summary

- Verdict: `watch_subtype_calibration_complete_no_replay`.
- Watch rows classified: 113.
- Upgrade/full-hold candidate rows: 36.
- Damage watch rows: 56.
- No replay was executed in this task.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

What changed:

- `watch` is now split into damage, normal winner volatility, information gap, overhang, and upgrade candidate states.
- Subtype assignment uses as-of quality, payoff, volatility cause, expectation, absorption, financing specificity, and breadth fields.
- PnL deltas are attached only for audit and are forbidden from assignment.
- Hold calibration was preregistered but not replayed.

| Watch subtype | Rows | Desk PnL | Baseline PnL | Delta vs Baseline | Delta vs Source | Restore Candidates | Damage Count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `normal_winner_volatility_watch` | 31 | 1138.8918 | 1576.8889 | -437.9971 | 42.0823 | 0 | 0 |
| `damage_watch` | 56 | 365.7132 | 603.4995 | -237.7863 | -130.1337 | 0 | 56 |
| `information_gap_watch` | 8 | 218.3744 | 289.2029 | -70.8285 | 3.609 | 0 | 0 |
| `upgrade_candidate_watch` | 5 | 160.4687 | 219.984 | -59.5153 | 22.1133 | 5 | 0 |
| `overhang_watch` | 13 | 196.2278 | 232.6604 | -36.4326 | 4.2572 | 0 | 0 |

Policy-level watch subtype split:

| Policy | Subtype | Rows | Delta vs Baseline |
| --- | --- | ---: | ---: |
| `desk_specific_top3_v1` | `damage_watch` | 26 | -146.605 |
| `desk_specific_top3_v1` | `information_gap_watch` | 4 | -50.5823 |
| `desk_specific_top3_v1` | `normal_winner_volatility_watch` | 14 | -314.1547 |
| `desk_specific_top3_v1` | `overhang_watch` | 3 | -32.8963 |
| `desk_specific_top3_v1` | `upgrade_candidate_watch` | 2 | -45.7371 |
| `desk_specific_top5_v1` | `damage_watch` | 30 | -91.1813 |
| `desk_specific_top5_v1` | `information_gap_watch` | 4 | -20.2462 |
| `desk_specific_top5_v1` | `normal_winner_volatility_watch` | 17 | -123.8424 |
| `desk_specific_top5_v1` | `overhang_watch` | 10 | -3.5363 |
| `desk_specific_top5_v1` | `upgrade_candidate_watch` | 3 | -13.7782 |

Specific audits:

- Live dilution precision rows: 54, audit delta vs baseline: -265.7233.
- Speculative no-entry rows: 12, audit delta vs baseline: 36.9355.

Interpretation:

- If watch is `damage_watch`, the brain should stay defensive.
- If watch is `normal_winner_volatility_watch` or `upgrade_candidate_watch`, the next frozen replay can test restoring full hold.
- If watch is `information_gap_watch`, the answer is source fill, not bearish scoring.
- If watch is `overhang_watch`, the answer is cap/precision review, not automatic exit.

Leakage audit:

- No price matching was introduced.
- No replay was executed.
- Outcome deltas are audit-only.

## No-Background Decision-Maker Report

1. Watch is no longer one bucket.
2. Some watch rows are real danger.
3. Some watch rows are winners that should probably be held harder.
4. Some watch rows are just missing information.
5. Next replay should only test the preregistered restore/full-hold candidates.

## Artifact Manifest

- `task1896_input_manifest.csv`
- `task1896_watch_subtype_panel.csv`
- `task1897_watch_subtype_attribution.csv`
- `task1898_live_dilution_precision_panel.csv`
- `task1899_speculative_block_payoff_audit.csv`
- `task1900_hold_calibration_contract.csv`
- `task1900_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1896_1900_watch_subtype_calibration_validate.py`
- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```