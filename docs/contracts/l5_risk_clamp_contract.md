# L5 Risk Clamp Contract

## Purpose

The L5 Risk Clamp is a diagnostic-only contract for recording how final
exposure research should be capped by risk constraints before any future
runtime gate can review it.

This first pass is documentation and contract only. It does not change selector
behavior, sizing behavior, replay, runtime state, paper order eligibility, live
order permission, broker state, acceptance, or deployment readiness.

## Standing State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN

## Clamp Formula

```text
final_multiplier =
  min(
    raw_combined_multiplier,
    pre_entry_risk_cap,
    liquidity_cap,
    crowding_cap,
    portfolio_cap,
    regime_cap
  )
```

The formula is a diagnostic review contract. It is not a sizing command and it
does not authorize position changes.

## Required Inputs

| Field | Purpose |
| --- | --- |
| `raw_combined_multiplier` | Unclamped diagnostic research multiplier. |
| `pre_entry_risk_cap` | Cap derived from pre-entry risk budget. |
| `liquidity_cap` | Cap derived from exit capacity and liquidity risk. |
| `crowding_cap` | Cap derived from crowding deterioration. |
| `portfolio_cap` | Cap derived from concentration and marginal contribution. |
| `regime_cap` | Cap derived from regime mismatch. |
| `cap_reason_codes` | Human-review reason codes for the binding caps. |
| `source_gap_flags` | Explicit source gaps that block or weaken the clamp. |

## Hard Gates

- Missing cap inputs must block or mark the clamp incomplete; they must not be
  approximated.
- The clamp output is diagnostic-only and cannot create orders.
- The clamp cannot override L6 runtime gates.
- The clamp cannot permit paper order intent or live order permission.
- The clamp cannot mutate broker state or runtime state.
- The clamp cannot change strategy acceptance, deployment readiness, or
  real-capital status.

## Validation Authority

- `GOVERNANCE_HEALTH` for this contract and report closeout.
- Future implementation tests may add `PACKAGE_HEALTH` for arithmetic bounds
  and missing-input behavior only.

PASS means the risk clamp contract preserves the diagnostic risk boundary. PASS
does not mean strategy acceptance, deployment readiness, broker truth
completion, paper-order permission, live-order permission, or real-capital
permission.

