# Phase 00: Project Operating System

## Objective
- 프로젝트 작업 운영체계를 저장소 루트에 부트스트랩한다.
- 인간과 AI가 동일한 규칙으로 phase와 task를 생성, 실행, 보고할 수 있는 상태를 만든다.
- 다음 단계의 Repository Foundation 또는 Context Inventory phase로 handoff 가능한 기반을 만든다.

## Why This Phase Exists
- 현재 저장소에 작업 헌법, phase 규격, task 규격, 템플릿, context 운영 원칙이 없으면 변경이 임의적으로 흩어진다.
- 운영 문서의 역할이 겹치면 AI와 인간 모두 해석 오류를 낸다.
- Phase 0은 트레이딩 기능 구현이 아니라 작업 운영체계를 정착시키는 도입 phase다.

## Entry Conditions
- 저장소 루트에 Phase 0 문서를 배치할 수 있어야 한다.
- 기존 트레이딩 로직, 브로커 코드, 전략 코드, 테스트 로직은 이번 phase 범위 밖으로 유지한다.
- 상위 원칙으로 룰 기반 매매, LLM 보조 역할, 변경관리 통제를 수용한다.

## Scope
- 운영 헌법 문서 작성
- phase 생성 규격 작성
- task 생성 규격 작성
- 실사용 템플릿 작성
- context 디렉터리 운영 원칙 작성
- 루트 최소 안내 문서 작성

## Out of Scope
- 실제 트레이딩 기능 구현
- 브로커 연동 변경
- 전략 로직 변경
- 백테스트 로직 변경
- 운영 스케줄러, Slack 명령, 킬스위치의 실제 구현

## Deliverables
- `skills/skill.md`
- `prompts/task-create.md`
- `prompts/phase-create.md`
- `templates/task-template.md`
- `templates/phase-template.md`
- `context/README.md`
- 루트 `README.md`

## Task Inventory
- Task 00-01: 프로젝트 작업 헌법 정의
- Task 00-02: task 생성 규격 정의
- Task 00-03: phase 생성 규격 정의
- Task 00-04: task/phase 템플릿 작성
- Task 00-05: context 운영 원칙 정의
- Task 00-06: 루트 진입 문서 정비
- Task 00-07: 문서 간 참조, 계층, 종료조건 검증

## Execution Order
- 먼저 `skills/skill.md`를 작성해 상위 운영 원칙을 고정한다.
- 다음으로 `prompts/task-create.md`와 `prompts/phase-create.md`를 작성해 하위 생성 규격을 분리한다.
- 다음으로 `templates/`와 `context/README.md`를 작성해 실사용 기반을 만든다.
- 마지막으로 루트 `README.md`와 전체 연결 관계를 검증한다.

## Exit Criteria
- 핵심 문서 4종의 역할이 서로 겹치지 않는다.
- `skill.md` -> prompt 문서 -> phase 문서 -> template 문서의 연결이 명시된다.
- context 폴더의 목적, 분류, 읽기 우선순위가 정의된다.
- 모든 변경이 phase/task 체계로 관리된다는 원칙이 문서에 반영된다.
- 이번 phase가 트레이딩 기능 구현 phase가 아니라는 점이 명시된다.
- 다음 단계로 `Phase 01: Repository Foundation` 또는 `Phase 02: Context Inventory`를 시작할 수 있다.

## Risks
- 상위 문서가 과도하게 상세하면 하위 문서와 책임이 겹친다.
- task와 phase 경계가 모호하면 이후 변경 통제가 무너진다.
- context 운영 원칙이 약하면 AI가 사실과 해석을 혼동할 수 있다.
- 고위험 문서의 임의 수정이 허용되면 운영체계 신뢰도가 떨어진다.

## Handoff
- `Phase 01: Repository Foundation`으로 이어질 경우 저장소 구조, 기본 실행 진입점, 검증 진입점을 정리한다.
- `Phase 02: Context Inventory`로 이어질 경우 product, architecture, codebase, workflow 근거 문서를 수집하고 분류한다.
- 이후 모든 구현 phase는 본 phase에서 도입한 규격에 따라 task inventory와 exit criteria를 먼저 명시한다.
