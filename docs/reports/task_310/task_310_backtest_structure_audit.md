# Task T310 - Backtest Structure Audit

## Phase 1 완료 보고

### 변경 파일
- None

### 추가 파일
- `docs/reports/task_310/task_310_backtest_structure_audit.md`

### 실행한 테스트
- Static repository inspection

### 생성된 리포트
- `docs/reports/task_310/task_310_backtest_structure_audit.md`

### 핵심 결과
- Current full backtest entrypoint: `src/backtest/engine_full.py`
- Capital validation runner: `src/backtest/analysis_capital_backtest_093.py`
- Breakout sensitivity runner: `src/backtest/analysis_breakout_sensitivity_099.py`
- Multi-strategy runner: `src/backtest/analysis_multi_strategy_300.py`
- Breakout condition source: `src/strategy/conditions.py`
- Execution policy source: `src/execution/policies.py`
- Risk policy source: `src/risk/policies.py`
- Metrics source: `src/analytics/metrics.py`
- Report style: task runners write JSON/Markdown under `docs/reports/task_*`

### 현재 엔진의 한계
- Existing `engine_full.py` models a single open position per symbol and does not model add/partial/runner lifecycle state.
- Existing A_10 sensitivity is signal/proxy oriented and does not aggregate partial/final exits by lifecycle.
- Existing metrics are trade-result oriented, so TBL requires explicit lifecycle-level R metrics.

### TBL 구현 시 건드려야 할 최소 파일 목록
- `src/strategy/lifecycle.py`
- `src/backtest/tbl_execution.py`
- `src/backtest/analysis_tbl_314.py`
- `src/backtest/analysis_tbl_robustness_316.py`
- `src/backtest/analysis_tbl_reports_315_317.py`

### 변경하면 안 되는 보호 대상 파일/함수
- `src/backtest/engine_full.py`
- `src/strategy/conditions.py`
- `src/execution/policies.py`
- `src/risk/policies.py`
- Existing `task_084`, `task_093`, `task_099`, `task_300` reports

### Strategy Integrity Check
- R 정의 정상 작동 여부: planned in `src/strategy/lifecycle.py`
- same-bar bias 제거 여부: planned in `src/backtest/tbl_execution.py`
- expectancy 계산 포함 여부: planned in `src/backtest/analysis_tbl_314.py`
- trailing stop 동작 검증: planned in lifecycle tests
- portfolio risk 제한 정상 작동 여부: planned in TBL runner

### 다음 Phase 진행 가능 여부
- YES

### Blocking Issue
- None
