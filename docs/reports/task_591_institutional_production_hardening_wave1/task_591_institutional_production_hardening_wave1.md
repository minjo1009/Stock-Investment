# Task591 - Institutional Production Hardening Wave 1

## Decision Summary

- decision_status=PRIMARY_PASS
- scope=runtime_import_compatibility_and_slack_secret_guard
- production_claim=NO_GO_FOR_REAL_CAPITAL
- execution_behavior_changed=NO
- validated_without_PYTHONPATH_src=YES
- validated_with_PYTHONPATH_src=YES

## Quant Expert Report

Wave 1 fixes two production-readiness weaknesses that can block or corrupt operations before strategy logic is even evaluated.

First, selected runtime modules now import under both repository-root `src.*` execution and legacy `PYTHONPATH=src` execution. This reduces scheduler and PowerShell fragility without changing trading behavior.

Second, the central Slack webhook client now blocks messages that contain configured broker, Alpaca, or Slack secrets before network transmission. Caller-level checks remain useful, but the transport layer is now the final outbound safety guard.

This patch does not change signal generation, risk sizing, order lifecycle, market calendar logic, fill assumptions, or backtest logic. It is infrastructure hardening only.

Remaining institutional gaps include a complete import-boundary cleanup, deterministic data contracts for all runtime tables, broker reconciliation stress tests, partial-fill lifecycle tests, frontend artifact contract tests, and live-source readiness gates.

## No-Background Decision-Maker Report

이번 패치는 실거래 수익률 개선이 아니라 운영 안정성 보강입니다.

스케줄러나 PowerShell 실행 방식에 따라 일부 운영 모듈이 import 단계에서 죽을 수 있던 문제를 줄였고, Slack 전송 계층에서 비밀키가 메시지에 섞이면 네트워크 전송 전에 차단하도록 만들었습니다.

아직 실자금 투입 가능 상태는 아닙니다. 다음 단계는 데이터 계약, 주문 생명주기, 부분체결, 재조정, 프론트엔드 표시 계약을 같은 방식으로 하나씩 검증 가능한 패치로 잠그는 것입니다.

## Artifact Manifest

See `artifact_manifest.csv`.
