# Task T311 - TBL_A10_LIFECYCLE Strategy Spec

## Phase 2 완료 보고

### 변경 파일
- None

### 추가 파일
- `docs/reports/task_311/task_311_tbl_strategy_spec.md`

### 실행한 테스트
- Spec review against v3 requirements

### 생성된 리포트
- `docs/reports/task_311/task_311_tbl_strategy_spec.md`

### 핵심 결과
- Strategy: `TBL_A10_LIFECYCLE`
- Entry candidate: existing A_10 breakout, confirmed on breakout bar, filled no earlier than next bar.
- Entry features known before entry use shifted values:
  - `ATR_for_entry = ATR(14).shift(1)`
  - `std5_prev = rolling_std(5).shift(1)`
  - `std20_prev = rolling_std(20).shift(1)`
  - `avg_volume_20_prev = volume.rolling(20).mean().shift(1)`
- Breakout quality filter:
  - `std5_prev < std20_prev`
  - `volume_today > avg_volume_20_prev * 1.5`
  - `(close - low) / (high - low) > 0.6`
- R definition:
  - `initial_stop = initial_entry_price - ATR_for_entry * 2.0`
  - `initial_R = initial_entry_price - initial_stop`
  - `initial_R` is fixed and never recalculated after add.
- Lifecycle:
  - `INITIAL_ENTRY`
  - `CONFIRMED_ADD`
  - `PARTIAL_TAKE_PROFIT`
  - `RUNNER`
  - `EXITED`
  - `STOPPED`
- Risk:
  - `max_positions=5`
  - `risk_per_trade_pct=1.0`
  - `max_total_open_risk_pct=5.0`
  - `daily_loss_limit_pct=3.0`, based on `daily_start_equity`
  - `max_symbol_weight_pct=25.0`
  - `max_sector_positions=2`

### Strategy Integrity Check
- R 정의 정상 작동 여부: YES, fixed ATR-based initial R is specified.
- same-bar bias 제거 여부: YES, next-bar only entry is specified.
- expectancy 계산 포함 여부: YES, lifecycle-level R metrics are specified.
- trailing stop 동작 검증: YES, runner trailing is `highest_close - ATR(14) * 3.0`.
- portfolio risk 제한 정상 작동 여부: YES, total risk and sector caps are specified.

### 다음 Phase 진행 가능 여부
- YES

### Blocking Issue
- None
