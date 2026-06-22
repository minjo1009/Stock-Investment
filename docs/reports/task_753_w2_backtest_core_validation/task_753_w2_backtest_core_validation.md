# Task753 W2 Backtest Core Validation

## Decision Summary

W2 work moved forward by fixing the raw-data fallback issue in `data_loader.py` and mapping the rest of the backtest candidates.

`engine.py` and `engine_full.py` are not promoted. They need boundary and as-of repairs before they can be treated as canonical core.

## Quant Expert Report

Current W2 classification:

| path | verdict | reason |
| --- | --- | --- |
| src/backtest/models.py | PASS_CONTRACT_CANDIDATE | stdlib-only backtest result contracts; reconcile duplication with common.models before wider use |
| src/backtest/data_loader.py | PASS_LOADER_AFTER_FALLBACK_REPAIR | PASS_EXPLICIT_OPT_IN_ONLY |
| src/backtest/engine.py | BLOCK_REPAIR_REQUIRED | imports strategy/validator/sector/lifecycle implementation and uses next-open execution convention needing as-of contract |
| src/backtest/engine_full.py | OWNER_REVIEW_ONLY | broad integration engine imports execution/risk/portfolio/universe/strategy and has portfolio full-snapshot leakage risk |
| src/backtest/analysis.py | SUPPORTING_ANALYZER_NOT_ENGINE_CORE | exported trades analyzer; useful but not simulation engine core |

Immediate implications:

```text
models.py: usable contract candidate, but check overlap with common.models.
data_loader.py: usable after explicit sample fallback opt-in repair.
analysis.py: supporting analyzer, not engine core.
engine.py: repair required before promotion.
engine_full.py: owner-review-only integration engine.
```

Subagent/GPT review agreed on the main blockers:

```text
No fake data fallback in canonical loader.
No broad strategy/risk/execution/portfolio import fan-out in W2 core.
No next-open/as-of ambiguity without explicit execution convention.
No full-period portfolio snapshot ranking in historical replay.
```

## No-Background Decision-Maker Report

1. 가짜 샘플 데이터 자동 사용은 막았습니다.
2. 백테스트 뼈대 중 바로 믿을 수 있는 건 아직 작습니다.
3. `engine.py`는 고쳐야 합니다.
4. `engine_full.py`는 아직 핵심 엔진이 아니라 큰 통합 엔진입니다.
5. 다음은 `engine.py`를 순수 replay core로 줄이는 작업입니다.

## Artifact Manifest

Primary artifacts:

- `task753_w2_backtest_core_validation.csv`
- `task753_summary.csv`
- `task_753_decision.csv`
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
