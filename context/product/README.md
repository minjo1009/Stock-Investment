# Product Context Index

## 목적
- Product 관점의 사실/합의를 구조화해 구현 범위 오해를 방지한다.
- 목표와 비목표를 분리해 설계·구현의 경계를 고정한다.

## 포함할 문서 유형
- 프로젝트 목표와 성공 조건
- 범위/비범위 정의
- MVP 정의(초기 전략, 시장 범위, 운영 정책)
- 운영 제약(완전 자동 운영, Slack 명령, LLM 역할 제한)
- 리스크 통제·감사 추적·운영 관제 수용 조건

## 작성/관리 규칙
- 전략 제안이나 구현 코드는 포함하지 않는다.
- 사실과 미결정 사항을 분리한다.
- Architecture 문서와 책임이 겹치지 않게 제품 요구 중심으로 기술한다.
- 변경 시 관련 Task 문서를 먼저 정의한다.

## 연계
- 상위 인덱스: `context/README.md`
- 관련 분류: `context/architecture/README.md`, `context/workflow/README.md`
