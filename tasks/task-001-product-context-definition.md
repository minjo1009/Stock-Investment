# Task 001: Product Context Definition

## Purpose
- 프로젝트의 목표, 범위, 비범위, MVP, 운영 정책을 Product context 관점에서 명확히 정의한다.

## Background
- Phase 02의 목적은 구현이 아니라 근거 기반 설계 준비다.
- Product 범위가 먼저 고정되지 않으면 아키텍처/구현 경계가 흔들린다.

## In Scope
- product context 문서 기준 정의
- 목표/범위/비범위/MVP 항목 구조화
- 운영 원칙(자동운영, Slack 명령, LLM 보조 제한) 정리
- 미결정 사항 분리 방식 정의

## Out of Scope
- 전략 규칙 상세 구현
- 브로커 연동 상세 설계/구현
- 실행 코드 및 테스트 코드 변경

## Inputs
- `skills/skill.md`
- `phases/phase-00-project-operating-system.md`
- `phases/phase-02-context-inventory.md`
- 기존 `context/README.md`

## Outputs
- `context/product/README.md` 갱신 기준 확정
- 필요 시 후속 product 상세 문서 작성 규칙 정의

## Target Files
- `context/product/README.md`

## Dependencies
- 선행: Phase 00 운영 규칙 이해
- 병행 가능: Task 003
- 후행 연계: Task 002, Task 005

## Implementation Notes
- 반드시 반영할 합의 항목:
- 완전 자동 운영
- Slack 기반 명령
- 룰 기반 매매
- LLM 보조 역할 제한
- KR/US 분리
- 초기 MVP 전략 1개
- 키워드/리포트 분석은 초기 보고/설명 전용
- 시각화 초기 범위
- 장애복구/리스크통제/감사추적성/운영관제/유지보수 체계 수용
- 사실과 미결정 항목을 분리한다.
- 구현 계획을 사실처럼 단정하지 않는다.

## Acceptance Criteria
- 목표/범위/비범위가 혼동 없이 구분된다.
- Product 합의 사항과 미결정 사항이 분리되어 기록된다.
- Architecture 문서 책임과 충돌하지 않는다.

## Tests
- 문서를 읽은 제3자가 “무엇을 만들고 무엇을 아직 만들지 않는지”를 1회 독해로 설명할 수 있다.
- LLM 역할이 의사결정 주체가 아니라 보조로 제한됨이 명확하다.

## Risks
- 범위/비범위 구분이 약하면 이후 구현 단계에서 scope creep가 발생한다.
- MVP 정의가 모호하면 Architecture 경계가 흔들린다.
