# Workflow State Management

## Purpose
- Phase와 Task 상태를 일관된 규칙으로 추적한다.
- 진행, 의존성, 차단, 이력 관리 기준을 고정해 실행 흐름을 통제한다.

## Phase State
```yaml
phase_status:
  - not_started
  - in_progress
  - completed
  - blocked
```

## Task State
```yaml
task_status:
  - created
  - in_progress
  - done
  - blocked
```

## State Transition Rules
- 정의된 상태 외 전이 금지.
- `phase_status`: `not_started -> in_progress -> completed` 또는 `blocked`.
- `task_status`: `created -> in_progress -> done` 또는 `blocked`.
- `blocked` 해제 시 직전 활성 상태(`in_progress`)로만 복귀한다.
- 상태 전이는 근거 문서 또는 실행 로그를 동반해야 한다.

## State Ownership
- Phase 상태 소유자: 인간 또는 GPT.
- Task 상태 소유자: Codex 실행 결과 기반.
- 소유자 외 주체는 상태를 임의 변경하지 않는다.

## Backlog Management
- 모든 backlog 항목은 아래 3개 속성을 가진다.
- `priority`
- `dependency`
- `status`
- backlog 정렬은 `priority` 우선, 동순위는 `dependency` 충족 순으로 처리한다.

## Dependency Rule
- 선행 task 없이 후행 task 실행 금지.
- 의존성이 `done`이 아니면 후행 task 상태를 `in_progress`로 전이할 수 없다.
- 순환 의존성 발견 시 즉시 `blocked`로 전환하고 조정한다.

## Progress Tracking
- Task 단위 진행 추적:
- 시작 시 `created -> in_progress`.
- 완료 검증 후 `done`.
- 이슈 발생 시 `blocked`.
- Phase 완료 기준:
- 모든 Task 완료.
- acceptance criteria 충족.
- 미결정 사항 분리 완료.

## Blocked Handling
- 차단 상태 보고는 아래 형식을 그대로 사용한다.

```text
BLOCKED REASON:
DEPENDENCY:
RESOLUTION:
```

## Audit Trail
- 기록 항목:
- 언제(타임스탬프)
- 어떤 작업(phase/task 식별자)
- 결과(상태 변경, 산출물, 검증 결과)
- 상태 전이와 차단 해제는 모두 추적 가능한 로그를 남긴다.

## Acceptance Criteria
- phase/task 상태 정의가 문서에 포함되어 있다.
- 상태 전이 규칙이 정의된 상태 집합과 일치한다.
- backlog 관리 속성(priority/dependency/status)이 명시되어 있다.
- blocked 처리 형식이 고정되어 있다.
- 진행 추적과 감사 이력 규칙이 실행 가능 수준으로 정의되어 있다.
