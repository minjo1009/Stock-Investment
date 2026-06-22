# Task2921-2940 L2/L3 MDD Attribution Pack

## Decision Summary

- Verdict: `l2_l3_mdd_attribution_pack_completed_diagnostic_only`.
- MDD trade count: 14.
- L2 match count: 14.
- L3 edge count: 28.
- Negative trade count: 11.
- Source-integrated top2 negative trade count: 10.
- Current L2/L3 blind spot count: 10.
- Replay performed: `0`.
- Selector tuning performed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Join keys: `trade_spec_id`, `symbol`, `decision_asof_ts`.

Worst L2/L3 loss groups:

- `debt_survival_financing_cluster` / `liquidity_rates_neutral_watch` / `no_material_interaction`: 3 trades, KIS PnL -417.691005, read `mixed_or_unboosted_loss_group`.
- `clean_or_low_financing_pressure` / `liquidity_rates_neutral_watch` / `no_material_interaction`: 5 trades, KIS PnL -183.612804, read `mixed_or_unboosted_loss_group`.
- `moderate_recent_financing_dilution_watch` / `liquidity_rates_neutral_watch` / `no_material_interaction`: 1 trades, KIS PnL -31.387631, read `mixed_or_unboosted_loss_group`.
- `high_recent_financing_dilution_pressure` / `liquidity_rates_neutral_watch` / `no_material_interaction`: 5 trades, KIS PnL 1.584649, read `mixed_or_unboosted_loss_group`.

Avoidability audit:

- `CC` 2022-05-31T21:00:00+00:00: -278.567104 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.
- `AVGO` 2022-03-31T21:00:00+00:00: -92.445057 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.
- `CBT` 2022-02-28T21:00:00+00:00: -88.49845 -> `not_flagged_by_current_l2_l3`. No current L2/L3 pre-trade warning was strong enough to exclude it.
- `AME` 2022-04-30T21:00:00+00:00: -71.609492 -> `not_flagged_by_current_l2_l3`. No current L2/L3 pre-trade warning was strong enough to exclude it.
- `ALSN` 2022-07-31T21:00:00+00:00: -69.29542 -> `not_flagged_by_current_l2_l3`. No current L2/L3 pre-trade warning was strong enough to exclude it.
- `ADM` 2022-08-31T21:00:00+00:00: -58.66196 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.
- `AVGO` 2022-07-31T21:00:00+00:00: -46.678844 -> `potentially_avoidable_sec_financing_signal`. SEC financing/dilution pressure existed before selection.
- `CB` 2022-03-31T21:00:00+00:00: -39.17191 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.
- `BMRN` 2022-08-31T21:00:00+00:00: -31.387631 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.
- `AFG` 2022-06-30T21:00:00+00:00: -26.073354 -> `l2_l3_signal_seen_but_not_invalidated`. SEC financing/dilution pressure existed, but L2/L3 still let the loss trade survive top2.

This is an attribution pack only. It does not change selector, sizing, exit, paper order, live order, or assignment logic.

## No-Background Decision-Maker Report

Conclusion first: L2/L3 data exists for the MDD-window trades, but some losers still look acceptable under the current source-integrated selector.

The main issue is not missing rows. The issue is judgment quality: clean SEC state plus benign liquidity state can still hide bad trades.

Next step: build L4 thesis invalidation from these specific blind spots. Do not optimize from outcomes directly.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2921_2940_l2_l3_mdd_attribution_pack/`.
- Validator: `python scripts/trader_brain_2921_2940_l2_l3_mdd_attribution_pack_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
