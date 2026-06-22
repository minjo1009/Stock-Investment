# Task 318 - TBL_A10_LIFECYCLE v3 FAIL 원인 분해 리포트

## 0) 범위/가정/성공기준
- 범위: 기존 `TBL_A10_LIFECYCLE` 로직과 파라미터(브레이크아웃 10, ATR stop 2, partial 2R, trailing 3ATR)를 그대로 사용해 실패 원인을 계층별 수량화한다.
- 금지 준수: grid search/튜닝/기존 결과 덮어쓰기 없음. `task_314~317` 파일 수정 없음.
- 데이터 기준: `docs/reports/task_314/task_314_tbl_backtest_result.json`의 핵심 KPI(CAGR 0.622687%, Sharpe 0.123813, Expectancy R 0.097692)와 동일한 트레이드 수(82)를 재현한 진단 실행 결과를 사용.
- 산출 기준: 진단용 카운터 결과는 `docs/reports/task_318/task_318_tbl_failure_attribution_metrics.json`에 저장.

## 1) Candidate Funnel

### 1-1. 절대 수치
- 전체 symbol-date 수: 13,812
- A_10 breakout 후보 수: 1,465
- quality filter 통과 수: 107
- risk filter 통과 수: 99
- execution fill 성공 수: 82
- 최종 trade 수: 82

### 1-2. 단계별 탈락률
- Symbol-date -> Breakout: 탈락 12,347 (89.39%), 통과율 10.61%
- Breakout -> Quality: 탈락 1,358 (92.70%), 통과율 7.30%
- Quality -> Risk: 탈락 8 (7.48%), 통과율 92.52%
- Risk -> Fill: 탈락 17 (17.17%), 통과율 82.83%
- Fill -> Final Trade: 탈락 0 (0.00%), 통과율 100.00%

해석:
- 병목은 **quality filter 단계(92.70% 탈락)**와 **체결 단계(17.17% 탈락)**에 집중되어 있다.
- risk cap 자체에서의 탈락은 상대적으로 작다(quality 통과 대비 7.48%).

## 2) Lifecycle Funnel
- initial entry 수: 82
- +1R 도달 수: 39 (47.56% of entries)
- add 실행 수: 36 (43.90% of entries, +1R 도달 대비 92.31%)
- +2R 도달 수: 22 (26.83% of entries)
- partial take profit 수: 21 (25.61% of entries, +2R 도달 대비 95.45%)
- runner 전환 수: 21
- trailing stop exit 수: 12
- time exit 수: 16
- initial stop exit 수: 51

해석:
- 엔트리 후 **초기 스톱 계열 종료(51/82, 62.20%)**가 과반이다.
- runner는 일부 작동(21건 전환, 12건 trailing 종료)하지만, runner에 도달하기 전 소실이 크다.

## 3) R Distribution
- trade별 realized_R_total 평균: 0.097692
- 중앙값: -1.021809
- 상위 10% 경계값: 2.812214
- 하위 10% 경계값: -1.056536
- avg_win_r: 2.119978
- avg_loss_r: -1.008842
- win/loss ratio: 2.101398
- top 5 winners contribution: +20.872556R
- bottom 5 losers contribution: -5.549188R

해석:
- 평균 expectancy는 소폭 양수지만, **중앙값이 -1R 근처**라서 전형적 트레이드는 손실 쪽에 몰려 있다.
- 성과가 소수의 큰 승자(top winners)에 의존한다.

## 4) Exposure Analysis
- 평균 보유 포지션 수: 1.2659
- 평균 현금 비중: 87.80%
- market exposure %: 12.20%
- `max_positions=5` 대비 실제 평균 사용률: 25.32%
- 자본 유휴 여부: **높음 (대부분 기간 현금 대기)**

해석:
- 포지션 슬롯 및 자본이 크게 남아 있었고, 실제 익스포저가 낮아 복리 성장이 제한되었다.

## 5) Execution Analysis
- 후보 대비 미체결률: 15.46% (15/97)
- limit miss 비율: 15.46% (동일)
- slippage/fee 총 차감액: 3,632.9051 (slippage 2,421.9390 + fee 1,210.9661)
- same-bar stop 발생 횟수: 4
- partial fill 발생 횟수: 0

해석:
- 체결 보수성으로 일정 비율의 기회가 소실되며(15.46%), 비용 누적도 절대 수익을 추가로 압박한다.

## 6) Yearly Breakdown
| Year | Return % | Sharpe | MDD % | Trade Count | Expectancy R |
|---|---:|---:|---:|---:|---:|
| 2021 | 3.4862 | 0.8858 | 3.4532 | 19 | 0.1071 |
| 2022 | -4.3239 | -0.8304 | 5.1653 | 9 | 0.1310 |
| 2023 | 2.3830 | 0.3403 | 6.6471 | 21 | -0.2470 |
| 2024 | 1.6835 | 0.2791 | 4.6628 | 19 | 0.7456 |
| 2025 | 0.8034 | 0.1690 | 5.2108 | 9 | -0.3033 |
| 2026 | -0.6438 | -0.5066 | 2.1419 | 5 | -0.2906 |

해석:
- 연도별로 샤프/기대값 변동이 커서 안정적 edge가 약하다.
- 거래 수가 연도별로 5~21건으로 낮아 표본 변동성이 크다.

## 7) Final Diagnosis (주된 실패 원인 판정)

### 7-1. 판정
1. **Exposure 부족 (주원인)**
- 평균 포지션 1.27/5, 평균 현금 87.8%, 시장 노출 12.2%로 자본 사용이 매우 낮다.
- 전략의 양(+) expectancy가 매우 작아(0.0977R) 저노출 환경에서 CAGR로 전환되기 어렵다.

2. **Quality filter 과도 (공동 주원인)**
- Breakout 이후 92.70%가 quality 단계에서 탈락.
- 기회 밀도가 낮아지고 결과적으로 익스포저 부족을 강화한다.

3. **체결 모델 보수성 (보조 원인)**
- risk 통과 건 중 17.17%가 미체결(주로 limit miss).
- slippage+fee 3,632.9 누적으로 성과를 추가 훼손.

### 7-2. 비주된 항목
- Entry edge 없음: 완전 부재로 단정하기 어려움(평균 expectancy는 양수).
- Runner가 작동하지 않음: 일부 작동(21건 runner 전환, trailing exit 12건).
- Risk cap 과도: 직접 탈락 비중은 낮음(quality 통과 대비 7.48%).
- Universe 부적합: 본 리포트 데이터만으로 1차 원인으로 확정 어려움.
- 일봉 전략 한계: 구조적 한계는 존재 가능하나, 이번 FAIL의 1차 설명력은 노출/후보밀도/체결에서 더 큼.

## 부록) 재현 파일
- 진단 메트릭 JSON: `docs/reports/task_318/task_318_tbl_failure_attribution_metrics.json`
