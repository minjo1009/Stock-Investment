# L5 Exit Score Contract

## Purpose

The L5 Exit Score is a diagnostic-only policy research contract for explaining
why a position should remain under review, receive no add, be reduced for human
review, be exited for human review, or stay blocked.

It is not an order generator. It cannot create paper or live order intent and
cannot change selector, sizing, broker, runtime, acceptance, or deployment
state.

## Standing State

- Strategy: NOT_ACCEPTED
- Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Real Capital: FORBIDDEN

## Inputs

- L4 thesis validity and invalidation state.
- L5 diagnostic policy context.
- Source gaps and blocker flags.
- Alpha decay, crowding, liquidity, regime, thesis failure, and price extension
  diagnostic factors when available.

Missing inputs remain source gaps or blocked factors. They must not become
bearish evidence by approximation.

## Score Formula

```text
ExitScore =
  25 * AlphaDecayRisk
+ 20 * CrowdingDeterioration
+ 15 * LiquidityDeterioration
+ 15 * RegimeBreakRisk
+ 15 * ThesisFailureRisk
+ 10 * PriceExtensionRisk
```

All component values are bounded from 0 to 1 before weighting. The final score
is bounded from 0 to 100.

## Output States

| State | Meaning |
| --- | --- |
| `hold` | Exit pressure is low. Review continues. |
| `no_add` | Thesis may remain reviewable, but additional exposure is blocked. |
| `reduce_review` | Human reduction review is required. |
| `exit_review` | Human exit review is required. |
| `blocked_review` | Critical source gap, invalid input, or governance blocker prevents scoring. |

## Hard Gates

- The score is diagnostic policy research only.
- `exit_review` is not a sell order.
- `reduce_review` is not a sizing directive.
- `hold` is not a permission to add, re-risk, or keep exposure.
- Critical source gaps must produce `blocked_review`.
- The score must not emit `PolicyAction` objects directly in this first pass.
- The score must not create order intent, paper permission, live permission,
  broker mutation, replay execution, or runtime mutation.
- Outcome and future return fields must not enter assignment or calibration.

## Validation Authority

- `GOVERNANCE_HEALTH` for this contract and report closeout.
- Future implementation tests may add `PACKAGE_HEALTH` only for bounded score
  arithmetic and guardrails.

PASS means the L5 exit score contract is present and diagnostic-only. PASS does
not mean strategy acceptance, deployment readiness, paper-order permission,
live-order permission, or real-capital permission.

