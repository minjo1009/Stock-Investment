# Task Result Reporting Framework

이 문서는 앞으로 모든 task 결과 보고에 적용할 기본 형식이다.

핵심 목적은 두 가지다.

1. quant 전문가가 검증 가능한 숫자, 누수 여부, 표본 한계, 전략적 시사점을 바로 판단할 수 있게 한다.
2. 배경지식이 없는 의사결정자가 과장 없이 현재 상태, 의미, 한계, 다음 결정을 이해할 수 있게 한다.

## Non-Negotiable Reporting Rules

- 측정된 사실과 해석을 분리한다.
- 추론 기반 lifecycle 연결, symbol/date/price/time proximity matching은 사용하지 않았는지 명시한다.
- `decision_id`, `lifecycle_id` exact join 여부를 반드시 보고한다.
- label 없는 row는 negative가 아니라 `unlabeled`로 보고한다.
- diagnostic, validation, deployment-ready를 절대 섞지 않는다.
- artifact, test, exact metric으로 확인되지 않은 내용은 결론처럼 쓰지 않는다.
- 결과가 약하면 약하다고 쓴다. `promising`이라는 표현은 근거와 제한을 함께 붙일 때만 쓴다.

## Required Report Structure

모든 task 결과 보고는 아래 두 섹션을 모두 포함한다.

## 1. Quant Expert Report

### 1. Task Scope

- Task 이름과 목적
- 이번 task가 검증하려는 정확한 질문
- 이번 task가 검증하지 않는 것

### 2. Data And Identity Integrity

- 입력 artifact 목록
- primary population
- exact join key
- labelable / unlabeled / non-lifecycle candidate 수
- exact label coverage
- inferred matching 사용 여부: `YES/NO`
- unlabeled row를 negative로 처리했는지 여부: `YES/NO`

### 3. Core Metrics

필요한 경우 아래를 포함한다.

- lifecycle count
- decision count
- ADD/SCALE success rate
- false positive rate
- `entry_reduce_failure` rate
- `add_only_weak` rate
- `post_cost_false_positive` rate
- post-cost average return
- compounded PnL proxy
- validation / recent OOS split quality
- monthly stability
- theme concentration
- symbol concentration
- capacity / trade density

### 4. Leakage And Inference Audit

- forbidden columns excluded 여부
- outcome/exit/reduce/realized return/net return이 feature에 들어갔는지 여부
- future information 사용 여부
- source discipline 이슈
- known limitation

### 5. Interpretation

반드시 아래 순서로 쓴다.

- Measured facts
- What we can conclude
- What we cannot conclude
- Confidence level: `HIGH / MEDIUM / LOW`
- Main failure mode
- Alternative explanation

### 6. Next Technical Action

- 다음에 고쳐야 할 코드/데이터 경로
- 다음에 돌려야 할 테스트
- 다음 task로 넘어가도 되는지 여부
- 넘어가면 안 된다면 blocker를 명확히 쓴다.

## 2. No-Background Decision-Maker Report

### 1. Bottom Line

세 줄 이내로 쓴다.

- 이번 결과가 좋은지 나쁜지
- 지금 무엇을 결정할 수 있는지
- 아직 무엇을 결정하면 안 되는지

### 2. What Changed

전문 용어를 최소화해서 설명한다.

- 이전 상태
- 이번 task 이후 상태
- 가장 중요한 변화

### 3. Business / Strategy Meaning

- 이 결과가 전략에 어떤 의미인지
- 실전 투입과 어떤 거리가 있는지
- 지금 단계가 연구, 검증, 배포 중 어디인지

### 4. Main Risk

가장 큰 위험 하나를 먼저 쓴다.

예:

- label coverage 부족
- false positive 과다
- OOS 붕괴
- 특정 theme/symbol 과집중
- 비용 후 edge 소멸
- 데이터 source 불완전

### 5. Recommended Decision

명확히 하나로 쓴다.

- Continue
- Pause and repair data
- Reject current approach
- Run more validation
- Do not deploy

### 6. Next Step

다음 행동을 하나 또는 두 개로 제한한다.

## Mandatory Final Verdict Format

모든 보고서 마지막에는 아래 형식을 붙인다.

```text
Measured facts:
- ...

What we can conclude:
- ...

What we cannot conclude:
- ...

Recommended next action:
- ...

Deployment status:
- NOT_DEPLOYMENT_READY / DIAGNOSTIC_ONLY / VALIDATION_READY / DEPLOYMENT_READY
```

## Low-Confidence Warning Rules

아래 중 하나라도 해당하면 결론의 신뢰도를 낮게 표시한다.

- exact label coverage insufficient
- validation or recent OOS sample underpowered
- source data proof unavailable
- inferred matching required
- unlabeled rows large
- false positive rate remains high
- one symbol/theme dominates result
- post-cost expectancy weak or negative
- monthly stability poor

이 경우 보고서에는 반드시 다음 문장을 포함한다.

```text
This result is not strategy validation. It is diagnostic evidence only.
```

