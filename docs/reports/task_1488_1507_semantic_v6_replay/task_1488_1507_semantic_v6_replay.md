# Task1488-1507 Semantic V6 Replay

## Decision Summary

- Verdict: `semantic_v6_judgment_structure_implemented_not_accepted`.
- Best policy: `semantic_v6_top5_v1`.
- Best final equity: 1975.4892.
- Best CAGR: 0.141016.
- Best MDD: -0.42143.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L2/L3 now classify event family before materiality, separate good words from surprise, and separate initial price reaction from sustained market absorption.
- Objective: judge whether the structure is coherent before treating replay PnL as alpha.

## Quant Expert Report

- `materiality` no longer gives a standalone bonus.
- `positive / survival / financing / dilution / mixed / unknown` is decided first.
- `good_words_only` is not `true_surprise_proxy`.
- `initial_reaction_only` is not `sustained_market_acceptance`.
- `source_gap` remains neutral unless a source-backed survival or dilution event exists.
- Outcome returns are present only in Task1502 displacement audit.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `semantic_v6_top10_v1` | 1231.8647 | 0.041233 | -0.322527 | 620 | 138 | 29 | 0 | 0 | 0 |
| `semantic_v6_top3_v1` | 1723.1987 | 0.111204 | -0.420186 | 186 | 52 | 7 | 0 | 0 | 0 |
| `semantic_v6_top5_v1` | 1975.4892 | 0.141016 | -0.42143 | 310 | 80 | 10 | 1 | 0 | 0 |

Top3 semantic family mix:

- `mixed`: 106
- `positive`: 79
- `unknown`: 1


## No-Background Decision-Maker Report

이번엔 점수 튜닝이 아니라 판단 구조를 고쳤다.

큰 이벤트를 바로 좋은 이벤트로 보지 않는다.

먼저 좋은 일인지, 생존 문제인지, 자금조달인지, 희석인지 나눈다.

좋은 말과 진짜 surprise도 분리했다.

잠깐 오른 것과 시장이 계속 받아준 것도 분리했다.

그래도 전략은 아직 승인 아니다.

## Artifact Manifest

- `task1488_expert_review_loop.csv`
- `task1489_v6_preregistered_spec.csv`
- `task1490_source_evidence_audit.csv`
- `task1491_l2_semantic_v6_panel.csv`
- `task1492_l3_mechanism_v3_edges.csv`
- `task1493_l4_thesis_cards_v6.csv`
- `task1494_payoff_ranker_v6.csv`
- `task1495_policy_specs.csv`
- `task1496_source_receipt_exit_panel.csv`
- `task1496_price_path_exit_panel.csv`
- `task1496_hold_receipt_panel.csv`
- `task1497_replay_trades.csv`
- `task1497_replay_equity.csv`
- `task1497_replay_metrics.csv`
- `task1502_displacement_audit.csv`
- `task1503_summary.csv`
- `task1506_acceptance_gate.csv`
- `task1507_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1488_1507_semantic_v6_replay_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
