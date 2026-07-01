1. Entry Confirmation은 어떻게 조건부로 써야 하나?
[interpretation]

Task643가 이미 보여준 것:

모든 거래
→ confirmation 적용

은 실패.

왜냐하면 accepted trade가 54개뿐인 희소 전략에서 글로벌 필터는 winner도 같이 제거하기 때문이다.

[interpretation]

Task644에서는

signal
→ confirmation 필요 여부 결정

구조가 되어야 한다.

Candidate 구조
Tier A
높은 신뢰 신호
→ confirmation 없음

Tier B
중간 신뢰 신호
→ confirmation 필요

Tier C
경계 신호
→ confirmation 강제
[interpretation]

즉

confirmation

은

entry filter

가 아니라

conditional wrapper

가 되어야 한다.

[promotion_blocker]

다시

모든 거래
→ VWAP 확인

같은 전역 필터는 금지.

Task643에서 이미 실패했다.

2. ATR / Gap / Volatility Sizing
[interpretation]

Task643의 핵심 교훈:

고변동성
≠
나쁜 거래

이다.

[interpretation]

현재 ATR sizing 실패는

변동성 자체

를 위험으로 취급했기 때문일 가능성이 높다.

Candidate 구조

위험을

good volatility

bad volatility

로 분리.

Good Volatility
strong signal

strong theme

strong continuation

상태에서 발생.

Bad Volatility
gap 과도

weak confirmation

fragile continuation

상태에서 발생.

[interpretation]

따라서 sizing은

ATR

단독이 아니라

ATR
×
signal quality

로 가야 한다.

[promotion_blocker]

다시

ATR 높음
→ size 감소

는 금지.

Task643가 이미 부정했다.

3. Signal Tier
[interpretation]

현재 가장 위험한 실수:

contract_only
평균 좋음

을 보고

최고 tier

로 승격하는 것.

[source_gap]

현재 표본:

contract_only
n=7

수준.

[interpretation]

따라서 tier는

수익률 순위

로 만들면 안 된다.

Candidate 구조

Tier 정의는

경제적 증거 강도

기반.

예:

contract + supply

contract only

supply only

그러나

size 차이

는 매우 작게.

[interpretation]

Task644에서는

full size

normal size

slightly reduced size

정도만 허용.

[promotion_blocker]
contract_only
2배

supply_only
0.5배

같은 공격적 차등은 금지.

현재 evidence 부족.

4. Exit / Capital Recycling
[interpretation]

현재 가장 큰 사실:

median hold
85.4일

그리고

hold20

은 DD 줄였지만 수익을 크게 훼손.

[interpretation]

즉

조기 청산

은 해답이 아니다.

Candidate 구조
winner 유지

loser 억제

분리.

Exit Layer 1

기존 exit 유지.

Exit Layer 2

부분 청산.

예:

일정 수익 도달

↓

일부만 회수

↓

나머지 유지
Exit Layer 3

강한 추세만 trailing.

[interpretation]

핵심은

exit shortening

이 아니라

capital recycling

이다.

5. Task644에서 먼저 코딩할 규칙
Rule 1
[interpretation]

Conditional Confirmation

signal tier 기반

confirmation 적용.

Rule 2
[interpretation]

Signal Quality × ATR Sizing

ATR 단독 금지
Rule 3
[interpretation]

Soft Tier Sizing

tier 간 작은 차이

만 허용.

Rule 4
[interpretation]

Partial Exit

full hold

vs

partial recycle

비교.

Rule 5
[interpretation]

Capacity Recycling

accepted 54

skipped 1567

구조 개선 연구.

6. Pass / Reject Gates
Entry Confirmation
PASS
[interpretation]
validation 유지

recent 유지

full-period 개선
REJECT
[interpretation]
recent만 개선

full-period 붕괴

반복.

ATR / Vol Sizing
PASS
[interpretation]
DD 감소

return 유지
REJECT
[interpretation]
DD 감소

return 훼손
Signal Tier
PASS
[interpretation]
validation

recent OOS

동시 유지
REJECT
[interpretation]
소표본 tier

에 의존.

Exit
PASS
[interpretation]
capital turnover 증가

return 유지
REJECT
[interpretation]
winner 조기 제거
최종 PM 의견
[interpretation]

Task643는 중요한 사실 하나를 보여줬다.

좋은 wrapper는
전역 필터가 아니다.
[interpretation]

Task644의 목표는

더 강한 confirmation

이 아니라

누구에게 confirmation을 적용할지

를 결정하는 것.

[promotion_blocker]

현재 가장 유망한 방향은

conditional confirmation

signal-quality-aware sizing

partial capital recycling

이다.

반대로

global confirmation

ATR-only sizing

shorter hold

은 Task643 evidence 기준으로 우선순위가 낮다.