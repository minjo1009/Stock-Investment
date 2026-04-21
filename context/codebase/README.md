# Codebase Context (Observation-Based)

## Purpose
- 이 문서는 현재 워크스페이스의 실제 파일/폴더 상태를 관찰 기반으로 기록한다.
- 본 문서는 `Phase 01: Repository Foundation` 및 후속 구현 Task의 입력 자료로 사용된다.
- 목적은 추측 제거이며, 설계 목표와 현재 상태를 분리해 전달하는 것이다.

## Observation Scope
- 관찰 기준 시점: 2026-04-18.
- 관찰 범위: 현재 워크스페이스 루트 및 하위 디렉터리의 실제 존재 파일/폴더.
- 관찰 방법: 디렉터리/파일 목록 조회(`Get-ChildItem`), 재귀 파일 조회, 확장자 집계.
- 원칙: 존재하는 항목만 기록한다. 추정, 상상, 숨은 구조 가정은 기록하지 않는다.

## Current Repository State
- 현재 저장소는 문서 중심 작업 공간이다.
- 전체 파일 확장자 관찰 결과는 `.md`만 확인되었다(총 23개).
- 현재 단계는 Project Operating System + Context Inventory 문서 체계 구축 단계다.
- 실행 가능한 코드 엔트리포인트나 테스트 실행 자산은 관찰되지 않았다.

## Root Inventory
- `skills/`: 운영 상위 규칙 문서(`skill.md`) 보관.
- `prompts/`: phase/task 생성 규격 문서 보관.
- `phases/`: 상위 단계 문서 보관(`phase-00`, `phase-02` 관찰).
- `tasks/`: 실행 단위 문서 보관(`task-001`~`task-005` 관찰).
- `context/`: product/architecture/codebase/workflow 근거 문서 보관.
- `templates/`: phase/task 템플릿 문서 보관.
- `src/`: 디렉터리 존재, 내부 파일 관찰되지 않음.
- `tests/`: 디렉터리 존재, `README.md`만 관찰.
- `README.md`: 루트 작업 안내 문서.

## Code Presence Status
- `src/`:
- 디렉터리는 존재한다.
- 재귀 조회 기준 파일이 관찰되지 않았다.
- 실행 코드 자산 존재 여부: 현재 기준 없음.
- `tests/`:
- 디렉터리는 존재한다.
- `tests/README.md` 1개 파일만 관찰되었다.
- 테스트 코드 자산 존재 여부: 현재 기준 없음.
- 결론:
- 코드/테스트 로직보다 문서 체계가 선행된 상태다.

## Document System Status
- `skill / prompt / phase / task / template / context` 체계는 실제 파일로 정비되어 있다.
- `context` 하위 분류(`product`, `architecture`, `codebase`, `workflow`)가 모두 존재한다.
- `architecture`에는 `domain-model.md`, `contracts.md`가 존재한다.
- `workflow`에는 `execution-rules.md`, `state-management.md`가 존재한다.
- 문서 운영 시스템은 구축되었고, 구현 코드 시스템은 아직 비어 있다.

## Current Gaps
- `src/` 내 실행 코드 파일 부재.
- 테스트 로직 파일 부재(`tests/README.md`만 존재).
- 실행 엔트리포인트(예: 앱 시작 파일, 런너 스크립트) 부재.
- 코드 모듈 경계(디렉터리 레벨) 구체안 미정.
- 테스트 체계(단위/통합/리플레이) 파일 구조 미정.

## Impact on Next Phase
- `Phase 01: Repository Foundation`는 코드베이스 골격을 우선 정의해야 한다.
- 현재 상태에서 우선순위는 실행 코드 작성이 아니라 저장소 구조 확정이다.
- 다음 단계 입력으로 필요한 항목:
- `src/` 모듈 경계와 엔트리포인트 구조.
- `tests/` 테스트 유형별 디렉터리 규칙.
- 실행/검증/리포트 경로를 반영한 파일 배치 기준.

## Facts vs Interpretation
- Facts
- 루트 디렉터리 8개(`context`, `phases`, `prompts`, `skills`, `src`, `tasks`, `templates`, `tests`)와 루트 파일 `README.md`가 관찰되었다.
- 재귀 파일 조회 결과 총 23개 파일이 관찰되었고 모두 `.md`였다.
- `src/`는 비어 있고, `tests/`는 `README.md`만 존재한다.
- `context` 하위 4분류 및 architecture/workflow 상세 문서가 존재한다.
- Interpretation
- 저장소는 구현 단계 이전의 문서 우선 상태로 해석된다.
- Foundation 단계에서 코드/테스트 구조를 먼저 확정하지 않으면 후속 Task 경계가 흔들릴 가능성이 높다.

## Maintenance Rules
- 본 문서는 관찰 결과로만 갱신한다.
- 저장소 구조가 변경되면 동일 작업 턴에서 본 문서 갱신 여부를 검토한다.
- 현재 상태와 목표 상태를 한 문장에 혼합하지 않는다.
- 새 코드/디렉터리/엔트리포인트가 추가되면 `Root Inventory`, `Code Presence Status`, `Current Gaps`를 우선 갱신한다.
- 설계 제안은 Facts와 분리된 섹션에서만 기록한다.

## Acceptance Criteria
- 다른 작업자가 본 문서만 읽고 현재 저장소 상태를 빠르게 파악할 수 있다.
- 문서 내용이 실제 워크스페이스 조회 결과와 일치한다.
- 현재 상태와 다음 단계 목표 입력이 혼동되지 않는다.
- `Phase 01: Repository Foundation` 설계 입력으로 즉시 사용 가능하다.
