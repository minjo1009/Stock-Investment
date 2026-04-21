# Workflow Execution Rules

## Purpose
- Workflow를 설명 문서가 아니라 실행 통제 규칙으로 고정한다.
- 인간, Codex, GPT가 동일한 실행 단위와 종료 형식을 사용하도록 강제한다.

## Execution Unit
- 1 Codex Run = 1 Task 수행.
- 여러 Task 동시 수행 금지.
- Task 범위 외 수정 금지.
- 1 Stage = 1 Sub-Agent 수행.
- Stage는 `Clarify -> Context Gather -> Plan -> Generate -> Evaluate` 순서를 강제한다.
- 모든 실행은 아래 표준 보고 형식으로 종료한다.
- `changed files`
- `summary`
- `validation`
- `risks`
- `next actions`

## Step Contracts
### Clarify
- Input: 사용자 요구사항.
- Output: 명확화된 요구, 범위, 미결정 사항, 제약.
- Artifact: `artifacts/<task-id>/clarify.md`
- 금지사항: 구현 시작 금지.

### Context Gather
- Input: Clarify 결과.
- Output: context 문서, 관찰 결과, 설계 근거.
- Artifact: `artifacts/<task-id>/context-gather.md`
- 금지사항:
- 추론 기반 작성 금지.
- codebase 가정 금지.

### Plan
- Input: Context Gather 결과.
- Output: phase 또는 task 계획, Target Files, Acceptance Criteria, Tests.
- Artifact: `artifacts/<task-id>/plan.md`
- 금지사항:
- 계획 없이 Generate 시작 금지.

### Generate
- Input: Plan 결과.
- Output: 변경된 파일, 구현 로그.
- Artifact: `artifacts/<task-id>/generate.md`
- 금지사항:
- 범위 외 수정.
- silent refactor.

### Evaluate
- Input: Generate 결과.
- Output: 검증 결과, 완료/차단 판정, 잔여 리스크.
- Artifact: `artifacts/<task-id>/evaluate.md`
- 금지사항:
- 검증 없이 완료 선언 금지.
- Evaluate 생략 금지.

## Sub-Agent Handoff Rules
- 단계별 sub-agent는 직전 단계 artifact를 명시적으로 입력받아야 한다.
- artifact가 없거나 손상되면 다음 단계로 진행하지 않고 `blocked` 처리한다.
- 각 단계의 출력은 사실/관찰/판정 중심으로 작성한다.
- 단계 간 구두 요약만으로 handoff 하지 않는다.
- 재시도 시 기존 artifact를 덮어쓰지 않고 버전 suffix를 추가한다.

## STOP Handling
- STOP 조건:
- 요구사항 불명확.
- 입력 부족.
- 범위 불명확.
- 상위 문서와 충돌.
- acceptance criteria 없음.
- codebase 상태 확인 불가.
- 직전 단계 artifact 없음.
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
