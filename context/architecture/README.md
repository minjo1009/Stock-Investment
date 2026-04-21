# Architecture Context Index

## 목적
- 구현 이전에 상위 아키텍처 경계와 책임 분리를 명확히 한다.
- Product 요구를 구현 가능한 구조 규칙으로 변환하는 기준을 제공한다.

## 포함할 문서 유형
- 아키텍처 원칙(5계층, KR/US 분리, 책임 분리)
- 계층별 책임/입출력 경계
- Strategy/Risk/Execution/Position Engine 분리 규칙
- Hard Block/Soft Block 정책 위치
- 이벤트 기반 + 보조 폴링 운영 전제

## 상세 계약 문서
- 도메인 객체 정의: `context/architecture/domain-model.md`
- 레이어 계약 정의: `context/architecture/contracts.md`

## 작성/관리 규칙
- 실제 클래스/함수 구현 상세는 포함하지 않는다.
- Product 문서의 요구를 위반하지 않는 상위 구조만 정의한다.
- Codebase 현황과 분리해서 “목표 구조”를 기술한다.
- 변경 시 영향 범위와 미결정 사항을 함께 기록한다.

## 연계
- 상위 인덱스: `context/README.md`
- 관련 분류: `context/product/README.md`, `context/codebase/README.md`
