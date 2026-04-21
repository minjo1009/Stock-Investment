# Task 006: Harness Pipeline Upgrade with Sub-Agents

## Purpose
- 프로젝트 하네스 파이프라인을 5단계(Clarify, Context Gather, Plan, Generate, Evaluate)로 고정한다.
- 각 단계를 별도 sub-agent 실행 단위로 정의하고 artifact handoff 규칙을 도입한다.

## Background
- 기존 workflow는 Taskize/Implement/Test/Report 분리로 정의되어 있으나, 단계별 실행 책임과 산출물 전달 규약을 더 명확히 할 필요가 있다.
- 단계별 artifact 기반 handoff를 도입하면 재현성, 감사추적성, 중단 후 재개 품질이 개선된다.

## In Scope
- `skills/skill.md`의 표준 워크플로 개정
- `context/workflow/execution-rules.md`의 단계 계약 및 sub-agent 규칙 개정
- `context/workflow/README.md` 인덱스 문구 개정

## Out of Scope
- 실제 트레이딩 로직 구현 변경
- 브로커 연동/전략 엔진 변경
- CI/CD 또는 자동 오케스트레이터 코드 구현

## Inputs
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `context/workflow/README.md`

## Outputs
- 5단계 파이프라인 정의 반영
- 단계별 sub-agent + artifact handoff 계약 반영

## Target Files
- `skills/skill.md`
- `context/workflow/execution-rules.md`
- `context/workflow/README.md`

## Dependencies
- 선행: Phase 00 운영 규칙 유지
- 후행: 필요 시 상태관리 문서(`context/workflow/state-management.md`) 세부 확장

## Implementation Notes
- 기존 핵심 원칙(룰 기반 매매, LLM 보조 역할 제한, 무규칙 수정 금지)을 유지한다.
- 기존 문서와 충돌하는 표현을 제거하고 단일 정답 흐름으로 정리한다.
- 단계 산출물은 다음 단계 입력으로 명시한다.

## Acceptance Criteria
- 표준 작업 흐름이 5단계로 명시된다.
- 각 단계가 별도 sub-agent 단위로 정의된다.
- artifact handoff 규칙이 문서에 포함된다.
- 기존 하드 제약과 충돌하지 않는다.

## Tests
- 문서만 읽고 단계 순서/입출력/중단 조건을 설명할 수 있다.
- 새로운 작업자가 단계별 artifact 없이 다음 단계를 시작하면 규칙 위반임을 즉시 판단할 수 있다.

## Risks
- 단계 수 축소 과정에서 기존 Taskize 의미가 누락될 수 있다.
- artifact 경로/형식이 과도하게 엄격하면 초기 적용 속도가 느려질 수 있다.
