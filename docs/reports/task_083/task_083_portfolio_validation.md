# Task 083 - Portfolio Mode Validation & Attribution

## Summary Table
| Mode | Trades | PF | NetPnL | MDD | Sharpe | WinRate | FillRate | CapUtil | AvgConcPos | ExpVar | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A_BASELINE_SINGLE | 192 | 1.093835 | 4588.7267 | 9874.4637 | 0.400162 | 32.29% | 61.54% | 0.099401 | 3.479167 | 0.000010 | PASS |
| B_PORTFOLIO_TOP3 | 45 | 0.836908 | -534.1260 | 1398.1179 | -0.443110 | 33.33% | 60.81% | 0.010689 | 1.100000 | 0.000000 | FAIL |
| C_PORTFOLIO_TOP5 | 79 | 1.153786 | 617.0912 | 1044.8080 | 0.423393 | 34.18% | 57.66% | 0.003817 | 1.803797 | 0.000000 | PASS |
| D_PORTFOLIO_SECTOR_FILTER | 39 | 1.698872 | 2466.2808 | 1071.4429 | 1.140162 | 38.46% | 50.65% | 0.010882 | 1.243590 | 0.000000 | PASS |

## Baseline vs Portfolio Comparison
- B_PORTFOLIO_TOP3: PF -0.256927, NetPnL -5122.8527, MDD -8476.3458, Sharpe -0.843272
- C_PORTFOLIO_TOP5: PF +0.059951, NetPnL -3971.6355, MDD -8829.6557, Sharpe +0.023231
- D_PORTFOLIO_SECTOR_FILTER: PF +0.605037, NetPnL -2122.4459, MDD -8803.0207, Sharpe +0.740000

## Symbol Contribution (Top/Worst)
### A_BASELINE_SINGLE
- Top:
  - META: net_pnl=7768.9771, trades=19
  - NVDA: net_pnl=7337.2093, trades=15
  - AAPL: net_pnl=3296.8577, trades=15
  - MSFT: net_pnl=910.0398, trades=15
  - QCOM: net_pnl=-0.8899, trades=9
- Worst:
  - NFLX: net_pnl=-5199.0870, trades=20
  - AVGO: net_pnl=-2753.1523, trades=19
  - TSLA: net_pnl=-2460.7740, trades=14
  - AMZN: net_pnl=-1628.6060, trades=21
  - GOOGL: net_pnl=-1556.8916, trades=14
### B_PORTFOLIO_TOP3
- Top:
  - MSFT: net_pnl=272.3534, trades=15
  - AMD: net_pnl=-254.4249, trades=9
  - AMZN: net_pnl=-552.0545, trades=21
- Worst:
  - AMZN: net_pnl=-552.0545, trades=21
  - AMD: net_pnl=-254.4249, trades=9
  - MSFT: net_pnl=272.3534, trades=15
### C_PORTFOLIO_TOP5
- Top:
  - NVDA: net_pnl=1448.4862, trades=15
  - MSFT: net_pnl=167.4860, trades=15
  - AMD: net_pnl=-130.8970, trades=9
  - AMZN: net_pnl=-332.0254, trades=21
  - AVGO: net_pnl=-535.9586, trades=19
- Worst:
  - AVGO: net_pnl=-535.9586, trades=19
  - AMZN: net_pnl=-332.0254, trades=21
  - AMD: net_pnl=-130.8970, trades=9
  - MSFT: net_pnl=167.4860, trades=15
  - NVDA: net_pnl=1448.4862, trades=15
### D_PORTFOLIO_SECTOR_FILTER
- Top:
  - NVDA: net_pnl=2448.3523, trades=15
  - MSFT: net_pnl=272.3534, trades=15
  - AMD: net_pnl=-254.4249, trades=9
- Worst:
  - AMD: net_pnl=-254.4249, trades=9
  - MSFT: net_pnl=272.3534, trades=15
  - NVDA: net_pnl=2448.3523, trades=15

## Sector Contribution
### A_BASELINE_SINGLE
- XLK: net_pnl=8060.1315, trades=82
- XLC: net_pnl=1012.9984, trades=53
- XLP: net_pnl=-395.0232, trades=22
- XLY: net_pnl=-4089.3800, trades=35
### B_PORTFOLIO_TOP3
- XLK: net_pnl=17.9285, trades=24
- XLY: net_pnl=-552.0545, trades=21
### C_PORTFOLIO_TOP5
- XLK: net_pnl=949.1166, trades=58
- XLY: net_pnl=-332.0254, trades=21
### D_PORTFOLIO_SECTOR_FILTER
- XLK: net_pnl=2466.2808, trades=39

## Drawdown Attribution
### A_BASELINE_SINGLE
- max_drawdown: 9826.3832
- worst_period: {'start': '2024-06-21T00:00:00+00:00', 'end': '2025-06-09T00:00:00+00:00'}
- top_symbol_losses: [{'symbol': 'AMZN', 'net_pnl': -1824.4764936929255}, {'symbol': 'NFLX', 'net_pnl': -1307.0474055013058}, {'symbol': 'AMD', 'net_pnl': -1236.1403756263703}, {'symbol': 'GOOGL', 'net_pnl': -1227.5212195259087}, {'symbol': 'COST', 'net_pnl': -1133.2092394465608}]
- exit_type_breakdown: [{'exit_type': 'STOP', 'trades': 39, 'net_pnl': -13050.755478906014}, {'exit_type': 'TREND', 'trades': 3, 'net_pnl': 513.0804695402196}, {'exit_type': 'TIME', 'trades': 2, 'net_pnl': 3438.1739735835304}]
### B_PORTFOLIO_TOP3
- max_drawdown: 1398.1179
- worst_period: {'start': '2023-06-13T00:00:00+00:00', 'end': '2025-02-07T00:00:00+00:00'}
- top_symbol_losses: [{'symbol': 'AMD', 'net_pnl': -700.814956696822}, {'symbol': 'AMZN', 'net_pnl': -274.7646238877298}, {'symbol': 'MSFT', 'net_pnl': 53.746285525257754}]
- exit_type_breakdown: [{'exit_type': 'STOP', 'trades': 20, 'net_pnl': -1980.1887972658444}, {'exit_type': 'TREND', 'trades': 3, 'net_pnl': -0.44011783748519306}, {'exit_type': 'TIME', 'trades': 3, 'net_pnl': 1058.7956200440356}]
### C_PORTFOLIO_TOP5
- max_drawdown: 1093.6352
- worst_period: {'start': '2022-04-05T00:00:00+00:00', 'end': '2023-02-10T00:00:00+00:00'}
- top_symbol_losses: [{'symbol': 'NVDA', 'net_pnl': -556.9265466023722}, {'symbol': 'AVGO', 'net_pnl': -236.81528560687286}, {'symbol': 'AMZN', 'net_pnl': -203.70695076135544}, {'symbol': 'MSFT', 'net_pnl': -89.35890561248763}]
- exit_type_breakdown: [{'exit_type': 'STOP', 'trades': 13, 'net_pnl': -1086.807688583088}]
### D_PORTFOLIO_SECTOR_FILTER
- max_drawdown: 739.3181
- worst_period: {'start': '2022-04-06T00:00:00+00:00', 'end': '2022-12-20T00:00:00+00:00'}
- top_symbol_losses: [{'symbol': 'NVDA', 'net_pnl': -928.5631487135777}, {'symbol': 'MSFT', 'net_pnl': -142.87979576091737}]
- exit_type_breakdown: [{'exit_type': 'STOP', 'trades': 5, 'net_pnl': -1071.442944474495}]

## Capital Utilization
- A_BASELINE_SINGLE: utilization=0.099401, avg_concurrent=3.479167
- B_PORTFOLIO_TOP3: utilization=0.010689, avg_concurrent=1.100000
- C_PORTFOLIO_TOP5: utilization=0.003817, avg_concurrent=1.803797
- D_PORTFOLIO_SECTOR_FILTER: utilization=0.010882, avg_concurrent=1.243590

## Failure Analysis
- B_PORTFOLIO_TOP3: PF declined vs baseline; ranking/diversification may be diluting edge.
- B_PORTFOLIO_TOP3: NetPnL declined; capital spread likely reduced high-conviction exposure.
- B_PORTFOLIO_TOP3: Sharpe declined; risk-adjusted return is weaker than baseline.
- C_PORTFOLIO_TOP5: NetPnL declined; capital spread likely reduced high-conviction exposure.
- D_PORTFOLIO_SECTOR_FILTER: NetPnL declined; capital spread likely reduced high-conviction exposure.

## Final Decision
- overall: PASS
- critical answer: YES
