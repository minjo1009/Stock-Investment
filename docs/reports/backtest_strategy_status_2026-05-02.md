# 백테스트 전략 현황 정리 (2026-05-02)

## 1) 진행했던 전략 목록 (전략명 + 소속 리포트)

### A. 단일 전략 (D_PORTFOLIO_SECTOR_FILTER 계열)
- `D_PORTFOLIO_SECTOR_FILTER` (전략 잠금/정의): `docs/reports/task_084/task_084_strategy_lock.json`
- `D_PORTFOLIO_SECTOR_FILTER` (자본 백테스트): `docs/reports/task_093/task_093_capital_backtest.json`

### B. 민감도 전략군 (Breakout 파라미터 변형)
- `BASELINE`, `A_10`, `A_15`, `A_30`, `B_0.25_pct`, `B_0.50_pct`, `C_HIGH_TOUCH`, `D_OFF`, `D_LIGHT`, `E_OFF`, `E_LIGHT`
- 소속 리포트: `docs/reports/task_099/task_099_breakout_sensitivity_results.json`

### C. 멀티전략
- `Cross-sectional Momentum`, `Short-term Mean Reversion`, `Regime Switch`
- 소속 리포트:
  - `docs/reports/task_300/task_300_multi_strategy.json`
  - `docs/reports/task_300/task_300_multi_strategy_with_leveraged.json`

## 2) 전략별 핵심 3지표 비교 (`return%`, `Sharpe`, `MDD`)

지표 표준화 규칙:
- `return%` := `return_pct` 또는 `total_return_pct`
- `Sharpe` := `sharpe`
- `MDD` := `mdd_pct` 또는 `max_drawdown_pct`

### A. 단일 전략 (task_093, 시나리오 A_BASE_10K_LOW_COST)

| Strategy | Report | return% | Sharpe | MDD |
|---|---|---:|---:|---:|
| D_PORTFOLIO_SECTOR_FILTER | task_093 (A_BASE_10K_LOW_COST) | 18.987329 | 0.292990 | 32.474546 |

### B. 민감도 전략군 (task_099 runs)

| Strategy | Report | return% | Sharpe | MDD |
|---|---|---:|---:|---:|
| BASELINE | task_099 | 31.990129 | 0.884498 | 3.831247 |
| A_10 | task_099 | 51.545713 | 1.198470 | 3.537458 |
| A_15 | task_099 | 30.025281 | 0.812353 | 4.976832 |
| A_30 | task_099 | 33.420985 | 0.929958 | 3.378261 |
| B_0.25_pct | task_099 | 31.318606 | 0.901740 | 2.570752 |
| B_0.50_pct | task_099 | 16.590174 | 0.585285 | 5.904568 |
| C_HIGH_TOUCH | task_099 | 37.190619 | 0.872125 | 5.802779 |
| D_OFF | task_099 | 34.996347 | 0.882139 | 5.362977 |
| D_LIGHT | task_099 | 34.996347 | 0.882139 | 5.362977 |
| E_OFF | task_099 | 31.990129 | 0.884498 | 3.831247 |
| E_LIGHT | task_099 | 31.990129 | 0.884498 | 3.831247 |

### C. 멀티전략 (task_300)

#### task_300_multi_strategy
| Strategy | Report | return% | Sharpe | MDD |
|---|---|---:|---:|---:|
| Cross-sectional Momentum | task_300_multi_strategy | 8.766981 | 1.151087 | 98.898941 |
| Short-term Mean Reversion | task_300_multi_strategy | 25.872250 | 0.786072 | 74.375363 |
| Regime Switch | task_300_multi_strategy | 81.294787 | 1.508999 | 96.158898 |

#### task_300_multi_strategy_with_leveraged
| Strategy | Report | return% | Sharpe | MDD |
|---|---|---:|---:|---:|
| Cross-sectional Momentum | task_300_multi_strategy_with_leveraged | -1.552494 | 0.988335 | 99.360604 |
| Short-term Mean Reversion | task_300_multi_strategy_with_leveraged | 24.004989 | 0.745714 | 68.941214 |
| Regime Switch | task_300_multi_strategy_with_leveraged | 55.123060 | 1.618707 | 95.958372 |

## 3) 현재 가장 최신으로 저장된 전략

판정 규칙: 대상 리포트 JSON의 `LastWriteTime` 기준.

| File | LastWriteTime |
|---|---|
| `docs/reports/task_084/task_084_strategy_lock.json` | 2026-04-24 21:49:44 |
| `docs/reports/task_093/task_093_capital_backtest.json` | 2026-04-25 10:09:37 |
| `docs/reports/task_099/task_099_breakout_sensitivity_results.json` | 2026-04-25 16:11:23 |
| `docs/reports/task_300/task_300_multi_strategy.json` | 2026-04-29 23:00:47 |
| `docs/reports/task_300/task_300_multi_strategy_with_leveraged.json` | 2026-04-29 23:28:08 |

최신 저장 전략 결과 파일:
- `docs/reports/task_300/task_300_multi_strategy_with_leveraged.json` (2026-04-29 23:28:08)

## 4) 검증 결과 (Test Plan 실행)

- 전략 누락 검증: PASS
  - 단일 전략 1개 계열, 민감도 runs 11개, 멀티전략 3개(2개 리포트 변형) 반영 완료.
- 지표 정합성 검증: PASS
  - 비교표의 모든 행에 `return%`, `Sharpe`, `MDD` 값 존재.
- 최신성 검증: PASS
  - 대상 5개 JSON의 수정시각 정렬 결과와 최신 판정 결과 일치.
