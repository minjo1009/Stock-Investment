# Task2581-2600 Source Integrated Selector Diagnostic

## Decision Summary

- Verdict: `source_integrated_selector_only_diagnostic_complete_no_replay`.
- Candidate rows: 3100.
- L2 bridge rows: 3100.
- L3 edge rows: 7241.
- Selector-only rows: 2480.
- Source gaps: 1.
- Base top2 avg audit return: 0.03009.
- Source-integrated top2 avg audit return: 0.027411.
- Capital replay run: `0`.
- Selector deployment changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task joins the two newly acquired source families into L2/L3 selector diagnostics:

- `sec_financing_dilution`: strict 3094/3100, gaps 6.
- `liquidity_rates_regime`: strict 3100/3100, gaps 0.

Interpretation:

- SEC financing/dilution is used mainly as dilution/survival risk, not as a standalone positive signal.
- Liquidity/rates regime is a market-context modifier. Treasury average interest rates remain proxy-only.
- SEC x liquidity/rates interaction penalizes financing pressure more heavily in tight liquidity or credit stress regimes.
- Existing repaired exit-chain returns are used only for ex-post selector diagnostics, never assignment.
- No capital path, replay engine, sizing, adapter, paper trading, or live order logic is touched.

Selector-only audit:

- `base_top10_selector_only_v1`: rows 620, avg audit return 0.013156, severe losses 9.
- `base_top2_selector_only_v1`: rows 124, avg audit return 0.03009, severe losses 2.
- `base_top3_selector_only_v1`: rows 186, avg audit return 0.023794, severe losses 2.
- `base_top5_selector_only_v1`: rows 310, avg audit return 0.01484, severe losses 5.
- `source_integrated_top10_selector_only_v1`: rows 620, avg audit return 0.014801, severe losses 9.
- `source_integrated_top2_selector_only_v1`: rows 124, avg audit return 0.027411, severe losses 2.
- `source_integrated_top3_selector_only_v1`: rows 186, avg audit return 0.023551, severe losses 2.
- `source_integrated_top5_selector_only_v1`: rows 310, avg audit return 0.014385, severe losses 6.

Validation summary:

- `full_candidate_l2_rows`: 3100/3100 pass `1`.
- `decision_regime_rows`: 62/62 pass `1`.
- `join_gap_rows`: 6/6 pass `1`.
- `capital_replay_run`: 0/0 pass `1`.

## No-Background Decision-Maker Report

Conclusion first: the new sources are now inside the brain's selector diagnostic layer.

This does not mean the strategy is accepted. It means we can now see how SEC dilution risk and rates/liquidity regime would change top candidates before running a controlled replay.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/`.
- Report: `docs/reports/task_2581_2600_source_integrated_selector_diagnostic/task_2581_2600_source_integrated_selector_diagnostic.md`.
- Validator: `python scripts/trader_brain_2581_2600_source_integrated_selector_diagnostic_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
