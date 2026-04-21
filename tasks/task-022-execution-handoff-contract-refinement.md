# Task 022: Execution Handoff Contract Refinement

## Purpose
- OrderIntent를 Execution canonical 입력 계약으로 정제한다.

## Background
- 초기 handoff는 동작했지만 quantity/reduce 표현이 중복되고 의미가 모호했다.

## In Scope
- quantity 의미 확정(Option A: 최종 수량)
- reduce_applied 제거, reduce_factor 단일화
- OrderIntent 필드 최소화
- contracts/domain-model 동기화
- 검증 테스트 보강

## Out of Scope
- sizing 계산
- 가격/슬리피지 계산
- 주문 실행 로직

## Inputs
- `src/common/models.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/app/pipeline.py`

## Outputs
- refined OrderIntent canonical contract

## Target Files
- `src/common/models.py`
- `context/architecture/contracts.md`
- `context/architecture/domain-model.md`
- `src/execution/interface.py`
- `src/app/pipeline.py`
- `tests/unit/test_structure.py`

## Dependencies
- 선행: Task 018, Task 020

## Implementation Notes
- quantity 없음은 계산 대기가 아니라 실행 불가로 해석.
- reduce_factor는 (0,1]만 허용.

## Acceptance Criteria
- OrderIntent 의미가 문서+코드에 단일 정의로 고정.
- ambiguity(reduce_applied vs reduce_factor) 제거.

## Tests
- quantity 양수 검증
- reduce_factor 범위 검증
- mapping에서 quantity 미지정 시 None 반환 검증

## Risks
- skeleton 파이프라인에서 quantity 공급 주체가 아직 없어 intent 미생성 상태 유지 가능.

