# Task750 Canonical Package Extraction Plan

## Decision Summary

Task750 creates an extraction plan only.

It does not move `src/` files, change imports, change trading logic, accept a strategy, or claim deployment readiness.

GPT review changed the order:

```text
contracts/state/interfaces first
backtest engines second
runtime/integration last
```

## Quant Expert Report

The 33 Task746 `canonical_package_candidate` files are still candidates.

The corrected extraction order is:

| wave_id | wave_name | count | owner_review_only | main_gate |
| --- | --- | --- | --- | --- |
| W0 | package_skeleton | 11 | 0 | namespace import and no side effect only; approval meaning forbidden |
| W1 | contracts_state_interfaces | 7 | 0 | interface contract, model compatibility, state boundary, no broker/live dependency |
| W2 | backtest_core | 5 | 1 | deterministic replay, as-of/timestamp discipline, no future leakage, W1 output compatibility |
| W3 | app_report_shell | 4 | 2 | does not bypass canonical engine, evidence-only reporting, no acceptance/status overclaim |
| W4 | guarded_runtime_integration | 6 | 6 | EXECUTION_HEALTH only, external guard, no live/order side effect, broker-truth distinction |

Key rule:

```text
Candidate != Approved
PASS != Acceptance
Import health != Trading validity
Runtime import != Broker truth
```

Owner-review-only even if import tests pass:

```text
src/app/run_trade_loop.py
src/app/run_trade_once.py
src/app/reconciliation.py
src/integration/kis_auth_manager.py
src/integration/kis_client.py
src/integration/slack_client.py
src/backtest/engine_full.py
src/app/pipeline.py
src/ui/app.py
```

## No-Background Decision-Maker Report

1. 먼저 껍데기와 계약부터 봅니다.
2. 그 다음 백테스트 엔진을 봅니다.
3. 실시간/외부연동/KIS/Slack은 맨 마지막입니다.
4. 테스트 통과는 정리 통과일 뿐입니다.
5. 전략 승인이나 실거래 가능 상태가 아닙니다.

## Artifact Manifest

Primary artifacts:

- `task750_canonical_package_plan.csv`
- `task750_summary.csv`
- `task_750_decision.csv`
- `gpt_review_notes.md`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
