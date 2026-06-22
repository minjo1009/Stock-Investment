# Task754 Engine Boundary Repair

## Decision Summary

Task754 repairs the `engine.py` as-of boundary enough to advance W2 work.

It does not certify strategy quality, alpha quality, full backtest correctness, deployment readiness, or real-capital use.

## Quant Expert Report

Boundary checks:

| check | status | evidence |
| --- | --- | --- |
| engine_import | PASS | backtest.engine imports successfully |
| no_next_open_source_pattern | PASS | no opens[i + 1] or next_open token in engine.py |
| execution_helpers_present | PASS | pending entry signal_close and deferred exit helper are present |
| no_top_level_lifecycle_writer_import | PASS | canonical lifecycle writer is absent from top-level imports |
| lazy_lifecycle_loader_present | PASS | _load_canonical_lifecycle_writers exists |
| lazy_lifecycle_runtime_check | PASS | importing backtest.engine does not import canonical lifecycle writer path |

Remaining owner-review dependencies:

| module | present | status | reason |
| --- | --- | --- | --- |
| backtest.analysis_sector | yes | REMAINING_REPAIR_SCOPE | sector mapping helper still belongs outside pure replay core |
| strategy.conditions | yes | REMAINING_REPAIR_SCOPE | strategy-specific signal conditions still belong in an adapter |
| strategy.validator | yes | REMAINING_REPAIR_SCOPE | strategy-specific validation still belongs in an adapter |

Interpretation:

```text
Entry and exit execution now resolve on the execution bar instead of reading the next bar during signal formation.
Lifecycle persistence is no longer a top-level engine dependency.
The engine still contains strategy-specific imports, so it is not yet a generic W2 replay core.
```

## No-Background Decision-Maker Report

1. 엔진이 미래 봉 가격을 미리 보는 큰 길을 막았습니다.
2. DB 기록기는 필요할 때만 불러오게 바꿨습니다.
3. 그래서 Task753 때 막힌 엔진 문제는 한 단계 앞으로 갔습니다.
4. 아직 순수 백테스트 코어는 아닙니다.
5. 다음은 전략 조건/검증/섹터 helper를 엔진 밖으로 빼는 일입니다.

## Artifact Manifest

Primary artifacts:

- `task754_engine_boundary_validation.csv`
- `task754_remaining_dependency_review.csv`
- `task754_summary.csv`
- `task_754_decision.csv`
- `gpt_review_notes.md`
- `subagent_review_notes.md`
- `validation_log.md`
- `artifact_manifest.csv`

## Standing Footer

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
