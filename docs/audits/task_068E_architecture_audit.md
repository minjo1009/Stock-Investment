# Task 068-E — Architecture Audit after Research Platform Refactor

## 1. Overall Assessment

- Current status: **PARTIALLY_READY**
- Core strengths (Top 3):
  1. 레이어 분리의 시작점은 명확함 (`execution/risk/analytics/experiments/data` 모듈이 실제로 분리됨).
  2. Golden regression test 도입으로 핵심 성과값(S4) 드리프트를 조기 탐지할 수 있음.
  3. `strategy.conditions`를 단일 조건 엔진으로 두려는 방향은 정합성 관점에서 올바름.
- Critical issues (Top 3):
  1. **`engine_full.py`가 여전히 740 lines의 중앙 오케스트레이터+도메인 로직 혼합체**로 남아 있어 God Object 성격이 잔존.
  2. 실험 계층이 `runner -> engine_full`에 강결합되어 전략/실행/리스크 조합 확장 시 재사용성이 낮음.
  3. 데이터 레이어가 메타/품질 “기초 유틸” 수준이며 stale/bias/feature version governance가 부재.

---

## 2. Layer-by-Layer Audit

### [strategy]
- 잘된 점:
  - `src/strategy/conditions.py`가 breakout/MA/exit(2-bar) 조건을 함수화.
  - `prepare_condition_frame`로 지표 계산 입력 프레임을 표준화.
- 문제점:
  - `selectors.py`는 placeholder 상태로 유니버스 선택 책임이 비어 있음.
  - 조건 계산이 `backtest.indicators`에 의존해 데이터/전략 경계가 완전 분리되진 않음.
- 위험도: **MEDIUM**

### [execution]
- 잘된 점:
  - `src/execution/policies.py`는 policy table + fill 로직이 명확하고 테스트 존재.
- 문제점:
  - 체결 모델이 bar-level 범위(low/high) 가정 중심이라 microstructure 현실성은 제한적.
  - order lifecycle(PENDING/FILLED/EXPIRED 등)는 엔진에서 관리되고 execution 모듈엔 순수 함수만 있음.
- 위험도: **MEDIUM**

### [risk]
- 잘된 점:
  - `src/risk/policies.py`에 break-even/giveback/time-stop 로직이 독립 함수로 있음.
- 문제점:
  - 글로벌 상수(`RISK_MFE_TRIGGER` 등) 기반이라 런타임 실험/병렬 실행 시 오염 가능성.
  - stop/exit state transition의 풍부한 상태 모델은 아직 엔진 중심.
- 위험도: **HIGH**

### [analytics]
- 잘된 점:
  - `metrics.py`, `attribution.py`로 성과 집계와 DD attribution을 분리함.
- 문제점:
  - 지표가 trade-sequence 기준 단순 계산(Sharpe/MDD) 중심이며 sampling/annualization 정교화 미흡.
  - attribution 함수가 `Any` 기반이라 schema drift에 취약.
- 위험도: **MEDIUM**

### [experiments]
- 잘된 점:
  - `ExperimentConfig`, `ExperimentRecord` 구조가 있어 결과 저장 형식이 명확함.
- 문제점:
  - `runner.py`가 `engine_full`에 직접 의존하고 실험 스케줄/재시도/체크포인트 표준 인터페이스가 없음.
  - 비교 실험(복수 scenario 동시, seed/metadata 고정)의 표준 실행 프레임은 아직 약함.
- 위험도: **MEDIUM-HIGH**

### [data]
- 잘된 점:
  - `catalog.py`, `quality.py`로 최소한의 메타/품질 체크 진입점 확보.
- 문제점:
  - stale 데이터 감지, 소스별 신뢰도, survivorship/selection bias, feature version hash 관리가 없음.
  - quality 검증이 파일 단위 단순 통계 중심.
- 위험도: **HIGH**

### [backtest engine]
- 잘된 점:
  - 외부 모듈 호출 구조로 일부 책임 이관 완료.
  - trade metadata 축적 및 validator 연계 시도는 강점.
- 문제점:
  - `engine_full.py`에 여전히 신호 필터링/포지션 상태기계/체결/리스크 반영/메타 생성/CLI까지 집중됨.
  - execution/risk/analytics가 분리됐지만 “호출 orchestration + 핵심 도메인 흐름”이 과도하게 엔진 하나에 묶여 있음.
- 위험도: **HIGH**

---

## 3. Critical Bottlenecks (Top 5)

1. `engine_full.py` 중심 구조 지속
   - 영향: 기능 추가/실험 누적 시 회귀 위험 급증, 변경 영향 범위 예측 어려움
   - 왜 위험한지: 단일 파일 장애가 전략 성과/실행/리스크/메타 전체를 동시에 깨뜨릴 수 있음

2. risk 파라미터의 글로벌 상수 모델
   - 영향: 실험 재현성 저하, 병렬 실행/중단 재개 시 결과 오염 가능
   - 왜 위험한지: 런타임 mutation이 발생하면 동일 config라도 다른 결과를 낼 수 있음

3. experiments 계층의 강결합(`runner -> engine_full`)
   - 영향: 정책 조합 확장 시 엔진 구현 디테일을 계속 알아야 함
   - 왜 위험한지: 실험 프레임워크가 독립 플랫폼으로 성장하기 어려움

4. data governance 미성숙
   - 영향: 백테스트 결과 신뢰성 판단 근거 부족
   - 왜 위험한지: stale/bias/결측 패턴이 성과를 왜곡해도 탐지 체계가 약함

5. 테스트 공백(통합 시나리오 다양성 부족)
   - 영향: 단위 테스트 통과해도 실제 전략 성과/리스크 구조가 깨질 수 있음
   - 왜 위험한지: golden 1점 고정만으로는 정책 확장 회귀를 충분히 막기 어려움

---

## 4. Hidden Risks

- **Golden single-point risk**: S4 단일 golden 통과만으로는 S5/S6 및 레짐별 구조 붕괴를 놓칠 수 있음.
- **Schema drift risk**: `metadata`가 dict[Any] 형태로 넓어 타입 계약 없는 필드 변경이 조용히 누락될 수 있음.
- **Operational illusion risk**: 연구용 엔진 지표와 실제 주문 시스템 상태(DB/orders/fills)의 동기화 검증이 분리돼 있음.
- **Time semantics risk**: entry/exit signal bar vs fill bar 해석이 모듈별로 다르게 쓰일 여지가 아직 있음.

---

## 5. Immediate Next Actions (Top 5)

1. Engine 책임 경계 명세서 작성 (코드 변경 없이 ADR 수준)
   - 기대 효과: 변경 시 영향 범위 명확화, God Object 해체 우선순위 가시화
   - 우선순위: **P0**

2. Risk/Execution 파라미터 주입 계약 표준화 (immutable config contract 설계 문서)
   - 기대 효과: 실험 재현성/병렬 안전성 개선
   - 우선순위: **P0**

3. Golden 확장 계획 수립 (S4 + S5 + S6 + regime split)
   - 기대 효과: silent regression 탐지 범위 확대
   - 우선순위: **P1**

4. Experiment schema 버전 필드 및 run provenance 정의
   - 기대 효과: 결과 비교 가능성/감사 추적성 강화
   - 우선순위: **P1**

5. Data quality governance checklist 정의(stale/missing/bias/version)
   - 기대 효과: 성과 해석 신뢰도 개선, 데이터 이슈 조기 차단
   - 우선순위: **P1**

---

## 6. Final Verdict

- 지금 시스템은 “돈을 넣을 준비가 되었는가?”: **CONDITIONAL (실질적으로는 NO에 가까움)**
- 이유:
  1. 연구 플랫폼으로는 유의미한 진전이 있으나, 엔진 중심 결합/데이터 거버넌스/실험 재현성 계약이 아직 미완성.
  2. 성과 고정 테스트는 시작됐지만 단일 시나리오 중심이라 production-level 리스크 방어로는 부족.
  3. 즉시 실계좌 투입보다는, 구조 감사 후속(Execution Integration Audit + 운영 시뮬레이션) 완료가 선행되어야 함.

