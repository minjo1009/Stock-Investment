# Task 003: Codebase Context Scan

## Purpose
- 현재 저장소의 실제 파일/폴더 상태를 관찰해 codebase context를 정리한다.

## Background
- 실측 없이 구조를 가정하면 Repository Foundation 단계에서 오설계 위험이 커진다.
- Phase 02는 추정이 아닌 관찰 기반 근거 축적을 우선한다.

## In Scope
- 루트 및 핵심 디렉터리 인벤토리 기록
- 문서 중심/코드 중심 상태 관찰
- 핵심 문서 위치와 역할 매핑
- 현재 상태와 목표 상태의 분리 기록

## Out of Scope
- 파일 구조 리팩터링
- 코드/테스트 추가 및 수정
- 빌드/실행 환경 변경

## Inputs
- 실제 저장소 파일 시스템 상태
- `phases/phase-02-context-inventory.md`
- `context/codebase/README.md`

## Outputs
- `context/codebase/README.md` 갱신
- 관찰 시점 기준 인벤토리 섹션 작성

## Target Files
- `context/codebase/README.md`

## Dependencies
- 선행: 없음
- 후행 연계: Task 005

## Implementation Notes
- 없는 구조를 상상해 작성하지 않는다.
- 관찰 기반 기술만 사용한다.
- 관찰 시점과 범위를 문서에 명시한다.
- “현재 상태”와 “향후 목표”를 같은 문단에서 혼합하지 않는다.

## Acceptance Criteria
- 문서 내용이 실제 파일 구조와 일치한다.
- 현재 상태와 목표 상태가 구분된다.
- 추정이 아닌 관찰 기반임이 드러난다.

## Tests
- 처음 보는 작업자가 문서만 읽고 루트 구조와 핵심 문서 위치를 빠르게 파악할 수 있다.
- 문서의 인벤토리 항목을 파일 시스템 조회로 재현할 수 있다.

## Risks
- 실측 누락 시 이후 phase에서 잘못된 전제가 전파된다.
- 인벤토리 갱신 주기가 불명확하면 문서 신뢰도가 빠르게 저하된다.
