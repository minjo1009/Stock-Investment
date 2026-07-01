# Task T410 - Always-In Leveraged Strategy

## Strategy Definition
- Always invested baseline, high-vol universe, weekly rebalance
- Top-ranked asset gets >=60%, second <=40% when qualified
- Drawdown >=50% triggers 50% deployment mode

## Backtest Results
- Initial Capital: $100,000.00
- Final Capital (5Y): $113,012.00
- Total Return: +13.01%
- CAGR: +2.48%
- MDD: -80.52%
- Worst Year: -74.91%
- Time Under Water: 77 months

## Validation
- no_same_bar_fill: PASS
- no_capital_overlap: PASS
- no_lookahead: PASS
- no_negative_cash: PASS
- leveraged_consistent: PASS

## Final Judgment: FAIL
