# ASTS / SNOW 실패 리뷰

## ASTS

### [supplied_project_fact]

ASTS는 내부 모델상:

```text
source_packet_direct_economic_supported
company_direct_event_count = 4
direct_economic_signature =
contract/customer/order_backlog/revenue/guidance

quality_risk_bucket =
cleaner_company_multi_signal
```

으로 분류됨.

하지만 결과:

```text
costed_return = -13.78%
QQQ 대비 -3.99%
```

---

### [externally_sourced_fact]

제공된 원문 이벤트를 보면 핵심은:

* 2025-01-27 ASTS 8-K
* "private offering"
* "Indenture and Notes"

즉 실제 텍스트에는 자금조달/채권성 구조가 포함됨.

패킷 자체에도 남아 있음.

```text
Item 1.01 Entry into a Material Definitive Agreement.
Indenture and Notes.
Completed its previously announced private offering...
```

(출처: ASTS 8-K, 2025-01-27, SEC filing)

---

### [trader_inference]

전문 트레이더 관점에서는:

```text
contract/customer/backlog
```

만 본 것이 문제.

동시에 존재한:

```text
financing
offering
capital structure event
```

를 충분히 감점하지 못했을 가능성이 높음.

즉 모델은:

```text
customer + backlog + guidance
```

를 긍정 신호로 읽었지만,

시장은:

```text
financing overhang
capital raise implications
```

를 같이 평가했을 수 있음.

---

### [trader_inference]

또 하나:

현재 ASTS 패킷은

```text
theme_breadth_not_broad
required_confirmation = source_packet_confirmation
```

이 명시되어 있음.

즉 내부 진단도:

```text
확인 필요
```

라고 보고 있었음.

그런데 source-direct bucket에서는 사실상:

```text
positive packet
```

으로 해석.

여기서

```text
경제 신호 강도
≠
가격 흡수 상태
```

를 분리하지 못함.

---

### [source_gap]

현재 없음:

```text
offering 규모
자금조달 희석 영향
시장 기대 대비 규모
```

---

# SNOW

### [supplied_project_fact]

SNOW는:

```text
company_revenue_guidance
revenue/guidance
```

로 분류.

그러나 동시에:

```text
all_event_count 26~27
direct_event_count 1
noise_ratio 0.96
```

즉:

```text
26~27개 이벤트 중
실질 direct signal 1개
```

뿐.

---

### [supplied_project_fact]

같은 기간 이벤트 대부분:

```text
FORM 4
144
13G
```

등.

패킷에도:

```text
ownership_or_sale_filing_noise
```

로 기록.

---

### [externally_sourced_fact]

직접 economic source는:

```text
SNOW 8-K
2025-10-27
```

내용:

```text
reaffirms revenue guidance
```

(출처: SNOW 8-K, 2025-10-27 SEC filing)

---

### [trader_inference]

전문 트레이더는:

```text
guidance 존재
```

보다

```text
guidance surprise
guidance change
guidance quality
```

를 봄.

현재 원문은:

```text
guidance raise
```

가 아니라

```text
guidance reaffirmation
```

에 가까움.

즉:

```text
새로운 정보 강도
```

가 약함.

---

### [trader_inference]

또한 패킷 스스로:

```text
dominant_interpretation_gap =
priced_in_analysis_proxy_only
```

라고 기록.

이건 사실상:

```text
우리는 guidance가 긍정인지 알지만
얼마나 가격에 반영됐는지는 모른다
```

는 뜻.

---

### [trader_inference]

SNOW 실패를 설명하는 가장 강한 내부 단서는:

```text
high_noise_thin_signal
noise_ratio 0.96
```

임.

즉:

```text
강한 direct economic signal
```

이 아니라

```text
매우 얇은 direct signal 하나
+
대량의 filing noise
```

구조.

---

### [source_gap]

현재 없음:

```text
guidance가 컨센서스 대비 상향인지
단순 유지인지

시장 기대 대비 surprise 크기

valuation/crowding 상태
```

---

# ASTS vs SNOW 공통 문제

### [trader_inference]

두 종목 모두

```text
direct signal 존재
```

는 맞음.

하지만 모델은 아직:

```text
경제 신호 존재
```

와

```text
시장에 새로운 정보인가
```

를 구분 못 함.

---

ASTS

```text
economic positive
+
financing overhang 가능성
```

---

SNOW

```text
guidance signal
+
reaffirmation 가능성
+
noise ratio 96%
```

---

즉:

```text
signal quality
```

는 봤지만

```text
information novelty
expectation gap
price absorption
```

을 못 봄.

---

# Feature 수정 제안

## 1. Economic Signal ≠ Information Novelty

### 추가 분리

현재:

```text
contract/customer/backlog/revenue/guidance
```

↓

```text
new_information
reaffirmation_only
financing_event
ownership_filing
```

---

## 2. Financing Overhang Axis

현재 ASTS 같은 경우:

```text
contract positive
```

와

```text
offering / financing
```

가 같이 존재.

---

추가:

```text
financing_structure_present
capital_raise_related
convertible_or_note_related
```

---

## 3. Guidance Quality Axis

현재:

```text
guidance
```

한 버킷.

---

분리:

```text
guidance_raise
guidance_reaffirm
guidance_soft
```

---

## 4. Noise Dominance Axis

현재 이미 noise_ratio 있음.

---

하지만:

```text
high_noise_thin_signal
```

을 더 강하게 분리.

---

예:

```text
single_direct_signal
multi_direct_signal
direct_signal_dominated
noise_dominated
```

---

# 최종 결론

### ASTS

```text
positive source-direct 해석 자체는 틀렸다고 보기 어렵다.

하지만 financing / offering 성격과
가격 흡수 확인이 부족했다.
```

---

### SNOW

```text
guidance 신호는 있었지만

새로운 정보인지
단순 재확인인지
기대 대비 강한지

구분하지 못했다.

그리고 noise ratio 96%는 매우 경고 신호였다.
```

---

### 가장 중요한 수정

현재:

```text
direct economic signal 존재
→ 긍정
```

---

다음:

```text
economic signal

+
information novelty

+
financing overhang

+
guidance quality

+
noise dominance

+
price absorption state
```

를 분리해야 함.

현재 패킷은 "좋은 뉴스가 있었는가"는 보지만,

```text
시장이 왜 굳이 지금 다시 사야 하는가
```

는 아직 설명하지 못합니다.
