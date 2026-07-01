# T600-0 Position Lifecycle Contract

Last updated: 2026-06-03

## Decision

This contract fixes the minimum execution lifecycle required before strategy acceptance review can begin.

Current blocker:

```text
BUY
↓
END
```

Target:

```text
BUY
↓
OPEN POSITION
↓
EXIT / TRIM / CLOSE
↓
REALIZED LIFECYCLE
```

This is a design contract only. It does not implement execution logic.

## Ownership

| Field | Value |
|---|---|
| Task | T600-0 |
| Owner | 주은 |
| Team | Execution & Risk |
| Reviewer | 필수 / 중훈 |
| Priority | P0 |
| Program blocker | `P0_EXIT_LIFECYCLE` |
| Strategy status | `NOT_ACCEPTED` |
| Deployment status | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |

## State Machine

```text
NEW
↓
OPEN
↓
PARTIAL_EXIT
↓
CLOSED
```

### State Definitions

| State | Meaning | Entry Condition | Exit Condition |
|---|---|---|---|
| `NEW` | Position intent exists but no broker-truth entry fill has opened exposure | candidate/order intent exists | exact broker-truth entry fill creates positive position quantity |
| `OPEN` | Position has positive open quantity | entry fill is accepted with exact `entry_fill_id` | exit or trim order is submitted and accepted |
| `PARTIAL_EXIT` | Position quantity has been reduced but remains positive | exact broker-truth exit/trim fill reduces position quantity | additional exit closes position or new trim leaves it partial |
| `CLOSED` | Position quantity is zero and realized PnL is final | exact broker-truth exit fill closes position | terminal state |

## Allowed Transitions

| From | To | Required Evidence |
|---|---|---|
| `NEW` | `OPEN` | exact `entry_order_id`, exact `entry_fill_id`, entry fill timestamp, quantity, price |
| `OPEN` | `PARTIAL_EXIT` | exact `exit_order_id`, exact `exit_fill_id`, exit type `TRIM`, reduced quantity |
| `OPEN` | `CLOSED` | exact exit order/fill, exit type `STOP`, `TAKE_PROFIT`, or `TIMEOUT` |
| `PARTIAL_EXIT` | `PARTIAL_EXIT` | exact additional trim fill with remaining quantity above zero |
| `PARTIAL_EXIT` | `CLOSED` | exact final exit fill reduces remaining quantity to zero |

Forbidden transitions:

- `NEW -> CLOSED`
- `OPEN -> NEW`
- `CLOSED -> OPEN`
- any transition using symbol/date/price/time proximity instead of exact IDs

## Exit Types

| Exit Type | Meaning | Required Trigger Evidence |
|---|---|---|
| `STOP` | Hard stop loss exit | stop rule, current price, threshold, timestamp |
| `TAKE_PROFIT` | Profit-taking exit | take-profit rule, current price, threshold, timestamp |
| `TIMEOUT` | Max holding time exit | entry time, current time, max hold rule |
| `TRIM` | Partial position reduction | trim rule, trim quantity, remaining quantity |

## Required Table

Table name:

```sql
position_lifecycle
```

Required columns:

```sql
position_id
symbol
entry_order_id
entry_fill_id
exit_order_id
exit_fill_id
entry_time
exit_time
holding_minutes
realized_pnl
exit_reason
```

## Column Contract

| Column | Required | Type Intent | Rule |
|---|---:|---|---|
| `position_id` | yes | stable text ID | unique lifecycle ID; must not be inferred from symbol/date/price proximity |
| `symbol` | yes | ticker text | broker/order/fill symbol |
| `entry_order_id` | yes | broker order ID | exact entry order ID |
| `entry_fill_id` | yes | broker fill ID | exact entry fill ID |
| `exit_order_id` | required when exited | broker order ID | exact exit/trim order ID |
| `exit_fill_id` | required when exited | broker fill ID | exact exit/trim fill ID |
| `entry_time` | yes | timestamp | broker-truth entry fill timestamp |
| `exit_time` | required when exited | timestamp | broker-truth exit/trim fill timestamp |
| `holding_minutes` | required when exited | numeric | computed from exact entry and exit timestamps |
| `realized_pnl` | required when closed | numeric | realized PnL only; proxy PnL forbidden |
| `exit_reason` | required when exited | enum text | one of `STOP`, `TAKE_PROFIT`, `TIMEOUT`, `TRIM` |

## Acceptance

T600-0 passes when this document is approved as the execution lifecycle contract.

Implementation acceptance for T600-1 is not granted by this document. T600-1 must prove:

- SELL fills exist.
- `position_lifecycle` rows are populated from exact broker-truth order/fill IDs.
- Closed positions have `realized_pnl`.
- `TRIM` rows can reduce quantity without closing the position.
- No proxy PnL enters realized lifecycle reporting.

## Immediate Fail Conditions

- SELL fills equal 0.
- `realized_pnl` is blank for closed positions.
- `exit_order_id` or `exit_fill_id` is inferred.
- Symbol/date/price/time proximity is used to close a lifecycle.
- Proxy PnL is reported as realized PnL.

## Validation Placeholder

The design-stage validation command is:

```powershell
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
```

The implementation-stage validation command must be added in T600-1.
