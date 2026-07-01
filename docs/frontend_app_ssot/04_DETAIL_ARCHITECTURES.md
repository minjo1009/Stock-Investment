# Detail Architectures

## Candidate Detail

Primary question: should this candidate progress in lifecycle?

Required six sections:

- `Decision Summary`: current candidate state and authority.
- `Thesis / Logic`: why the candidate exists.
- `Validation / Readiness`: split/OOS, leakage, cost/slippage, and gate status.
- `Evidence`: source-backed facts and provenance.
- `Risk`: blockers, stale sources, unknowns, and invalidation flags.
- `Next Action`: read-only next engineering or review action.

## Position Detail

Primary question: is the holding thesis still valid and sized correctly?

The surface must separate broker/account truth from local runtime records and must show reconciliation state.

## Chain Detail

Primary question: what path led from source evidence to runtime decision?

The surface must preserve L0 through L7 provenance and show missing layer evidence as blockers.

## Risk Detail

Primary question: which exposures, limits, kill-switches, stale sources, and blockers matter now?

The surface must show kill-switch/control-state evidence and must not present green status when source gates are closed.

## Order Detail

Primary question: is the order purpose, state, and execution quality justified?

Current state is read-only. Broker mutation and local order creation controls remain disabled unless future operating documents explicitly change permission.

