# Phase 02: Context Inventory

## Objective
- 이후 설계/구현/검증이 근거 기반으로 진행되도록 context 체계를 구축한다.
- product, architecture, codebase, workflow 4개 범주의 인덱스와 초기 사실 집계를 완료한다.
- 구현 이전 의사결정 기준(사실/해석/미결정 분리)을 문서로 고정한다.

## Why This Phase Exists
- Phase 00은 운영 체계 정의를 완료했지만, 실제 구현 단계로 넘어가기 위한 근거 인벤토리가 아직 부족하다.
- Repository Foundation(Phase 01)을 먼저 진행하면 근거 없이 구조를 고정할 위험이 있다.
- 따라서 Phase 02에서 context를 먼저 수집·정리해 이후 구조 설계와 구현 우선순위의 기준을 확보한다.
- 본 Phase는 문서/인벤토리 구축 단계이며 트레이딩 기능 구현 단계가 아니다.

## Entry Conditions
- `skills/skill.md`, `prompts/task-create.md`, `prompts/phase-create.md`를 읽고 운영 규칙을 수용한 상태.
- `phases/phase-00-project-operating-system.md`가 존재하고 형식상 완료된 상태.
- 구현 코드(`src/`) 및 테스트 로직 변경 없이 문서 작업만 수행하는 범위가 합의된 상태.

## Scope
- context 4분류 인덱스 구조 생성/정비
- Phase 02 정의 문서 작성
- Phase 02 실행용 Task 5개 정의
- 저장소 실측 기반 codebase 관찰 기준 수립

## Out of Scope
- 트레이딩 로직 구현
- 브로커 연동 구현
- 전략 엔진/백테스트 엔진 구현
- `src/` 내부 코드 로직 수정
- 테스트 로직 구현

## Deliverables
- `context/README.md`
- `context/product/README.md`
- `context/architecture/README.md`
- `context/codebase/README.md`
- `context/workflow/README.md`
- `tasks/task-001-product-context-definition.md`
- `tasks/task-002-architecture-context-definition.md`
- `tasks/task-003-codebase-context-scan.md`
- `tasks/task-004-workflow-context-definition.md`
- `tasks/task-005-context-index-build.md`

## Task Inventory
- Task 001: Product context 정의(목표/범위/비범위/MVP/운영 정책)
- Task 002: Architecture context 정의(원칙/계층/경계/흐름)
- Task 003: Codebase context 스캔(실측 인벤토리)
- Task 004: Workflow context 정의(작업 흐름/변경관리/STOP)
- Task 005: Context index 빌드(4분류 탐색 체계 정비)

## Execution Order
1. Task 003으로 현재 저장소 사실을 확보한다.
2. Task 001로 제품 목표와 범위를 고정한다.
3. Task 002로 상위 구조 경계를 고정한다.
4. Task 004로 작업 거버넌스를 고정한다.
5. Task 005로 전체 context 탐색 인덱스를 최종 정리한다.

## Exit Criteria
- 4개 context 분류 디렉터리와 README가 존재한다.
- Task 001~005가 템플릿 섹션을 충족하며 실행 가능한 단위로 작성된다.
- 문서가 사실/해석/미결정 분리를 명시한다.
- 구현 코드와 테스트 로직은 변경되지 않는다.
- Phase 01 또는 다음 상세기획 phase로 handoff 가능한 기준 문서가 준비된다.

## Risks
- 근거 수집 전에 구조 결정을 강행하면 이후 재작업 비용이 증가한다.
- Product/Architecture 책임 분리가 불명확하면 Task 간 산출물 충돌이 발생한다.
- Codebase 실측 없이 작성하면 문서 신뢰도가 급격히 떨어진다.
- Workflow 거버넌스가 약하면 무규칙 수정과 silent refactor가 재발한다.

## Handoff
- 선택지 1: `Phase 01: Repository Foundation`으로 넘어가 context 근거에 기반해 저장소 구조를 설계/고정한다.
- 선택지 2: 다음 상세기획 phase로 넘어가 product/architecture 세부 명세를 확장한 뒤 구현 phase를 시작한다.
