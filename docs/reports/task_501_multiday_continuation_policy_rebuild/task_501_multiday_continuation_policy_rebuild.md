# Task 501 - Multi-Day Continuation Policy Rebuild

## Decision Summary

- Goal achieved: 0
- Count / avg net / win / entry_reduce: 561 / 7.305% / 55.1% / 39.9%
- Median holding days / same-day exit: 85.48 / 0.0%
- Inferred lifecycle matching used: NO
- Daily raw bars used for policy simulation: YES

## Quant Expert Report

The prior Task499 failure was caused by short original lifecycle exits. Task501 keeps the exact entry population but regenerates a multi-day policy lifecycle from raw daily bars. This tests whether the entry/regime/continuation signal can support the requested holding horizon.

## No-Background Decision-Maker Report

이전 결과는 대부분 하루 안에 종료돼 목표와 맞지 않았다. 이번 task는 같은 진입 후보를 며칠 이상 보유하는 정책으로 다시 평가해, 목표가 데이터/엔진 구조상 가능한지 확인한다.

## Artifact Manifest

See `artifact_manifest.csv`.