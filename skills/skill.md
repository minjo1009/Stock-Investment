# Project Operating System

## Purpose
- 이 문서는 저장소 전체의 작업 운영체계를 정의하는 헌법이다.
- 인간과 AI는 동일한 규칙, 동일한 용어, 동일한 변경 절차를 따른다.
- 모든 구현, 문서 수정, 보고는 이 문서의 계층과 통제 규칙을 따른다.

## Scope
- 작업 계층 정의
- 표준 작업 흐름 정의
- 변경 통제 규칙 정의
- 산출물과 완료 판정의 기본 원칙 정의

## Core Principles
- 모든 매매 의사결정은 룰 기반으로 정의한다.
- LLM은 분석, 리포트, 우선순위 보조 역할만 수행한다.
- 백테스트는 룰 기반 only로 운영하며 LLM을 의사결정 경로에 포함하지 않는다.
- KR과 US는 전략, 유니버스, 세션, 체결 가정을 분리한다.
- 자동 운영, 긴급중지, 킬스위치, Slack 기반 명령 체계를 수용할 수 있도록 설계한다.
- 장애복구, 리스크통제, 감사추적성, 운영관제, 유지보수 체계를 향후 수용할 수 있어야 한다.
- 모든 변경은 phase 또는 task 체계 안에서 관리한다.
- 직접적인 무규칙 수정은 금지한다.
- silent refactor는 금지한다.
- 문서 또는 요구사항이 불명확하면 STOP 한다.

## Working Hierarchy
- `skill.md`: 프로젝트 작업 헌법이다. 상위 원칙과 작업 계층을 정의한다.
- `prompts/phase-create.md`: 실행계획인 phase의 생성 규격을 정의한다.
- `prompts/task-create.md`: 구현단위인 task의 생성 규격을 정의한다.
- `phases/*.md`: 특정 목표를 위한 phase 실행계획을 정의한다.
- `tasks/*.md`: 개별 구현, 수정, 검증 단위를 정의한다.
- 구현 코드와 보고 문서는 승인된 phase/task의 범위 안에서만 변경한다.

## Standard Workflow
- Clarify: 요구사항과 제약을 확인한다.
- Context Gather: 근거 문서와 현재 코드 상태를 수집한다.
- Plan: phase가 필요한지 판단하고 상위 실행계획을 명시한다.
- Taskize: 구현 단위를 task로 분해한다.
- Implement: 승인된 범위 내에서 구현, 검증, 보고를 수행한다.
- Report: 산출물, 검증 결과, 리스크, 다음 행동을 남긴다.

## Read Order Before Work
- `skills/skill.md`
- 관련 `phases/*.md`
- 관련 `tasks/*.md`
- `context/README.md` 및 필요한 근거 문서
- 대상 코드와 테스트

## Change Control Rules
- 모든 변경은 phase 또는 task에 연결되어야 한다.
- phase 없이 진행되는 대규모 변경은 금지한다.
- task 없이 진행되는 직접 수정은 금지한다.
- `skills/skill.md`, `prompts/task-create.md`, `prompts/phase-create.md`는 고위험 문서다.
- 고위험 문서 수정은 별도 task를 생성하고 영향 범위를 검토해야 한다.
- Phase 0 문서도 임의 수정하지 않는다.
- 변경 사유, 범위, 완료 기준, 검증 방법이 없는 수정은 금지한다.

## Output Contract
- 모든 작업 결과는 변경 파일, 요약, 검증, 리스크, 다음 행동을 포함한다.
- 구현 산출물은 어떤 phase/task에 속하는지 추적 가능해야 한다.
- 문서는 선언형 문장으로 작성하고, 모호한 표현을 피한다.

## Quality Gate
- 문서 또는 코드 변경은 목적과 범위가 명확해야 한다.
- acceptance criteria와 검증 방법이 존재해야 한다.
- 문서 간 역할 중복이 없어야 한다.
- 상위 원칙과 하위 실행 문서 간 참조 관계가 유지되어야 한다.
- 룰 기반 매매 원칙과 LLM 보조 원칙을 훼손하지 않아야 한다.

## STOP Rules
- 요구사항이 phase인지 task인지 구분되지 않으면 STOP 한다.
- 근거 없이 전략, 체결 가정, 리스크 통제를 변경하려 하면 STOP 한다.
- 영향 범위를 설명할 수 없는 고위험 문서 수정은 STOP 한다.
- task 또는 phase 없이 직접 수정하라는 요청은 STOP 한다.
- context가 부족해 사실과 해석을 구분할 수 없으면 STOP 한다.

## Directory Convention
- `skills/`: 프로젝트 작업 헌법과 상위 운영 규칙을 둔다.
- `prompts/`: phase/task 생성 규격을 둔다.
- `phases/`: 상위 실행계획 문서를 둔다.
- `tasks/`: 구현 단위 문서를 둔다.
- `templates/`: phase/task 실사용 템플릿을 둔다.
- `context/`: 근거 중심의 제품, 아키텍처, 코드베이스, 워크플로 문서를 둔다.
- `src/`: 구현 코드를 둔다.
- `tests/`: 검증 코드를 둔다.

## Lifecycle
- 새 요구가 들어오면 먼저 phase 필요 여부를 판단한다.
- 복수 task가 필요한 변화면 phase를 만든다.
- 단일 목적 구현이면 task를 만든다.
- 구현 후 결과를 보고하고, 후속 phase 또는 task로 handoff 한다.
- 문서 체계 자체의 변경도 동일하게 task 기반으로 관리한다.
