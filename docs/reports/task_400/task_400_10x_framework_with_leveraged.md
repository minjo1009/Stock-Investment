# Task T400 - 10x Objective Strategy Framework

## Strategy Definition
- Track A: Convex Growth (trend+momentum+vol guard)
- Track B: Mean Reversion on residual idle cash

## Backtest Results
### Dual-Track 10x Framework
- Initial Capital: $100,000.00
- Final Capital (5Y): $113,272.58
- Total Return: +13.27%
- CAGR: +2.52%
- MDD: -73.44%
- Worst Year: -26.73%
- Time Under Water: 72 months

## Validation Checklist
- no_same_bar_fill: PASS
- no_capital_overlap: PASS
- no_negative_cash: PASS
- no_lookahead: PASS
- regime_past_only: PASS
- equity_continuity: PASS

## Sensitivity
- perturbation: MA window 200 -> 220
- total_return_change_pct: -5.687561
- overfit_risk: LOW

## Final Judgment: INVALID
