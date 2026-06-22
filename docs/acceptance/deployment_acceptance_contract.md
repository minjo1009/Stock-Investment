# Deployment Acceptance Contract

Last updated: 2026-06-03

## Scope

This contract separates deployment readiness from paper operation and strategy acceptance.

Current state:

| Field | Status |
|---|---|
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |
| Strategy acceptance | `NOT_ACCEPTED` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| Real capital | `FORBIDDEN` |

Controlled paper readiness does not imply deployment readiness.

Strategy acceptance review does not imply deployment readiness.

## Deployment Claim Rule

The project must not claim any of the following while deployment readiness is `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`:

- deployment ready
- production ready
- real-capital ready
- live trading approved
- firm-grade live-ready

## Required Deployment Gates

Deployment readiness remains blocked until all gates pass:

| Gate | Owner | Required Evidence |
|---|---|---|
| Strategy acceptance | 필수 | Strategy status has progressed beyond `NOT_ACCEPTED` through the acceptance contract |
| Full lifecycle | 주은 | Entry, exit, trim, stop, take-profit, timeout, and kill-switch paths are tested |
| Broker truth | 주은 | Broker/order/fill reconciliation uses exact IDs only |
| Source health | 윤헌 | Source-health ledger passes at least 20 trading sessions and provider status is known |
| Microstructure readiness | 윤헌 | Live source contract includes quote, status, LULD or halt handling, timestamps, and required depth scope |
| Exact replay | 동승 | Paper-to-replay match rates are at least 99% with explained diffs |
| Cost/slippage | 동승 | Cost and slippage stress are applied to realized lifecycle, not proxy PnL |
| Risk limits | 주은 | Max position, concentration, daily order, scale-in, exposure, and kill-switch reports exist |
| Frontend warnings | 규승 | UI shows deployment blockers above PnL and polish |
| Slack policy | 서연 | Slack messages cannot imply deployment readiness |
| Governance closeout | 중훈 | Registry, manifests, readiness registry, and validation commands are current |

## Immediate Deployment Fail Conditions

Deployment readiness is blocked immediately if any item is true:

- SELL fills equal 0
- realized closed trades are below 100
- paper replay has unexplained mismatches
- missing source is inferred or approximated
- timestamp is unavailable
- provider is unknown
- proxy PnL is shown as realized PnL
- Slack or frontend copy implies deployment approval
- kill-switch path is untested

## Allowed Current Claim

The only allowed current claim is:

`READY_FOR_CONTROLLED_PAPER_RUN` and `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

## Validation

```powershell
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```
