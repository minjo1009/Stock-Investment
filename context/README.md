# Context Index

## Purpose
- `context/`는 구현 전에 필요한 근거 문서를 체계적으로 정리하는 상위 인덱스다.
- 이 프로젝트에서 context는 phase/task 설계 입력과 변경 근거의 기준점 역할을 한다.
- 구현보다 context가 먼저 필요한 이유는, 구조/책임/현재 상태를 근거 없이 고정하는 위험을 줄이기 위해서다.

## Context Structure
- 하위 분류는 `product`, `architecture`, `codebase`, `workflow` 4개다.
- 4개 분류는 서로 대체 관계가 아니라 상호보완 관계다.
- 상위 인덱스(`context/README.md`)는 탐색 규칙과 문서 역할을 정의하고, 하위 인덱스(각 분류 `README.md`)는 분류별 문서 입구를 제공한다.

## Category Definitions
- `product`:
무엇을 만들고 무엇을 만들지 않는지에 답한다. 목표, 범위, 비범위, MVP, 운영 원칙을 기준으로 제품 경계를 고정한다.
- `architecture`:
시스템을 어떻게 나누고 어떤 경계로 연결하는지에 답한다. 계층/모델/계약 문서를 통해 목표 구조를 정의한다.
- `codebase`:
현재 저장소가 실제로 어떤 상태인지에 답한다. 관찰 기반 현황을 기록해 현재 상태와 목표 구조 혼동을 방지한다.
- `workflow`:
프로젝트에서 어떻게 일하는지에 답한다. phase/task/STOP/state 규칙으로 실행 거버넌스를 정의한다.

## Read Order
1. `skills/skill.md`
2. 관련 `phases/*.md`
3. 관련 `tasks/*.md`
4. `context/README.md`
5. `context/product/README.md`
6. `context/architecture/README.md`
7. `context/codebase/README.md`
8. `context/workflow/README.md`
9. 필요한 상세 계약 문서(`architecture/domain-model.md`, `architecture/contracts.md`, `workflow/execution-rules.md`, `workflow/state-management.md`)

## Facts vs Interpretation Policy
- context 문서는 Facts와 Interpretation을 혼합하지 않는다.
- `codebase`는 관찰 기반 현재 상태 문서다.
- `architecture`는 목표 구조 문서다.
- 미결정 사항은 사실처럼 기록하지 않고 별도 항목으로 분리한다.

## Current Coverage
- Product:
- `context/product/README.md`
- Architecture:
- `context/architecture/README.md` (overview)
- `context/architecture/domain-model.md` (detail model)
- `context/architecture/contracts.md` (contract)
- Codebase:
- `context/codebase/README.md`
- Workflow:
- `context/workflow/README.md` (overview)
- `context/workflow/execution-rules.md` (execution contract)
- `context/workflow/state-management.md` (state contract)

## Use in Phase and Task Planning
- `product`는 범위/비범위/MVP 기준으로 phase/task 경계 입력을 제공한다.
- `architecture`는 계층/객체/계약 기준으로 설계 task 분해 입력을 제공한다.
- `codebase`는 현재 저장소 제약과 공백 기준으로 우선순위 입력을 제공한다.
- `workflow`는 실행 규칙과 상태 관리 기준으로 수행 방식 입력을 제공한다.
- `Phase 01: Repository Foundation`은 특히 `codebase`의 현재 공백 + `architecture`의 목표 구조를 함께 입력으로 사용한다.

## Maintenance Rules
- 새 context 문서가 추가되면 상위 인덱스 갱신 필요성을 검토한다.
- 상위 인덱스와 하위 인덱스의 역할 충돌을 금지한다.
- 관찰 기반 문서(`codebase`)는 저장소 상태 변경 시 갱신한다.
- 상세 계약 문서가 추가되면 해당 하위 인덱스(`architecture` 또는 `workflow`)의 링크/역할 설명 갱신을 검토한다.

## Acceptance Criteria
- 새 작업자가 context 구조와 탐색 순서를 빠르게 이해할 수 있다.
- Codex가 문서 읽기 순서를 오해하지 않는다.
- overview 문서와 detail/contract 문서를 혼동하지 않는다.
- 현재 상태(`codebase`)와 목표 구조(`architecture`)를 혼동하지 않는다.
- `Phase 01` 및 후속 task 생성 입력으로 즉시 사용할 수 있다.
