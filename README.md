# 외국주식 퀀트트레이딩

이 저장소는 외국주식 퀀트트레이딩 프로젝트를 위한 작업 공간이다.

## 작업 방식
- 프로젝트 작업 운영체계는 `skills/skill.md`를 기준으로 한다.
- phase 생성 규격은 `prompts/phase-create.md`를 따른다.
- task 생성 규격은 `prompts/task-create.md`를 따른다.
- 상위 실행계획은 `phases/`에, 구현 단위는 `tasks/`에 기록한다.
- 템플릿은 `templates/`를 사용한다.
- 근거 문서는 `context/`에 축적한다.

## 원칙
- 매매 의사결정은 룰 기반으로 관리한다.
- LLM은 분석, 리포트, 우선순위 보조 역할만 수행한다.
- 모든 변경은 phase/task 체계 안에서 관리한다.
- 무규칙 직접 수정과 silent refactor는 금지한다.

## 현재 상태
- Phase 0은 Project Operating System 부트스트랩 단계다.
- 이후 `Phase 01: Repository Foundation` 또는 `Phase 02: Context Inventory`로 이어질 수 있다.

## KIS Token Cache / Auth Manager
- Why: avoid issuing a new KIS access token on every run and reduce auth-rate-limit failures.
- Default behavior:
- reuse cached token first
- issue a new token only when cache is missing or near expiry
- cache file: `.kis_token_cache.json` (git-ignored)
- Rate-limit handling:
- if token issuance is rate-limited and a still-valid cached token exists, reuse cache
- if no valid cached token exists, fail fast with explicit error
- Environment:
- cache is validated against `KIS_ENVIRONMENT`
- Run note:
- if module import fails on local shell, run with `PYTHONPATH=src`
