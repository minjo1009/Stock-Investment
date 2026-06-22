# Task2191-2200 API Drawdown Sizing Guard

## Decision Summary

- Verdict: `api_drawdown_sizing_guard_complete_diagnostic_only`.
- Best policy: `api_dd_guard_winner_preserve_top2_v1`.
- Final equity: 8011.1549.
- CAGR: 0.496601.
- MDD: -0.280843.
- Delta vs API baseline final: -457.5318.
- Delta vs API baseline MDD: 0.058965.
- Joint target met: 1.
- Guarded trade rows: 165.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

The guard uses only prior portfolio drawdown and previous-period PnL state at each decision. It caps API boost during stress and preserves high winner-defense trades. The intent is to reduce drawdown without killing CIEN/AVGO/AEIS-style winner sizing.

Replay results:

- `api_dd_guard_soft_boost_cap_top2_v1`: final 8079.7165, CAGR 0.499074, MDD -0.327669, delta final -388.9702, delta MDD 0.012139.
- `api_dd_guard_stress_neutral_top2_v1`: final 8060.7699, CAGR 0.498392, MDD -0.316043, delta final -407.9168, delta MDD 0.023765.
- `api_dd_guard_winner_preserve_top2_v1`: final 8011.1549, CAGR 0.496601, MDD -0.280843, delta final -457.5318, delta MDD 0.058965.

Guard action summary:

- `api_dd_guard_soft_boost_cap_top2_v1` / no_guard_normal_state: rows 61, multiplier delta 0.0, pnl 6762.6376.
- `api_dd_guard_soft_boost_cap_top2_v1` / risk_state_tighter_cap: rows 5, multiplier delta 0.0, pnl -390.2431.
- `api_dd_guard_soft_boost_cap_top2_v1` / soft_boost_cap: rows 46, multiplier delta -0.338, pnl 300.4613.
- `api_dd_guard_soft_boost_cap_top2_v1` / winner_preserved_partial_boost: rows 4, multiplier delta -0.056, pnl 406.8604.
- `api_dd_guard_stress_neutral_top2_v1` / no_guard_normal_state: rows 61, multiplier delta 0.0, pnl 6760.3622.
- `api_dd_guard_stress_neutral_top2_v1` / risk_state_tighter_cap: rows 5, multiplier delta -0.1, pnl -389.8768.
- `api_dd_guard_stress_neutral_top2_v1` / stress_neutralizes_api_boost: rows 46, multiplier delta -0.52, pnl 283.159.
- `api_dd_guard_stress_neutral_top2_v1` / winner_preserved_partial_boost: rows 4, multiplier delta -0.056, pnl 407.1255.
- `api_dd_guard_winner_preserve_top2_v1` / no_guard_normal_state: rows 61, multiplier delta 0.0, pnl 6737.309.
- `api_dd_guard_winner_preserve_top2_v1` / nonwinner_stress_cap: rows 46, multiplier delta -6.92, pnl 246.6243.
- `api_dd_guard_winner_preserve_top2_v1` / risk_state_tighter_cap: rows 5, multiplier delta 0.0, pnl -383.997.
- `api_dd_guard_winner_preserve_top2_v1` / winner_preserved_full_boost: rows 4, multiplier delta 0.0, pnl 411.2189.

## No-Background Decision-Maker Report

Conclusion first: this is a drawdown-state sizing guard, not a new selector. It tries to stop API boost from making bad market windows worse while leaving strong winner trades alone.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2191_2200_api_drawdown_sizing_guard/`.
- Validator: `python scripts/trader_brain_2191_2200_api_drawdown_sizing_guard_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
