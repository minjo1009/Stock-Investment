# Workflow Execution Rules

## Purpose
- Workflow를 설명 문서가 아니라 실행 통제 규칙으로 고정한다.
- 인간, Codex, GPT가 동일한 실행 단위와 종료 형식을 사용하도록 강제한다.

## Execution Unit
- 1 Codex Run = 1 Task 수행.
- 여러 Task 동시 수행 금지.
- Task 범위 외 수정 금지.
- 모든 실행은 아래 표준 보고 형식으로 종료한다.
- `changed files`
- `summary`
- `validation`
- `risks`
- `next actions`

## Step Contracts
### Clarify
- Input: 사용자 요구사항.
- Output: 명확화된 요구, 범위, 미결정 사항.
- 금지사항: 구현 시작 금지.

### Context Gather
- Input: Clarify 결과.
- Output: context 문서, 관찰 결과, 설계 근거.
- 금지사항:
- 추론 기반 작성 금지.
- codebase 가정 금지.

### Plan
- Input: context.
- Output: phase 또는 task 계획.
- 금지사항: 계획 없이 구현 금지.

### Taskize
- Input: plan.
- Output: task 문서.
- 금지사항:
- 리팩토링, 최적화, 전반 개선.
- 필수 조건:
- 1 task = 1 목적.
- acceptance criteria 필수.
- tests 필수.

### Implement
- Input: task 문서.
- Output: 변경된 파일.
- 금지사항:
- 범위 외 수정.
- silent refactor.

### Test
- Input: 구현 결과.
- Output: 검증 결과.
- 금지사항: 검증 없이 완료 선언 금지.

### Report
- Input: 테스트 결과.
- Output: 표준 보고 형식.
- 금지사항: 비표준 종료 보고 금지.

## STOP Handling
- STOP 조건:
- 요구사항 불명확.
- 입력 부족.
- 범위 불명확.
- 상위 문서와 충돌.
- acceptance criteria 없음.
- codebase 상태 확인 불가.
- STOP 시 아래 형식을 그대로 사용한다.

```text
STOP REASON:
MISSING INFORMATION:
IMPACT:
NEXT ACTION:
```

## Task Execution Rules
- Task Isolation:
- 실행 중에는 현재 Task의 Target Files와 In Scope만 수정한다.
- Determinism:
- 동일 입력은 동일 산출물을 생성해야 한다.
- Reproducibility:
- 동일 문맥과 입력으로 언제든 재실행 가능해야 한다.

## AI Execution Rules
- Codex:
- task 범위 내 실행.
- 규칙 위반 조건 감지 시 즉시 STOP.
- GPT:
- 설계 및 검수 담당.
- 실행 규칙 위반 여부 검토 및 수정 지시 담당.

## Hard Constraints
- Strategy broker 호출 금지.
- Execution signal 생성 금지.
- Risk 주문 실행 금지.
- Intelligence 매매 결정 금지.
- 본 제약은 `context/architecture/contracts.md`와 동일 우선순위로 적용한다.

## Acceptance Criteria
- Execution Unit이 1 Run 1 Task로 명시되어 있다.
- 모든 Step에 Input/Output/금지사항이 존재한다.
- STOP 조건과 STOP 출력 형식이 명시되어 있다.
- Task Isolation/Determinism/Reproducibility 규칙이 포함되어 있다.
- Hard Constraints가 아키텍처 계약 문서와 충돌하지 않는다.
