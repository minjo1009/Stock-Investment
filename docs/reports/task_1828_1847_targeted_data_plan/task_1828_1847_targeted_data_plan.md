# Task1828-1847 Targeted Data Plan

## Decision Summary

- Verdict: `targeted_data_plan_ready_no_replay_executed`.
- What changed: sleeve attribution is converted into a targeted data acquisition plan.
- No replay executed.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Next action: implement rates/liquidity source contract and vintage loader plan before any new replay.

## Quant Expert Report

### Sleeve Attribution

| Policy | Sleeve | Trades | PnL Audit Only | Drawdown Audit Only | Dominant Gap |
| --- | --- | ---: | ---: | ---: | --- |
| `sleeve_split_top3_v1` | `cyclical_beta` | 42 | 135.6229 | -392.7842 | `rates_liquidity_plus_sector_breadth` |
| `sleeve_split_top3_v1` | `defensive_quality` | 14 | 146.3757 | -70.9247 | `rates_liquidity_plus_quality_stability` |
| `sleeve_split_top3_v1` | `speculative_event` | 16 | 42.757 | -180.7432 | `financing_dilution_plus_catalyst_validation` |
| `sleeve_split_top3_v1` | `winner_compounder` | 88 | 2619.7904 | -1098.2564 | `earnings_revision_plus_sector_breadth` |
| `sleeve_split_top5_v1` | `cyclical_beta` | 62 | 222.7065 | -204.1693 | `rates_liquidity_plus_sector_breadth` |
| `sleeve_split_top5_v1` | `defensive_quality` | 20 | 107.5793 | -31.9284 | `rates_liquidity_plus_quality_stability` |
| `sleeve_split_top5_v1` | `speculative_event` | 29 | 97.4613 | -76.5033 | `financing_dilution_plus_catalyst_validation` |
| `sleeve_split_top5_v1` | `winner_compounder` | 106 | 1394.6648 | -588.5916 | `earnings_revision_plus_sector_breadth` |

### Source Basis

- `rates_liquidity` / ALFRED: https://alfred.stlouisfed.org/ (official_public, impact=high)
- `rates_liquidity` / FRED DGS10: https://fred.stlouisfed.org/series/DGS10 (official_public, impact=high)
- `rates_liquidity` / FINRA Margin Statistics: https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics (official_public, impact=medium)
- `earnings_revision` / Nasdaq Data Link Zacks Analyst Revisions: https://data.nasdaq.com/databases/ZREV (vendor_or_paid, impact=high_if_available)
- `earnings_revision` / Nasdaq Data Link Zacks Earnings Trends: https://data.nasdaq.com/databases/ZET (vendor_or_paid, impact=high_if_available)
- `financing_dilution` / SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces (official_public, impact=very_high)
- `sector_breadth` / Kenneth French Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html (academic_public, impact=medium)
- `sector_breadth` / AQR Quality Minus Junk: https://www.aqr.com/Insights/Datasets/Quality-Minus-Junk-Factors-Monthly (academic_public, impact=medium)

### Priority

| Rank | Family | Why | Access |
| ---: | --- | --- | --- |
| 1 | `rates_liquidity` | largest immediate link to valuation_compression, broad_selloff, winner_macro_pressure, and sleeve budget changes | `public_first` |
| 2 | `earnings_revision` | largest expected CAGR quality impact for winner_compounder, but likely vendor-gated | `vendor_gate` |
| 3 | `financing_dilution` | highest public-source safety impact for speculative_event and issuer-specific damage | `public_first` |
| 4 | `sector_breadth` | useful for cyclical_beta and winner-volatility diagnosis, but much can be derived from existing OHLC first | `mostly_public_or_local` |

### L0-L5 Field Contract

| Family | Layer | Field | Asof Guard |
| --- | --- | --- | --- |
| `rates_liquidity` | `L0` | `rate_regime_state` | published_date <= decision_asof |
| `rates_liquidity` | `L0` | `liquidity_stress_state` | release_month <= decision_asof |
| `rates_liquidity` | `L5` | `sleeve_regime_budget_multiplier` | no PnL fields |
| `financing_dilution` | `L1` | `financing_source_packet_id` | CIK/accession exact only |
| `financing_dilution` | `L2` | `dilution_pressure_state` | acceptedDateTime <= decision_asof |
| `financing_dilution` | `L5` | `terminal_financing_override` | no missing-as-negative |
| `sector_breadth` | `L0` | `theme_breadth_state` | basket constituents predeclared |
| `sector_breadth` | `L3` | `theme_confirms_or_weakens_edge` | same-decision only |
| `earnings_revision` | `L2` | `revision_surprise_state` | vendor/public timestamp <= decision_asof |
| `earnings_revision` | `L4` | `expectation_gap_quality` | blocked if vendor history missing |

Leakage and validation discipline:

- Attribution PnL and drawdown fields remain audit-only.
- Missing source fields are source gaps, not negative labels.
- Vendor-gated earnings revision cannot be approximated as true consensus.
- Future replay is blocked until source packets have explicit published/received/as-of timestamps.

## No-Background Decision-Maker Report

1. Do not go back to micro sizing.
2. The next high-impact work is targeted data, not broad data hoarding.
3. Start with official/public rates-liquidity because it directly controls sleeve budget and MDD states.
4. Earnings revision is high-alpha but vendor-gated.
5. SEC financing/dilution comes next for speculative and terminal-risk control.
6. Sector breadth starts lightweight from existing OHLC.

## Artifact Manifest

- `task1828_sleeve_attribution_decision.csv`
- `task1829_expert_review.csv`
- `task1830_professional_source_context.csv`
- `task1831_targeted_data_priority.csv`
- `task1832_l0_l5_field_contract.csv`
- `task1833_validation_contract.csv`
- `task1834_1847_task_plan.csv`
- `task1846_acceptance_gate.csv`
- `task1847_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1828_1847_targeted_data_plan_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```