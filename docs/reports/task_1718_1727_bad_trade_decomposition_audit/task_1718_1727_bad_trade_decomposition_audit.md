# Task1718-1727 Bad-Trade Decomposition Audit

## Decision Summary

- Verdict: `bad_trade_decomposition_completed_diagnostic_only`.
- Main conclusion: the loop is not caused primarily by the 32 new open-slot candidates.
- Main failure: baseline-preserved cluster risk and late/weak reduce behavior.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Baseline comparison:

| Policy | Final | Base Final | Delta Final | CAGR | MDD | Base MDD | Delta MDD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bad_trade_gate_top3_v1` | 3525.2985 | 2740.1193 | 785.1792 | 0.276522 | -0.32335 | -0.2539 | -0.06945 |
| `bad_trade_gate_top5_v1` | 2638.334 | 2054.2962 | 584.0378 | 0.206812 | -0.286708 | -0.236762 | -0.049946 |

Selection reason decomposition:

| Policy | Selection | Trades | PnL | Avg Net | Win Rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `bad_trade_gate_top3_v1` | `baseline_preserved` | 153 | 2503.3228 | 0.028132 | 0.594771 |
| `bad_trade_gate_top3_v1` | `high_confidence_open_slot_filled_by_payoff_rank` | 7 | 21.9762 | 0.009911 | 0.571429 |
| `bad_trade_gate_top5_v1` | `baseline_preserved` | 192 | 1584.9733 | 0.027044 | 0.598958 |
| `bad_trade_gate_top5_v1` | `high_confidence_open_slot_filled_by_payoff_rank` | 25 | 53.3604 | 0.023223 | 0.56 |

Action decomposition:

| Policy | Action | Trades | PnL | Avg Net | Win Rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `bad_trade_gate_top3_v1` | `exit` | 29 | 685.5885 | 0.040352 | 0.586207 |
| `bad_trade_gate_top3_v1` | `hold` | 90 | 2618.9855 | 0.049681 | 0.7 |
| `bad_trade_gate_top3_v1` | `reduce` | 41 | -779.275 | -0.030926 | 0.365854 |
| `bad_trade_gate_top5_v1` | `exit` | 33 | 347.9481 | 0.033842 | 0.606061 |
| `bad_trade_gate_top5_v1` | `hold` | 137 | 1822.004 | 0.046205 | 0.671533 |
| `bad_trade_gate_top5_v1` | `reduce` | 47 | -531.6184 | -0.035616 | 0.361702 |

Worst periods:

| Policy | Date | Period PnL | Period Return | Drawdown | Worst Symbol | Worst Symbol PnL |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| `bad_trade_gate_top3_v1` | 2022-05-31T21:00:00+00:00 | -192.4431 | -0.129049 | -0.23919 | CC | -116.1798 |
| `bad_trade_gate_top3_v1` | 2022-08-31T21:00:00+00:00 | -156.413 | -0.119259 | -0.32335 | CC | -95.9444 |
| `bad_trade_gate_top3_v1` | 2025-01-31T21:00:00+00:00 | -257.3025 | -0.113377 | -0.181702 | AMBA | -145.3749 |
| `bad_trade_gate_top3_v1` | 2022-11-30T21:00:00+00:00 | -122.4261 | -0.084726 | -0.225288 | CCRN | -102.4629 |
| `bad_trade_gate_top3_v1` | 2021-08-31T21:00:00+00:00 | -115.1497 | -0.081668 | -0.081668 | AOS | -71.7583 |
| `bad_trade_gate_top3_v1` | 2022-03-31T21:00:00+00:00 | -133.082 | -0.080156 | -0.105395 | AMP | -65.3566 |
| `bad_trade_gate_top3_v1` | 2022-07-31T21:00:00+00:00 | -95.9362 | -0.068162 | -0.231727 | ADI | -80.6062 |
| `bad_trade_gate_top3_v1` | 2026-02-28T21:00:00+00:00 | -244.1411 | -0.064769 | -0.064769 | BDX | -138.3514 |
| `bad_trade_gate_top3_v1` | 2021-05-31T21:00:00+00:00 | -83.0658 | -0.064066 | -0.064066 | CE | -44.0496 |
| `bad_trade_gate_top3_v1` | 2024-11-30T21:00:00+00:00 | -120.1588 | -0.048866 | -0.048866 | CDNA | -120.1588 |

Root causes:

- `primary_root`: The open-slot additions are not the main MDD source. Evidence: Open-slot additions were 32 trades and positive in aggregate, while worst drawdown months were dominated by baseline-preserved rows.
- `primary_root`: MDD comes from baseline-preserved 2022 and 2025 drawdown clusters. Evidence: The worst period was 2022-08-31 for both top3 and top5; key symbols include CC, AA, AVGO, ADM, BMRN, AMBA, AMZN.
- `l5_root`: Reduce did not mean loss control succeeded. Evidence: Reduce actions have negative aggregate PnL because they often fired after damage or left enough exposure to suffer.
- `l2_l4_root`: Ordinary_pass is too broad. Evidence: Worst losing baseline rows were often ordinary_pass and top3_payoff_candidate, so current L2/L4 does not detect cyclical beta/valuation air-pocket risk.
- `process_root`: The loop is caused by mixing candidate expansion and risk control in one replay. Evidence: Open-slot fill raises return and exposure, while L5 risk rules try to reduce drawdown after the fact.

## No-Background Decision-Maker Report

1. 새 후보가 주범이 아닙니다.
2. 2022년 기존 보존 종목 묶음이 MDD를 만들었습니다.
3. reduce는 많이 했지만 손실 방어에는 부족했습니다.
4. `ordinary_pass`가 너무 넓어서 경기민감/고베타 급락을 못 잡았습니다.
5. 다음은 룰 추가가 아니라 cluster exposure control입니다.

## Artifact Manifest

- `task1719_selection_reason_summary.csv`
- `task1720_action_summary.csv`
- `task1721_open_slot_trade_audit.csv`
- `task1722_worst_trade_audit.csv`
- `task1723_worst_period_audit.csv`
- `task1724_baseline_comparison.csv`
- `task1725_root_cause_chain.csv`
- `task1727_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1718_1727_bad_trade_decomposition_audit.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```