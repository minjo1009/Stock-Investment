# Task774 Salience Triage Contract

## Decision Summary

- Verdict: `SALIENCE_TRIAGE_CONTRACT_COMPLETE_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 6 salience classes; 0 numeric scores; 0 trading outputs.
- What changed: Defined non-directional salience classes that separate material facts from background noise after Task773.
- Next action: Task775 should retain only bounded working-memory slots from these salience classes.

## Quant Expert Report

Task774 converts `enough_for_review` packets into qualitative salience classes. Salience explains why a fact deserves attention. It does not rank candidates or create hidden priority.

Allowed salience classes are stored in `salience_class_catalog.csv`.

No joins, labels, PnL, or price reaction matching were used.

## No-Background Decision-Maker Report

1. Done: 중요한 정보와 잡음을 나누는 기준을 만들었습니다.
2. Done: 점수 없이 6개 class로만 분류합니다.
3. Not done: 순위나 매매 판단은 없습니다.
4. Next: Task775에서 작업기억 구조를 만듭니다.

## Artifact Manifest

- `task_774_salience_triage_contract.md`
- `salience_class_catalog.csv`
- `task_774_decision.csv`
- `artifact_manifest.csv`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
