# Task1971-1980 Free Source L0-L5 Replay

## Decision Summary

- Verdict: `free_source_l0_l5_replay_complete_diagnostic_only`.
- Policy: `free_source_l0_l5_top3_v1`.
- Final equity: 4024.7118.
- CAGR: 0.309717.
- MDD: -0.240402.
- Delta vs Task1951-1960 source-receipt replay: 59.506.
- Delta vs sleeve baseline: 80.1661.
- ALFRED/FRED vintage is active only as small adjustment for downloaded FRED series.
- SEC issuer guidance is support-only and does not certify analyst surprise.
- Yahoo price data is cross-check-only, not original as-of market receipt.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Data flow:

- L0 verifies free-source availability by exact task scope symbol, SEC packet, and macro decision state.
- L1 builds certified FRED vintage macro by decision timestamp.
- L2 maps SEC guidance, macro, and Yahoo price cross-check into semantic primitives.
- L3 creates relation edges from those primitives.
- L4 applies small pre-registered source adjustments.
- L5 replays the frozen top3 path using prior controlled trade returns.

| Policy | Final | CAGR | MDD | Trades | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: |
| `free_source_l0_l5_top3_v1` | 4024.7118 | 0.309717 | -0.240402 | 160 | 1 |

Split/OOS metrics:

| Window | Final | Return | MDD |
| --- | ---: | ---: | ---: |
| IS_2021_2023 | 2005.642 | 1.005642 | -0.240402 |
| OOS_2024_2026Q1 | 4024.7118 | 3.024712 | -0.168198 |

Attribution audit:

| Source Family | Trades | Adjusted | PnL Audit |
| --- | ---: | ---: | ---: |
| `macro` | 124 | 124 | 3433.8956 |
| `issuer_guidance` | 160 | 160 | 3024.7117 |
| `price_crosscheck` | 151 | 0 | 2804.5193 |

Remaining blockers:

- Analyst PIT consensus revision remains unavailable.
- Yahoo price remains cross-check only.
- Non-FRED/vendor rows in the prior free-source ledger are not macro vintage certified.
- This diagnostic replay does not change acceptance.

## No-Background Decision-Maker Report

1. The new free sources were connected into L0-L5.
2. The replay was run on the frozen top3 path.
3. The result must be read as diagnostic only.
4. The key question is whether the extra source logic improved judgment or added noise.

## Artifact Manifest

- `task1971_input_manifest.csv`
- `task1971_l0_free_source_admission.csv`
- `task1972_l1_alfred_macro_vintage_panel.csv`
- `task1973_l2_free_source_semantics.csv`
- `task1974_l3_free_source_relation_edges.csv`
- `task1975_l4_free_source_thesis_cards.csv`
- `task1976_free_source_top3_replay_trades/equity/metrics/split/cost`
- `task1977_free_source_attribution.csv`
- `task1978_expert_subagent_audit.csv`
- `task1980_acceptance_gate.csv`
- `task1980_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
