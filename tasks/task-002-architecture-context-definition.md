# Task 002: Architecture Context Definition

## Purpose
- 상위 아키텍처 원칙과 계층 경계를 architecture context로 정의한다.

## Background
- Product 요구를 구현 가능한 구조로 전환하려면 계층 책임과 경계 정의가 필요하다.
- Strategy/Risk/Execution 혼재는 운영 리스크를 증가시킨다.

## In Scope
- 5계층 구조 기준 정의
- KR/US 분리와 공유 범위 정의
- Strategy/Risk/Execution/Position Engine 경계 정의
- Hard Block/Soft Block 위치 및 책임 정의
- 이벤트 기반 + 보조 폴링 원칙 반영

## Out of Scope
- 클래스/함수 단위 구현 설계
- 백테스트/실행 엔진 구현
- 브로커 API 세부 연동 구현

## Inputs
- `skills/skill.md`
- `phases/phase-02-context-inventory.md`
- `tasks/task-001-product-context-definition.md`
- `context/architecture/README.md`

## Outputs
- `context/architecture/README.md`에 상위 구조 인덱스 기준 반영
- 후속 상세 architecture 문서 작성 기준 정의

## Target Files
- `context/architecture/README.md`

## Dependencies
- 선행: Task 001(Product 경계 정의)
- 참조: Task 003(Codebase 실측 결과)

## Implementation Notes
- 반드시 반영할 항목:
- 5계층 구조
- KR/US 분리
- Strategy/Risk/Execution 분리
- Position Engine 분리
- Hard Block/Soft Block
- 백테스트 룰 기반 only
- LLM은 ranking/reporting 보조
- 이벤트 기반 + 보조 폴링
- 장애복구/감사추적/운영관제 수용 가능 구조
- 구현 세부가 아니라 책임 경계 중심으로 작성한다.

## Acceptance Criteria
- 각 계층 책임이 서로 섞이지 않는다.
- Product 요구사항과 충돌하지 않는다.
- 구현 이전의 상위 구조가 문서만으로 파악된다.

## Tests
- 문서만 읽고 Strategy와 Execution 책임을 혼동하지 않는다.
- KR/US의 공유/분리 범위를 설명할 수 있다.

## Risks
- 계층 정의가 모호하면 구현 단계에서 결합도가 높아진다.
- Product와 Architecture 간 불일치가 발생하면 재설계 비용이 커진다.
