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

## Execution Persistence / State Store
- Purpose: keep a local trace of each run (`trade_runs`), submitted orders (`orders`), and confirmed fills (`fills`).
- Fill source is explicitly stored as one of:
- `ORDER_STATUS`
- `POSITION_DELTA_FALLBACK`
- This layer is minimal tracking for operations; advanced position/PnL/idempotency is a follow-up scope.

## Recent Run Report CLI
- Command: `python -m app.report_recent_runs`
- Optional limit: `python -m app.report_recent_runs --limit 20`
- Show order intent key: `python -m app.report_recent_runs --show-intent-key`
- Position snapshot view: `python -m app.report_recent_runs --positions`
- DB path is read from `TRADING_DB_PATH` (default: `trading.db`).

## Fill Dedupe Policy (Task 030-A)
- Fill inserts use a deterministic dedupe key built from `order_id`, `symbol`, `side`, `filled_quantity`, `fill_price`, and `source`.
- Duplicate inserts are ignored (`INSERT OR IGNORE`) by unique index `uq_fills_dedupe_key`.
- Return status from `record_fill`: `inserted` or `duplicate_ignored`.

## Position Tracking (Task 031)
- `positions`: latest snapshot per symbol (`quantity`, `avg_price`, `updated_at`).
- `position_events`: append-only event trail after each applied fill.
- Current scope is minimal authoritative tracking for operations (not a full portfolio engine).

## Fill Price Truth Source
- Priority 1 (authoritative): broker-reported fill price from execution/order status payloads.
- Priority 2 (temporary fallback): submitted order price when authoritative fill price is unavailable.
- Position `avg_price` quality depends on this truth-source order.

## Execution Loop Foundation (Task 032)
- Command: `python -m app.run_trade_loop`
- Optional: `python -m app.run_trade_loop --max-runs 10`
- Safety guards:
- `TRADING_KILL_SWITCH=true` stops loop before and between runs.
- `TRADING_LOOP_INTERVAL_SEC` controls run interval (minimum enforced: 1 second).
- Single-process lock file: `.trading.lock` (or `TRADING_LOOP_LOCK_PATH`).
- If the process crashes, delete `.trading.lock` manually before restarting.

## Order Idempotency Foundation (Task 033)
- `order_intent_key` is deterministic from: `symbol`, `side`, `intended_price`, `quantity`, `strategy_id`.
- Pre-submit block rule: if same `intent_key` exists with status `SUBMITTED` (or `PENDING`), submit is skipped.
- Optional recent-window guard: set `TRADING_INTENT_RECENT_SEC` (default `0`, disabled).
- Blocked duplicate submits are logged as `[IDEMPOTENT BLOCK] ...`.

## Broker Truth Sync / Reconciliation Foundation (Task 034)
- Submit is guarded by a pre-submit reconciliation check (broker truth vs local state).
- If reconciliation status is `MISMATCH` or `ERROR`, new submit is blocked:
- log: `[RECON BLOCK] local/broker mismatch detected`
- run result: `SKIPPED_RECON_BLOCK`
- Reconciliation persistence:
- `reconciliation_runs` (summary)
- `reconciliation_events` (append-only mismatch details)
- CLI:
- `python -m app.report_recent_runs --show-reconciliation`
- Broker status is conservatively mapped to internal minimal statuses:
- `SUBMITTED`, `FILLED`, `REJECTED`, `FAILED`, `UNKNOWN`

## Operational Hardening (Task 034-A)
- Reconciliation severity:
- `INFO` / `WARN` / `CRITICAL`
- Only `CRITICAL` mismatches block new orders.
- `WARN` events are recorded but do not block.

### Broker Status Mapping Table
| BROKER_STATUS | INTERNAL |
|---|---|
| `OPEN` | `SUBMITTED` |
| `SUBMITTED` | `SUBMITTED` |
| `PENDING` | `SUBMITTED` |
| `WORKING` | `SUBMITTED` |
| `PARTIAL` | `SUBMITTED` |
| `PARTIALLY_FILLED` | `SUBMITTED` |
| `FILLED` | `FILLED` |
| `DONE` | `FILLED` |
| `CANCELLED` / `CANCELED` / `CANCEL` | `CANCELLED` |
| `REJECTED` / `REJECT` / `DENIED` | `REJECTED` |
| `FAILED` / `FAIL` / `ERROR` | `FAILED` |
| (anything else) | `UNKNOWN` |

Rules:
- explicit table mapping first
- unknown values remain `UNKNOWN` (no guess mapping)

### Reconciliation Tuning
- `STATUS_MISMATCH` is CRITICAL only for:
- local `SUBMITTED` vs broker `CANCELLED` / `REJECTED` / `FILLED`
- broker `UNKNOWN` becomes WARN (recorded, no block)
- `FILL_MISMATCH` remains CRITICAL

### Reconciliation Alerting
- Enable with: `TRADING_RECON_ALERT=true`
- On `CRITICAL` mismatch or reconciliation `ERROR`, Slack sends `[RECON ALERT] ...`

### Stale Lock Handling
- lock file now stores JSON with `pid` and `created_at`
- if lock exists and pid is alive: block start
- if lock exists and pid is dead: treat as stale and remove lock
- if lock content cannot be parsed: block conservatively

### Reconciliation CLI
- `python -m app.report_recent_runs --show-reconciliation`
- `python -m app.report_recent_runs --recon-summary`
