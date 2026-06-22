# KIS Fixture Capture Report (Task 075)

## Scope
- Goal: harden cancel/order/fill contracts using fixture-driven tests.
- Environment guard: `KIS_ENVIRONMENT=paper` only.
- Safety guard: no forced order/cancel execution in default capture path.

## Capture Plan
| Case | Endpoint / Source | Trigger | Risk | Capture Status |
|---|---|---|---|---|
| order status pending/open | `/trading/inquire-ccnl` | read-only query | Low | Added fixture (synthetic fallback) |
| order status filled | `/trading/inquire-ccnl` | read-only query | Low | Added fixture (synthetic fallback) |
| fills empty | order status row with `tot_ccld_qty=0` | read-only query | Low | Added fixture (synthetic fallback) |
| fills partial/full | order status row with `tot_ccld_qty>0` | read-only query | Low | Added fixture (synthetic fallback) |
| cancel success | `/trading/order-rvsecncl` | cancel request | Medium | Added fixture (synthetic fallback) |
| cancel rejected/already terminal | `/trading/order-rvsecncl` | cancel request | Medium | Added fixture (synthetic fallback) |
| API/transport error | exception / `rt_cd != 0` | network/API failure | Low | Added fixture (synthetic fallback) |

## Why Synthetic Fallback Was Used
- In this execution session, required KIS credentials were unavailable in environment variables.
- Read-only capture script was added (`scripts/capture_kis_fixtures.py`) and can capture real paper fixtures when credentials are present.

## Sanitization Policy
Removed/masked keys include:
- `authorization`, `appkey`, `appsecret`
- token fields (`token`, `access_token`, `refresh_token`)
- account identifiers (`CANO`, `ACNT_PRDT_CD`, account-like keys)
- `hashkey`

Fixtures keep:
- `rt_cd`, `msg_cd`, `msg1`
- response structural shape (`output`, `output1`, order/fill fields)
- status/quantity/price-like values used for parser and loop tests

## Stored Fixtures
- `tests/fixtures/kis/cancel_success.json` (synthetic)
- `tests/fixtures/kis/cancel_rejected.json` (synthetic)
- `tests/fixtures/kis/order_status_pending.json` (synthetic)
- `tests/fixtures/kis/order_status_filled.json` (synthetic)
- `tests/fixtures/kis/fills_empty.json` (synthetic)
- `tests/fixtures/kis/fills_partial_or_full.json` (synthetic)
- `tests/fixtures/kis/error_transport_or_api.json` (synthetic)

## Contract Hardening Applied
- Fixture-driven parser contract tests added in `tests/test_kis_cancel_contract.py`.
- Cancel loop fixture integration scenarios added in `tests/test_cancel_loop.py`.
- Parser safety strengthened in `src/integration/kis_client.py` for malformed numeric fields.

## Remaining Gaps
- At least one real KIS paper fixture still needs capture once credentials are present.
- Real broker response diversity (exchange/product/time windows) not yet sampled.

## Next Actions
1. Set paper credentials and run:
   - `python scripts/capture_kis_fixtures.py --read-only --symbol AAPL`
2. Replace highest-priority synthetic fixtures with real sanitized captures:
   - `order_status_pending`, `order_status_filled`, `fills_empty`
3. Re-run full suite and lock fixture metadata (`real_capture=true`) for captured files.
