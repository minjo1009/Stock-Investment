# Task783 Institutional Trader Panel Contract

## Decision Summary

- Verdict: `INSTITUTIONAL_TRADER_PANEL_CONTRACT_COMPLETE_RESEARCH_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics: 10 institutional lenses; 10 minimal questions; 10 blockers; 0 trade decisions.
- What changed: Converted the institutional role matrix into bounded input-budget review questions.
- Next action: Task784 should define macro/politics confidence caps.

## Quant Expert Report

The institutional panel is a critique router. Each desk gets one question and one blocker. No desk can create a source fact, rating, target, order, rank, or score.

The lens contract is stored in `institutional_lens_questions.csv`.

## No-Background Decision-Maker Report

1. Done: 10개 기관 역할별 질문을 만들었습니다.
2. Done: 각 기관은 질문 1개와 blocker 1개만 가집니다.
3. Not done: 기관 의견으로 매매 판단을 만들지 않았습니다.
4. Next: 정치/거시 필터로 넘어갑니다.

## Artifact Manifest

- `task_783_institutional_trader_panel_contract.md`
- `institutional_lens_questions.csv`
- `task_783_decision.csv`
- `artifact_manifest.csv`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
