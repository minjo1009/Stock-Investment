# Phase 01: Repository Foundation

## Objective
- 구현 단계 진입 전, 저장소의 실행/검증/아티팩트 기본 골격을 고정한다.
- 5단계 하네스(Clarify, Context Gather, Plan, Generate, Evaluate)를 저장소 운영 단위에 연결한다.
- 신규 작업자가 문서만으로 `run -> evaluate` 1사이클을 재현 가능한 상태를 만든다.

## Why This Phase Exists
- Phase 00은 운영체계 정의, Phase 02는 근거 인벤토리 구축을 완료했다.
- 현재는 Foundation skeleton 코드가 존재하지만 실행 표준, 테스트 진입점, artifact 운영 규약이 분산되어 있다.
- Repository Foundation을 명시하지 않으면 후속 구현에서 task 경계와 검증 루프가 흔들릴 위험이 크다.

## Entry Conditions
- `skills/skill.md` 및 `context/workflow/execution-rules.md`의 5단계 하네스 규칙이 반영된 상태.
- `context/` 4분류 문서(product, architecture, codebase, workflow)가 존재하는 상태.
- 본 phase는 저장소 기반 정비 단계이며 전략/주문 실행 로직 확장을 포함하지 않는다는 합의가 있는 상태.

## Scope
- 실행 진입점 표준 문서화
- 테스트 진입점 및 최소 검증 루프 표준화
- task 단위 artifact 디렉터리/파일 규약 도입
- 단계별 sub-agent handoff 템플릿 도입
- 운영 환경(paper/live) 분리 전제와 설정 규약 문서화

## Out of Scope
- 전략 신호 생성 로직 구현
- 리스크 정책 알고리즘 구현
- 브로커 API 실연동 및 주문 실행 자동화
- CI/CD 파이프라인 구축
- 실거래 운영 스케줄러 구현

## Deliverables
- `phases/phase-01-repository-foundation.md`
- `tasks/task-011-runtime-entrypoint-standardization.md`
- `tasks/task-012-test-entrypoint-standardization.md`
- `tasks/task-013-artifact-layout-convention.md`
- `tasks/task-014-subagent-handoff-template.md`
- `tasks/task-015-environment-config-convention.md`

## Task Inventory
- Task 011: 실행 진입점 표준화(실행 명령, 입력, 종료 계약)
- Task 012: 테스트 진입점 표준화(단위/통합/리플레이 최소 검증 루프)
- Task 013: artifact 디렉터리/네이밍 규약 도입
- Task 014: 단계별 sub-agent handoff 템플릿 도입
- Task 015: 환경/설정 규약 문서화(paper/live 분리 전제)

## Execution Order
1. Task 013으로 artifact 경로/형식을 먼저 고정한다.
2. Task 014로 단계별 handoff 템플릿을 확정한다.
3. Task 011로 실행 진입점을 표준화한다.
4. Task 012로 검증 진입점을 표준화한다.
5. Task 015로 환경/설정 규약을 잠그고 phase 종료 판정을 수행한다.

## Exit Criteria
- Foundation 관련 task(011~015)가 모두 작성되고 실행 가능한 수준의 acceptance criteria/tests를 가진다.
- 5단계 하네스 결과물을 저장할 artifact 규약이 문서화되어 있다.
- 실행/검증 표준이 문서 기준으로 재현 가능하다.
- paper/live 분리 원칙이 실행 및 검증 규약과 충돌하지 않는다.
- 다음 구현 phase가 즉시 시작 가능한 handoff 기준이 준비된다.

## Risks
- 실행 진입점과 테스트 진입점이 불일치하면 허위 완료 판정이 발생할 수 있다.
- artifact 규약이 약하면 단계별 추적성과 감사 가능성이 저하된다.
- 환경 분리 규약이 늦게 고정되면 이후 구현에서 cross-env 결합이 발생할 수 있다.
- context 문서와 현재 코드 상태 간 불일치가 남아 있으면 계획 품질이 떨어질 수 있다.

## Handoff
- 다음 구현 phase는 본 phase의 Task 011~015 산출물을 입력으로 사용한다.
- 모든 후속 task는 `artifacts/<task-id>/<stage>.md` 규약을 따른다.
- 기능 구현 착수 전, 실행/검증 루프가 문서 기준으로 재현되는지 Evaluate 단계에서 확인한다.
