1. 가장 큰 Firm-Grade Gap
[interpretation] Entry Quality가 아직 너무 거침

현재 gap matrix 1순위가 이미 말해준다.

모든 accepted trade
=
intraday_breakout_acceptance

뿐이다.

VWAP, opening range, relative strength, volume confirmation이 아직 lock되지 않았다.

현재 DD를 만드는 큰 손실은

opening_drive
large_loss 9
loss_trade 14

에서 많이 발생한다.

즉,

signal quality

보다

entry execution quality

가 더 큰 공백이다. 

붙여넣은 텍스트 (2)

[interpretation] Risk Normalization 부재

현재

equal max5

는 모든 종목을 동일 위험으로 취급한다.

하지만 accepted trade 기준

large loss count = 13

이 존재한다. 

붙여넣은 텍스트 (2)

Firm-grade에서는

signal
+
risk budget

가 분리되어야 한다.

[source_gap] Microstructure가 0%

현재

microstructure available rate = 0.00%

이다. 

붙여넣은 텍스트 (2)

실제 continuation과 fragile breakout을 구분하는 execution-time 정보가 전혀 없다.

이건 live/paper-shadow 이전 단계에서 매우 큰 공백이다.

[interpretation] Capital Efficiency 문제

현재

1621 source trades
54 accepted
1567 capacity skip
median hold 85.4 days

이다. 

붙여넣은 텍스트 (2)

즉 전략 성과의 상당 부분이

selection

뿐 아니라

capital lock-up

에 의존하고 있을 가능성이 있다.

2. 지금 우리가 속고 있을 가능성
[interpretation] MDB 제외

가장 위험한 후보.

현재는

MDB 제거
→ 성과 상승

만 확인됨.

하지만

왜 MDB가 제거됐어야 하는가

가 없다.

따라서 아직은

causal rule

이 아니라

backtest patch

에 가깝다.

[interpretation] Contract Tier 과신

accepted 기준에서

contract_only
avg 46.05%
n=7

이다. 

붙여넣은 텍스트 (2)

좋아 보인다.

하지만 표본이 매우 얇다.

지금 바로

contract_only 최상위 tier

로 승격하면 위험하다.

[interpretation] Full-period 결과 과신

현재

$7639.62

가 눈에 띈다.

하지만 firm-grade는

validation
+
recent OOS

를 우선 본다.

3. 다음 실험 순서
[interpretation] Task641A — Entry Confirmation Gate

가장 먼저.

이유:

현재 손실 cluster가

opening_drive

에 집중. 

붙여넣은 텍스트 (2)

따라서

same signal
+
better entry

를 먼저 검증해야 한다.

[interpretation] Task641B — Risk-Normalized Sizing

두 번째.

현재

equal max5

가 DD를 증폭할 수 있다.

ATR/volatility bucket sizing은

return 유지
+
DD 감소

가능성이 있는 가장 경제적으로 타당한 실험이다.

[interpretation] Task641C — Signal Tier Sizing

세 번째.

현재

OR rule

이

both
contract_only
supply_only

를 같은 비중으로 다룬다. 

붙여넣은 텍스트 (2)

Tier를 구분하는 건 경제적 해석이 가능하다.

[interpretation] Task641D — Exit / Capital Recycling

A~C 이후.

현재 median hold 85.4일. 

붙여넣은 텍스트 (2)

exit 변경은 효과가 클 수 있지만 과적합 위험도 크다.

먼저 entry quality를 해결해야 한다.

4. 각 실험을 기각해야 하는 증거
[interpretation] Entry Confirmation Gate 기각

다음 중 하나면 reject.

validation 개선 없음

recent OOS 개선 없음

accepted trade 급감만 발생
[interpretation] Risk-Normalized Sizing 기각
DD 감소

하지만 return 급락

이면 reject.

[interpretation] Signal Tier 기각
tier 효과가
validation/recent OOS에서 재현 안 됨

이면 reject.

[interpretation] Exit 실험 기각
capital turnover 증가

하지만 OOS edge 감소

이면 reject.

5. Return ↑ + DD ↓ 를 만드는 방향
[interpretation]

현재 데이터가 말하는 방향은

더 좋은 종목 찾기

가 아니다.

이미 accepted trade 평균은 높다.

문제는

몇 개의 큰 손실

이다.

[interpretation]

따라서 우선순위는

1.
Entry confirmation

2.
Risk-normalized sizing

3.
Signal-tier sizing

4.
Capital recycling

이다.

[interpretation]

반대로 하지 말아야 할 것:

MDB blacklist

theme blacklist

drawdown label 기반 제거

after-the-fact loser 제거
최종 PM 판정
[promotion_blocker]

현재 가장 중요한 미해결 항목은:

entry_quality_confirmation_missing

risk_normalized_sizing_missing

microstructure_source_gap

이다. 

붙여넣은 텍스트 (2)

[promotion_blocker]

Task641은

새 alpha 탐색

이 아니라

기존 alpha를
더 좋은 진입과 더 좋은 위험배분으로
정제하는 단계

가 되어야 한다.