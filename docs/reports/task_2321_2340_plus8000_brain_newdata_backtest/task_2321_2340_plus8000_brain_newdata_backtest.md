# Task2321-2340 Plus8000 Brain Newdata Backtest

## Decision Summary

- Verdict: `plus8000_brain_newdata_overlay_backtest_complete_diagnostic_only`.
- Brain reference: `Task2191_api_dd_guard_winner_preserve_top2_v1`.
- Candidate decision rows: 377.
- Overlay changed rows: 186.
- Best policy: `plus8000_brain_newdata_stress_neutral_top2_v1`.
- Best final equity: 7886.7314.
- Best CAGR: 0.492068.
- Best MDD: -0.316043.
- Reference +8000 final: 8011.1549.
- Same selector stack as +8000: `1`.
- Same replay capital path as +8000: `1`.
- Strict raw/as-of complete: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task keeps the Task2191 +8000 selector/sizing/capital path and replaces only the API card/decision overlay with Task2251 full-source feature/proxy data. It does not rerun a new 3,100-candidate selector. Missing new data remains neutral, not negative.

Replay results:

- `plus8000_brain_newdata_soft_boost_cap_top2_v1`: final 7876.4302, CAGR 0.49169, MDD -0.328559, trades 116.
- `plus8000_brain_newdata_stress_neutral_top2_v1`: final 7886.7314, CAGR 0.492068, MDD -0.316043, trades 116.
- `plus8000_brain_newdata_winner_preserve_top2_v1`: final 7776.9153, CAGR 0.48802, MDD -0.280843, trades 116.

Comparison:

- `api_dd_guard_soft_boost_cap_top2_v1` (original_plus8000_brain_task2191): final 8079.7165, CAGR 0.499074, MDD -0.327669, trades 116.
- `api_dd_guard_stress_neutral_top2_v1` (original_plus8000_brain_task2191): final 8060.7699, CAGR 0.498392, MDD -0.316043, trades 116.
- `api_dd_guard_winner_preserve_top2_v1` (original_plus8000_brain_task2191): final 8011.1549, CAGR 0.496601, MDD -0.280843, trades 116.
- `plus8000_brain_newdata_soft_boost_cap_top2_v1` (plus8000_brain_newdata_overlay): final 7876.4302, CAGR 0.49169, MDD -0.328559, trades 116.
- `plus8000_brain_newdata_stress_neutral_top2_v1` (plus8000_brain_newdata_overlay): final 7886.7314, CAGR 0.492068, MDD -0.316043, trades 116.
- `plus8000_brain_newdata_winner_preserve_top2_v1` (plus8000_brain_newdata_overlay): final 7776.9153, CAGR 0.48802, MDD -0.280843, trades 116.

Overlay coverage:

- `overlay_action` / `newdata_light_support`: 96/377 (0.254642).
- `overlay_action` / `newdata_neutral`: 191/377 (0.506631).
- `overlay_action` / `newdata_supportive_boost`: 90/377 (0.238727).
- `proxy_state` / `api_proxy_mixed_or_light`: 188/377 (0.498674).
- `proxy_state` / `api_proxy_source_gap_neutral`: 3/377 (0.007958).
- `proxy_state` / `api_proxy_supportive`: 186/377 (0.493369).

## No-Background Decision-Maker Report

Conclusion first: this is the intended test shape. It uses the +8000 brain and only changes the data overlay. It is still diagnostic because strict raw/as-of complete data is not solved.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2321_2340_plus8000_brain_newdata_backtest/`.
- Validator: `python scripts/trader_brain_2321_2340_plus8000_brain_newdata_backtest_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
