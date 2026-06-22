# Task1951-1960 Source Receipt And Ablation

## Decision Summary

- Verdict: `source_receipt_ablation_complete_diagnostic_only`.
- Policy: `source_receipt_hardened_top3_v1`.
- Final equity: 3965.2058.
- CAGR: 0.305942.
- MDD: -0.238461.
- Delta vs Task1941-1950 hardened final equity: -10.9484.
- Macro remains shadow-only because ALFRED vintage is not certified.
- Analyst revision remains vendor-gated; issuer-public SEC text is support-only, not true consensus surprise.
- Event and breadth receipts are explicit derived as-of fields, not raw-source acceptance certification.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Data and join discipline:

- Event/breadth receipt uses exact prior Task1931-1940 rows and `decision_asof_ts` as source availability timestamp.
- Macro vintage audit reuses Task1834 source packets and keeps active macro scoring blocked.
- Issuer-public guidance probe uses exact Task1842 `trade_spec_id -> financing_source_packet_id` and exact Task1836 local SEC path.
- Analyst revision is not inferred from issuer text.
- Replay returns reuse prior controlled winner-defense trades; no new price matching or symbol/date fallback.

| Policy | Final | CAGR | MDD | Trades | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: |
| `source_receipt_hardened_top3_v1` | 3965.2058 | 0.305942 | -0.238461 | 160 | 1 |

Split/OOS metrics:

| Window | Final | Return | MDD |
| --- | ---: | ---: | ---: |
| IS_2021_2023 | 2009.4348 | 1.009435 | -0.238461 |
| OOS_2024_2026Q1 | 3965.2058 | 2.965206 | -0.168384 |

Primitive ablation audit:

| Variant | Final | Delta vs Full | MDD |
| --- | ---: | ---: | ---: |
| `ablate_price_receipt` | 3923.8509 | -41.3549 | -0.235573 |
| `ablate_breadth_receipt` | 3922.6665 | -42.5393 | -0.235573 |
| `ablate_issuer_public_guidance_support` | 3967.1068 | 1.901 | -0.238461 |
| `ablate_quality_like_high_conviction` | 3967.1068 | 1.901 | -0.238461 |
| `ablate_financing_risk_cap` | 4056.3567 | 91.1509 | -0.239827 |
| `ablate_all_receipt_adjustments` | 3967.1068 | 1.901 | -0.238461 |

Top5 receipt gate:

| Gate | Count |
| --- | ---: |
| `blocked_financing_or_bad_asof` | 50 |
| `blocked_insufficient_receipt_score` | 7 |
| `covered_by_top3_replay` | 160 |

Remaining blockers:

- Raw OHLC and breadth manifests are timestamped as derived fields here, but not recertified as raw-source acceptance artifacts.
- Full ALFRED vintage remains blocked without local vintage archive/API-backed vintage pull.
- True analyst revision and consensus surprise remain unavailable locally.
- Top5 promotion remains shadow-only and needs a separate frozen replay after the above source upgrades.

## No-Background Decision-Maker Report

1. The weak gaps were not hand-waved.
2. Macro was kept blocked.
3. Analyst surprise was kept blocked.
4. SEC issuer-public text was used only as small support.
5. Top3 still clears the diagnostic target.
6. Top5 still does not get promoted.
7. This remains diagnostic only.

## Artifact Manifest

- `task1951_source_receipt_input_manifest.csv`
- `task1952_event_breadth_source_receipt_manifest.csv`
- `task1953_macro_vintage_attempt_ledger.csv`
- `task1954_issuer_public_guidance_probe.csv`
- `task1955_expectation_source_recertification.csv`
- `task1956_primitive_ablation_replay_metrics.csv`
- `task1957_source_receipt_hardened_l4.csv`
- `task1958_source_receipt_top3_replay_trades.csv/equity/metrics/split_oos/cost_stress`
- `task1959_top5_promotion_blocker_audit.csv`
- `task1960_acceptance_gate.csv`
- `task1960_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
