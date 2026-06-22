## 결론

네, 방향은 **source-direct 단순 긍정보다 훨씬 낫습니다.**
이제 “직접 긍정 뉴스 있음”이 아니라 **그 뉴스가 신규 정보인지, 약한 재확인인지, 자금조달 부담이 있는지, 가격이 흡수했는지**를 분리합니다.

다만 아직은 **rule promotion용이 아니라 failure-filter 진단용**으로 봐야 합니다.

---

## 1. source-direct only보다 나은가

좋습니다.

기존 문제:

```text
direct economic signal 있음 → 긍정
```

Task703 방향:

```text
direct signal
+ financing overhang
+ guidance quality
+ novelty
+ noise/thinness
+ price absorption
```

이 구조가 더 trader-grade입니다.

특히 ASTS/SNOW 실패 원인으로 봤던:

```text
financing conflict
reaffirm guidance
high-noise thin signal
priced-in / absorption gap
```

을 upstream 전체 후보에 붙이는 건 맞습니다.

---

## 2. 가장 큰 leakage / overfit 위험

### 1) ASTS/SNOW 실패에서만 나온 키워드 과적합

```text
private offering
reaffirm
noise_ratio
price absorption
```

이 ASTS/SNOW에는 맞았지만, 전체 universe에서 과도하게 conservative할 수 있습니다.

### 2) price_absorption_confirmation_flag

이건 entry-time feature여야 합니다.
entry 이후 가격/거래량이 섞이면 즉시 leakage입니다.

### 3) action logic이 너무 필터형

```text
financing overhang → confirmation required
low novelty → research only
```

은 합리적이지만, 너무 강하면 winner를 죽일 수 있습니다.

### 4) no source packet 처리

```text
no source packet → research only
```

은 backtest universe를 크게 바꿀 수 있습니다.
반드시 event-linked 2,445와 full 5,265를 분리 비교해야 합니다.

---

## 3. Action state는 엄격한가, 느슨한가

현재는 **약간 엄격한 편**입니다.

특히:

```text
low novelty → RESEARCH_ONLY_LOW_NOVELTY
```

는 너무 강할 수 있습니다.

더 안전한 구조:

```text
financing overhang → CONFIRMATION_REQUIRED
guidance reaffirm/soft → CONFIRMATION_REQUIRED
high-noise thin + no absorption → CONFIRMATION_REQUIRED
low novelty → REVIEW_ONLY 또는 LOW_PRIORITY, 바로 제외는 신중
```

즉 처음부터 trade exclusion이 아니라 **eligibility tier**로 두는 게 낫습니다.

---

## 4. promising vs suspicious 결과 패턴

### Promising

```text
eligible 후보가 event_linked_2445보다
수익은 유지/개선하고
MDD와 failure rate를 줄임
```

그리고:

```text
validation / recent OOS 둘 다 방향이 같음
max5/10/20에서 과도하게 깨지지 않음
financing/high-noise/reaffirm bucket이 실제로 위험 분리
```

### Suspicious

```text
max5에서만 좋고 max10/20에서 붕괴
eligible 수가 너무 작음
ASTS/SNOW 같은 유형만 제거해서 좋아짐
recent OOS만 좋고 full/validation 약함
price_absorption 하나가 성과 대부분 설명
no source packet 제외 효과가 성과 대부분
```

---

## 5. 좋아 보여도 반드시 caveat로 보고할 것

```text
Strategy still NOT_ACCEPTED / FORBIDDEN
```

필수입니다.

또 반드시 보고:

```text
eligible count
blocked count by action state
no-source count
financing overhang count
guidance reaffirm/soft count
low novelty count
high-noise thin count
price absorption pass/fail count
```

그리고:

```text
outcome은 freeze 이후 attach
return/label/future price assignment 미사용
price absorption entry-time only 검증
```

을 audit로 남겨야 합니다.

---

## 최종 검수 의견

Task703은 진행할 가치가 있습니다.
단, 첫 버전은 **매수 룰**이 아니라 **source-direct 품질 필터 / confirmation layer**로 검증해야 합니다.

핵심은 이것입니다.

```text
좋은 뉴스인가?
```

가 아니라

```text
새롭고, 가격에 덜 반영됐고,
자금조달/노이즈/약한 가이던스 부담이 없는가?
```

를 검증하는 작업입니다.
