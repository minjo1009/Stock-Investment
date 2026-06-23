# Task3879 Frontend Product IA Reorder

## Summary

Task3879 corrected the first-screen IA for the fixture-backed mobile frontend after user review found that governance/safety copy had become too dominant. The product hierarchy now starts with account, return, risk, portfolio, and candidate-review comprehension, while governance, source freshness, disabled permissions, and NOT_AUTHORITY warnings remain visible as secondary context.

## Scope

- HOME: move the first-screen focus to Korean account/performance/risk summary.
- PORTFOLIO: move the first-screen focus to holdings/account/PnL/risk summary.
- BRAIN: move the first-screen focus to candidate review/scanner summary.
- Preserve read-only, no broker mutation, no paper/live permission, no deployment readiness, and no real-capital permission.
- Keep all data fixture-backed and NOT_AUTHORITY.

## GPT Consult Evidence

GPT was used as page-level IA reviewer before each page patch.

| Page | Captured recommendation | Codex action |
| --- | --- | --- |
| HOME | First screen should show invested cash, account state, return state, win-rate state, and MDD before governance/source detail. | Reordered HOME around `오늘의 투자 요약`; governance/source moved below product summary. |
| PORTFOLIO | First screen should show invested cash, cash, market value, unrealized/realized PnL, exposure, MDD, and win rate. | Added portfolio summary fields and Korean top summary; broker/source controls stay secondary. |
| BRAIN | First screen should show candidate count, review-only candidates, blocked candidates, weak-evidence candidates, and review queue without score/rank/confidence. | Added scanner summary and Korean candidate queue; no candidate score/rank/confidence fields were introduced. |

## Implementation Notes

- HOME tab label is Korean and the header is hidden for a cleaner mobile app surface.
- HOME now starts with `투자 현황` and `오늘의 투자 요약`.
- PORTFOLIO now starts with `투자 현황` and `보유자산 요약`.
- BRAIN now starts with `후보 탐색` and `오늘의 후보 검토`.
- `UNKNOWN` remains an unknown/missing authority state, not negative evidence.
- Disabled action, source freshness, blocker, and governance sections remain visible after the product-first summary layer.

## Read Model Contract

The frontend read-model contract was updated so the UI is not relying on invented props:

- HOME `portfolioSnapshot`: `totalReturnPct`, `winRatePct`, `maxDrawdownPct`.
- PORTFOLIO `portfolioSummary`: invested cash, cash, market value, PnL, position count, exposure, win rate, MDD.
- BRAIN `scannerSummary`: candidate count, review-only count, blocked count, weak-evidence count, latest review timestamp.

These fields are still fixture-backed and are not authoritative broker, DB, runtime, or strategy state.

## Screenshot Evidence

| Screen | Evidence |
| --- | --- |
| HOME | `data/artifacts/task_3879_frontend_product_ia_reorder/home_after_ia_reorder_final_390x844.png` |
| PORTFOLIO | `data/artifacts/task_3879_frontend_product_ia_reorder/portfolio_after_ia_reorder_final_390x844.png` |
| BRAIN | `data/artifacts/task_3879_frontend_product_ia_reorder/brain_after_ia_reorder_final_390x844.png` |

## Validation

Run from `apps/ios-trader-brain`:

- `npm run typecheck`
- `npm run lint`
- `npm run validate:safety`
- `npm run validate:fixtures`
- `npm run validate:mobile-product-v1`
- `npm run validate:product-ia-reorder`
- `npm run validate:screen-boundary`
- `npm run validate:frontend-governance`
- `npm test`

Run from repo root:

- `python scripts/task_registry_validate.py`
- `git diff --check`
- `git diff --cached --check`

## Boundaries

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains false.
- No DB/runtime/KIS/Alpaca/broker connection was added.
- No order handler, submit path, or real trading action was added.
- Web-preflight screenshots are QA evidence only; they are not native iOS device evidence.

## Next

1. Continue product-first Korean IA on ORDERS and SYSTEM without letting governance become the primary visual subject.
2. Add native iOS device/simulator evidence when Mac/Apple tooling becomes available.
3. Replace fixture-backed summaries only after an authoritative read path is selected and documented.
