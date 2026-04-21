# Task 015: Environment Config Convention

## Purpose
- `paper/live` 분리 전제를 유지하는 실행/검증 환경 설정 규약을 문서화한다.

## Background
- architecture 계약은 cross-env 혼합을 금지한다.
- Foundation 단계에서 환경 설정 규약을 먼저 고정해야 후속 구현에서 결합 오류를 줄일 수 있다.

## In Scope
- 환경 식별자 규약(`paper`, `live`) 정의
- 실행/테스트/리포트에서 환경 태그 필수 규칙 정의
- 환경별 로그/산출물 분리 원칙 문서화

## Out of Scope
- 실제 비밀키/자격증명 관리 도입
- 운영 인프라 배포
- 외부 비밀관리 시스템 연동

## Inputs
- `context/architecture/contracts.md`
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `phases/phase-01-repository-foundation.md`

## Outputs
- 환경 설정 및 분리 규약 문서
- 실행/검증 단계 체크리스트의 환경 항목

## Target Files
- `README.md`
- `context/architecture/contracts.md` (필요 시 참조 보강)
- `context/workflow/README.md` (필요 시 참조 보강)

## Dependencies
- 선행: Task 011, Task 012
- 후행: 다음 구현 phase의 실행 task

## Implementation Notes
- 환경 규약은 설정 방법보다 분리 원칙을 우선한다.
- 문서에는 cross-env 금지 사례를 명시한다.
- 실행/검증 artifact에 env 필드를 필수로 요구한다.

## Acceptance Criteria
- paper/live 분리 규칙이 실행/검증 문서에 반영된다.
- 신규 task 작성 시 환경 지정 기준을 즉시 적용할 수 있다.
- architecture 계약과 workflow 문서 간 환경 규약 충돌이 없다.

## Tests
- 샘플 artifact에서 env 미기재 시 규칙 위반으로 판정할 수 있다.
- 동일 symbol이라도 env가 다르면 다른 상태로 취급됨을 문서로 확인할 수 있다.

## Risks
- 설정 상세를 과도하게 단순화하면 실제 운영 단계에서 추가 재작업이 필요할 수 있다.
