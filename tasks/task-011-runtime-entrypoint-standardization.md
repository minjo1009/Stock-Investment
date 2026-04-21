# Task 011: Runtime Entrypoint Standardization

## Purpose
- 저장소의 실행 진입점과 실행 계약을 표준화한다.

## Background
- Foundation 단계에서 구현 속도보다 실행 재현성이 우선이다.
- 실행 명령/입력/출력 기준이 없으면 task별 Generate/Evaluate 결과를 비교하기 어렵다.

## In Scope
- 실행 진입점 기준 문서 작성 또는 갱신
- 실행 명령 예시와 입력 파라미터 규약 정의
- 실행 종료 시 필수 출력 항목 정의

## Out of Scope
- 전략 신호 생성 로직 구현
- 브로커 API 호출 구현
- 성능 최적화

## Inputs
- `phases/phase-01-repository-foundation.md`
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `src/app/main.py`
- `src/app/pipeline.py`

## Outputs
- 실행 진입점 표준 문서
- 실행 예시 명령과 기대 출력 체크리스트

## Target Files
- `README.md`
- 필요 시 `context/workflow/README.md`

## Dependencies
- 선행: Task 013(artifact 규약), Task 014(handoff 템플릿)
- 후행 연계: Task 012(검증 루프 표준화)

## Implementation Notes
- 실행 규약은 5단계 하네스의 Generate/Evaluate와 직접 연결한다.
- 실행 예시는 `paper` 환경 기준을 기본값으로 둔다.
- 문서는 실제 존재 코드와 불일치하지 않도록 작성한다.

## Acceptance Criteria
- 신규 작업자가 문서만으로 동일 실행 명령을 수행할 수 있다.
- 실행 입력과 출력 기대값이 명확히 구분된다.
- 실행 규약이 workflow 하네스 규칙과 충돌하지 않는다.

## Tests
- 문서의 실행 명령을 따라 1회 실행 시 실패 없이 종료된다.
- 출력 체크리스트 항목이 실제 콘솔 출력 또는 로그와 대응된다.

## Risks
- 코드 변경 없이 문서만 갱신할 경우 실제 실행 흐름과 문서가 빠르게 불일치할 수 있다.
