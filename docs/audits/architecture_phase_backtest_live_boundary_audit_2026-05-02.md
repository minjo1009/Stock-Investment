# Architecture / Phase / Backtest-Live Boundary Audit (2026-05-02)

## 1) Audit Scope and Verdict

- Scope:
  - Architecture intent vs implementation mapping
  - Phase documents vs actual runtime/backtest progress
  - Backtest and live-trading mingle/separation boundary
- Evidence base:
  - `docs/architecture/canonical_architecture.md`
  - `phases/phase-00-project-operating-system.md`, `phases/phase-01-repository-foundation.md`, `phases/phase-02-context-inventory.md`
  - `src/backtest/engine.py`, `src/backtest/engine_full.py`
  - `src/app/task_089_market_data_signal_refresh.py`, `src/app/run_trade_once.py`
  - `src/state/store.py`
  - `docs/contracts/mapping_contract_execution_backtest.md`, `docs/contracts/execution_state_contract.md`

### Final verdict

- Conclusion: **partial coupling (부분 결합)**.
- Reason:
  - Backtest engine is cleanly separated from direct broker API calls.
  - Runtime signal generation intentionally reuses backtest logic.
  - A single default DB path (`trading.db`) is used across runtime signal snapshots and live execution state, creating state-mixing risk without explicit environment-level DB isolation.

---

## 2) Intended vs Implemented Architecture

| Layer | Intended responsibility | Must not do (intent) | Implemented location / evidence | Assessment |
|---|---|---|---|---|
| `backtest` | Historical simulation, analysis | Depend on live broker adapter | `src/backtest/engine.py`, `src/backtest/engine_full.py` do not import `integration.kis_client` | Green |
| `broker` (`integration`) | Broker auth/client/slack adapters | Own strategy/risk decision | `src/integration/kis_client.py`, `src/integration/kis_auth_manager.py` | Green |
| `apps` (`src/app`) | Orchestration and operation scripts | Own core domain rules | `src/app/run_trade_once.py`, `src/app/task_089_market_data_signal_refresh.py` orchestrate runtime flow | Yellow (intentional operational coupling exists) |
| `execution` + `state` | Order lifecycle + durable execution state | Compute alpha strategy | `src/execution/*`, `src/state/store.py` manage orders/fills/reconciliation | Green |
| `strategy/risk` | Signal generation and risk decision | Direct broker execution | `src/strategy/*`, `src/risk/*`; broker call path is in app/integration layers | Green |

Key mismatch against strict canonical ideal:
- `src/app/task_089_market_data_signal_refresh.py` imports both `backtest.engine_full` and `integration.kis_client` in one operational script. This is acceptable as orchestration, but it is a coupling hotspot and should remain explicitly managed.

---

## 3) Phase Status vs Code Progress

### Documented operating-system phases

- Phase 00: project operating system rules and governance bootstrap
- Phase 01: repository foundation and execution/test entrypoint conventions
- Phase 02: context inventory and indexing

### Actual code progress (runtime features)

- Live/paper execution lifecycle exists:
  - `run_trade_once`, `run_trade_loop`, reconciliation, cancel loop, idempotency, fill correction
- Backtest engines and many analysis tracks exist:
  - quick/full backtest engines and multiple analysis scripts
- Runtime signal refresh pipeline exists:
  - market quote ingestion + indicator snapshot persistence + live candidate selection

### Gap summary

- Operating-system phases are documented as foundational/governance steps, while the repository already contains advanced runtime/backtest implementation.
- This is not a functional bug, but phase docs and implementation maturity are currently not aligned in the same timeline narrative.

---

## 4) Backtest-Live Boundary Audit

### Q1. Does backtest engine directly call live broker API?

- Finding: **No direct call found**.
- Evidence:
  - `src/backtest/engine.py`, `src/backtest/engine_full.py` use backtest/strategy/risk/portfolio modules but no `KISClient` import.
- Assessment: **Green (normal separation)**.

### Q2. Does live execution depend on backtest artifacts?

- Finding: **Yes, partially**.
- Evidence:
  - `src/app/run_trade_once.py` reads `indicator_snapshots` and uses runtime candidate selection logic.
  - `src/app/task_089_market_data_signal_refresh.py` writes `indicator_snapshots` and builds them using backtest-derived logic (`backtest.engine_full`).
- Assessment: **Yellow (intentional operational coupling)**.
- Interpretation:
  - This is a design choice to keep runtime signal policy aligned with backtest policy.
  - Coupling is acceptable if controlled and clearly versioned.

### Q3. Is DB sharing limited to market/signal level, or mixed with execution state?

- Finding: **Mixed in same default DB**.
- Evidence:
  - `task_089` writes `indicator_snapshots` to `TRADING_DB_PATH` default `trading.db`.
  - `run_trade_once` and `state.store` use same DB path for `trade_runs`, `orders`, `fills`, `positions`, reconciliation tables.
- Assessment: **Red (risk coupling)**.
- Risk:
  - Backtest/runtime-signal artifacts and live execution state coexist in one DB file by default.
  - Environment misconfiguration can cause cross-context contamination and operational misreads.

### Q4. Does live API failure affect standalone backtest workflow?

- Finding: **Backtest engines themselves are independent; runtime signal refresh is not**.
- Evidence:
  - Backtest engines can run from local OHLCV CSV without KIS.
  - `task_089` path requires KIS for quote refresh; if KIS init fails, it emits a failure report.
- Assessment: **Green for engine-only backtest, Yellow for runtime-signal workflow**.

---

## 5) Scenario Checklist Result

### Scenario A: Standalone backtest should not require KIS auth/network

- Result: **Pass** (based on import/runtime path inspection).
- Note:
  - Backtest engine reads local data loader path and does not import broker client.

### Scenario B: `run_trade_once` fail-safe when `indicator_snapshots` is absent

- Result: **Conditional fail-safe only**.
- Behavior:
  - If `indicator_snapshots` table exists and no candidate: `SKIPPED_NO_SIGNAL`.
  - If table does not exist: runtime mode is inactive and execution continues with fallback defaults (symbol/side), not an explicit skip.
- Assessment: **Risky default for strict no-signal discipline**.

### Scenario C: Single DB (`TRADING_DB_PATH`) mixing risk

- Result: **Risk confirmed**.
- Behavior:
  - Signal snapshot tables and live order/fill tables share same default DB.
- Assessment: **High-priority operational risk**.

---

## 6) Priority Risks and Recommendations

### P1 (High): DB boundary ambiguity (Red)

- Risk:
  - Shared default DB for backtest-like signal artifacts and live execution lifecycle.
- Recommendation:
  - Enforce environment-specific DB path policy (`paper/live/backtest` separated DB files).
  - Add startup guard that rejects live run when DB naming/env contract is violated.

### P2 (Medium): `run_trade_once` fallback execution when runtime snapshot table is missing

- Risk:
  - Accidental trade path can proceed without explicit runtime signal pipeline readiness.
- Recommendation:
  - Add strict mode flag (default-on for live) requiring `indicator_snapshots` availability and freshness.
  - If missing, return `SKIPPED_NO_SIGNAL` (or explicit `FAILED_PRECONDITION`) instead of fallback symbol execution.

### P3 (Medium): Coupling hotspot in `task_089` (backtest logic + broker integration in one script)

- Risk:
  - Future changes can unintentionally blur domain boundaries.
- Recommendation:
  - Keep current behavior but document as intentional adapter layer.
  - Optional refactor later: split into `runtime_signal_adapter` module and keep `app` script orchestration thin.

---

## 7) Contract Consistency Summary

- `docs/contracts/mapping_contract_execution_backtest.md` and `docs/contracts/execution_state_contract.md` provide a good semantic bridge for execution/backtest mapping.
- Main gap is not contract definition quality, but **runtime storage and precondition enforcement** for boundary safety.

---

## 8) One-line Executive Decision

- Current design is **not fully separated** and should be treated as **partial coupling with guard requirements**; immediate action should focus on DB isolation policy and strict runtime precondition checks.
