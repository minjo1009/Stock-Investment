# Layer Contracts

## Purpose
- 레이어별 입력/출력/책임/금지사항을 명시해 구현 오해를 줄인다.
- Source of Truth, 실패 처리, 환경 분리 규칙을 계약 수준으로 고정한다.

## Layer Contracts
### 1) Market/Data Layer
- 입력:
- 외부 시세/종목/시장 데이터
- 내부 보조 메타데이터(거래 캘린더, 심볼 매핑)
- 출력:
- 정제된 시장 데이터
- feature snapshot(전략 입력용)
- 책임:
- 데이터 수집, 정제, 정합성 점검, feature 생성
- 금지사항:
- 주문 생성 금지
- 포지션 변경 금지
- 리스크 의사결정 금지

### 2) Strategy Layer
- 입력:
- feature snapshot
- 전략 설정값(룰 파라미터)
- 출력:
- `signal_event`
- 책임:
- 100% 룰 기반 신호 생성
- 환경 독립 전략 판단(동일 전략은 paper/live에서 동일 로직)
- 금지사항:
- broker 호출 금지
- 주문 실행 금지
- 리스크 승인/차단 결정 금지
- 계좌 정보 직접 의존 금지(필요 시 최소 참조만 허용, 의사결정 핵심 의존 금지)

### 3) Risk Layer
- 입력:
- `signal_event`
- `account_snapshot`
- `position_snapshot`
- 리스크 파라미터
- 출력:
- `risk_decision`
- 필요 시 축소된 주문 수량 정보
- 책임:
- 신호 허용/차단/축소 결정
- 하드 블록/소프트 블록 정책 적용
- 금지사항:
- 직접 주문 실행 금지
- 신규 신호 생성 금지
- 브로커 상태 임의 수정 금지

### 4) Execution Layer
- 입력:
- `order_intent`
- `risk_decision`(ALLOW/REDUCE 결과 반영)
- 브로커 연결 설정
- 출력:
- `broker_order`
- `fill_event`
- 동기화된 `position_snapshot` / `account_snapshot`
- 책임:
- KIS API 호출, 주문 제출/정정/취소, 체결 수신, 상태 동기화
- 환경 분기 처리(paper/live)는 이 레이어에서만 수행
- 금지사항:
- 전략 판단 금지
- 리스크 결과 override 금지
- 임의 신호 생성 금지

### 5) Intelligence / Report Layer
- 입력:
- 거래 로그, 체결/포지션/계좌 스냅샷
- 분석 데이터, 리포트 파라미터
- 출력:
- 분석 결과, 리포트, Slack 보고 메시지
- 책임:
- 사후 분석, 설명, 요약, 운영 모니터링 지원
- 금지사항:
- 매매 결정 금지
- 리스크 정책 변경 금지
- 주문 실행 금지

## Source of Truth Policy
- 주문/체결 상태의 진실원: KIS API
- 전략 판단의 진실원: Strategy Layer 내부 룰 계산 결과
- 포지션 상태의 진실원: 브로커 상태 + 내부 동기화 결과
- 내부 저장소는 감사/리플레이/검증을 위한 기록 진실원으로 활용 가능
- 진실원 충돌 시 우선순위:
1. 브로커 체결/주문 상태
2. 동기화된 내부 스냅샷
3. 파생 분석 데이터

## Failure Handling
### Execution failure
- 책임 레이어: Execution Layer
- 기본 반응:
- 제한된 재시도(retry budget)
- 재시도 초과 시 거래 중단 또는 해당 intent BLOCK
- Slack 운영 알림 전송

### Reconcile failure
- 책임 레이어: Execution Layer(동기화) + 운영 보고(Intelligence/Report)
- 기본 반응:
- 불일치 상태 플래그 기록
- 신규 주문 일시 중단(보수적 기본값)
- 수동 확인 필요 알림(Slack)

### Data failure
- 책임 레이어: Market/Data Layer
- 기본 반응:
- 데이터 품질 검증 실패 시 신호 생성 중단
- Strategy 입력 공급 차단(BLOCK 처리)
- 운영 알림 및 원인 데이터 소스 추적

## Environment Separation
- `paper`와 `live`는 데이터, 주문, 로그, 리포트를 완전 분리한다.
- 전략 로직은 동일하게 유지하고, 환경 분기는 Execution Layer에서만 수행한다.
- 모든 상태/로그/리포트는 환경 태그를 포함해야 한다.
- cross-env 집계는 보고 목적의 읽기 전용으로만 허용하며 실행 의사결정 입력으로 금지한다.

## Hard Rules
- Strategy는 broker 호출 금지.
- Execution은 signal 생성 금지.
- Risk는 주문 실행 금지.
- Intelligence는 매매 결정 금지.
- 레이어는 자신의 입력 계약에 없는 필드를 임의 참조하지 않는다.

## Next Design Tasks
- Execution State Machine 상세 정의(Task 후보)
- KIS Adapter 상세 계약 정의(Task 후보)
- Risk Parameter 스키마 및 운영 정책 정의(Task 후보)
- Slippage 모델 정의(Task 후보)

## Acceptance Criteria
- 5개 레이어의 입력/출력/책임/금지사항이 모두 정의되어 있다.
- Source of Truth 정책이 명시되어 있다.
- 실패 처리 흐름(Execution/Reconcile/Data)이 포함되어 있다.
- paper/live 분리 원칙이 계약 수준으로 반영되어 있다.
- `context/architecture/README.md`의 상위 개요와 역할 충돌이 없다.

## Market Snapshot Contract (task 보강)
- Market/Data Layer의 canonical 출력은 `MarketDataSnapshot`이다.
- Strategy Layer의 canonical 입력은 `MarketDataSnapshot`이다.
- Market/Data Layer는 snapshot 생성 시 freshness/completeness 확인 책임을 가진다.
- Market/Data Layer는 signal_event 생성을 금지한다.
- Snapshot 계약 문서는 목표 구조(architecture) 기준이며, 현재 구현 현황(codebase) 문서와 혼동하지 않는다.
- 미결정 사항(후속 task 분리): feature key 표준 목록, session_state 세분화, freshness 임계값, multi-timeframe 지원 범위.

## Market Snapshot Contract (Rework Alignment)
- Market/Data Layer 출력 계약은 `MarketDataSnapshot`으로 고정한다.
- Strategy Layer 입력 계약은 `MarketDataSnapshot`으로 고정한다.
- Market/Data Layer는 snapshot 생성 시 freshness/completeness 검증 책임을 가진다.
- Market/Data Layer는 signal 생성이 금지된다.
- 이 snapshot 계약은 목표 구조(architecture) 문서 기준이며, codebase 현황 문서와 혼동하지 않는다.

## Strategy Input Refinement (Feature Key Contract)
- Strategy Layer 입력 계약은 `MarketDataSnapshot`으로 고정한다.
- `SymbolFeatureSnapshot`는 top-level 핵심값과 `features` 맵을 함께 가진다.
- top-level(`last_price`, `volume`, `turnover`, `spread_bps`)은 raw-ish 공통 핵심값으로 취급한다.
- `features`는 전략용 파생/정규화 값으로 취급한다.
- Strategy 최소 표준 feature key는 `turnover_rank`, `volatility_20d`, `gap_pct`, `momentum_20d`이다.
- 최소 표준 key가 누락된 symbol은 신호 생성 평가에서 제외(SKIP)할 수 있다.
- key 누락이 일부 symbol에 존재해도 snapshot 전체 유효성은 유지될 수 있다.
- 본 계약은 목표 구조(architecture) 계약이며 codebase 현황 문서와 혼동하지 않는다.

## Risk Input Contract (Foundation Refinement)
- Risk Layer 입력 계약은 `RiskInputContext`로 고정한다.
- `RiskInputContext`는 `SignalEvent`, `MarketDataSnapshot`, `AccountSnapshot | None`, `PositionSnapshot | None`을 포함한다.
- `signal`이 없으면 Risk 평가를 호출하지 않는 것이 기본 흐름이다.
- `account`/`position`은 foundation 및 초기 상태에서 `None`을 허용한다.
- market snapshot freshness 및 입력 completeness는 Risk 판단 전제에 영향을 준다.
- Risk Layer 출력은 `RiskDecision`이다.
- Risk Layer는 signal 생성 금지, 주문 실행 금지, broker 상태 임의 수정 금지를 따른다.
- ALLOW/BLOCK/REDUCE 구체 규칙과 completeness policy는 후속 task에서 상세화한다.
