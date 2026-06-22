# Task 084 - Portfolio Strategy Lock & Paper Pilot Readiness

## 1. Strategy Summary
- strategy_id: D_PORTFOLIO_SECTOR_FILTER
- execution: LIMITED_CHASE
- risk: TIME_STOP_ONLY
- max_positions: 3
- sector_filter: XLK, XLY

## 2. Cost Sensitivity Table (S1~S6)
| Scenario | PF | NetPnL | MDD | Sharpe | Trades | FillRate |
|---|---:|---:|---:|---:|---:|---:|
| S1_ZERO_COST | 2.069946 | 3317.1539 | 973.6122 | 1.522885 | 39 | 50.65% |
| S2_LOW_COST | 1.957125 | 3077.5339 | 1000.5818 | 1.415991 | 39 | 50.65% |
| S3_MEDIUM_COST | 1.898196 | 2948.4508 | 1016.3214 | 1.357292 | 39 | 50.65% |
| S4_KIS_REALISTIC | 1.698872 | 2466.2808 | 1071.4429 | 1.140162 | 39 | 50.65% |
| S5_KIS_STRESS_20 | 1.615622 | 2246.5858 | 1093.8913 | 1.042152 | 39 | 50.65% |
| S6_KIS_STRESS_30 | 1.537177 | 2026.4947 | 1116.3398 | 0.943269 | 39 | 50.65% |

## 3. Stability Analysis
- pf_decay_s1_to_s6: 0.532769
- s4_pf_ge_1_2: True
- s5_pf_ge_1_0: True
- s4_sharpe_ge_1_0: True
- pf_collapses_hard: False

## 4. Drawdown Attribution
- period: {'start': '2022-04-06T00:00:00+00:00', 'end': '2022-12-20T00:00:00+00:00'}
- drawdown: 739.3181
- top_symbol_losses: [{'symbol': 'NVDA', 'net_pnl': -928.5631487135777}, {'symbol': 'MSFT', 'net_pnl': -142.87979576091737}]
- top_sector_losses: [{'sector': 'XLK', 'net_pnl': -1071.442944474495}]
- exit_type_breakdown: [{'exit_type': 'STOP', 'net_pnl': -1071.442944474495, 'trades': 5}]

## 5. Concentration Risk
- top3_symbol_share_abs: 0.312377
- top_sector_share_abs: 0.25895
- symbol_risk: False
- sector_risk: False

## 6. Trade Quality
- fill_rate: 50.649351
- missed_trade_ratio: 44.155844
- big_miss_ratio_of_missed: 94.117647
- avg_slippage: 0.262808
- missed_trades: 34
- big_miss_count: 32

## 7. Failure Mode
- code: B
- label: strategy weakness
- reasons: ['Primary weakness appears in baseline edge retention under costs.']

## 8. Pilot Conditions
- enabled: True
- max_positions: 3
- max_notional_per_trade: 0.3
- daily_loss_limit_pct: 0.75
- kill_switch: ['UNKNOWN order detected', 'reconciliation critical mismatch', 'consecutive cancel loop UNKNOWN']
- stop_trading_conditions: ['realized day loss exceeds daily limit', 'rolling PF below 1.0 for 20 trades', 'MDD exceeds 43.443672% of S4 net reference']

## 9. Final Decision
- gate_status: PASS
- decision: PASS -> 즉시 Paper Pilot 가능
- answer_q1_real_money: YES
- answer_q2_long_term: YES
