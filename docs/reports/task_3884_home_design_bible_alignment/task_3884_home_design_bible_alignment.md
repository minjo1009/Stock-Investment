# Task3884 — HOME Design Bible Alignment

## Summary

Task3884 realigned the read-only mobile HOME screen with the frontend SSOT, Design System, production UI toolchain reference, and the local UI Design Bible so the first screen leads with account/investment comprehension instead of governance-heavy scaffolding.

## GPT Loop Ledger

| Loop | Role | Result |
| --- | --- | --- |
| 1 | Mobile product architect / design reviewer | Recommended removing duplicate HOME sections, hiding internal fixture paths, and centering HOME on QQQ-relative return/MDD plus meaningful attention items. |
| 2 | Read-model / chart contract reviewer | Recommended `relativeReturnChart`, empty `points`, `SOURCE_NOT_ATTACHED`, and no synthetic chart series. |
| 3 | Final pre-implementation reviewer | Confirmed PASS_WITH_CHANGES for HOME IA, chart source state, attention queue, and validators. |
| 4 | Post-implementation reviewer | Found no P0; requested shorter Korean copy, flat chart missing-state presentation, and committing the design bible for future GPT access. |
| 5 | Final visual / SSOT reviewer | Returned PASS; recorded P1 follow-ups for above-fold density and future source-backed chart island. |

## Implemented

- HOME now leads with `투자 현황`, `오늘의 투자 요약`, QQQ-relative return/MDD chart area, `오늘 확인할 것`, and compact `데이터 상태`.
- HOME no longer renders `계좌 스냅샷`, `운영 제한 상태`, or `비활성화된 기능` as first-level sections.
- HOME cards no longer render the internal fixture path `apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json`.
- Added `HomeRelativeReturnChart` read-model contract and fixture data with `SOURCE_NOT_ATTACHED`, `points: []`, and QQQ benchmark.
- Added `HomeRelativeReturnChartCard` with Daily/1H/30m/15m/5m chips and visible QQQ/MDD labels.
- Kept the chart source-backed: no fake return series, no generated OHLC/VWAP, no broker/API/DB/runtime connection.
- Added `home-design-alignment` validation and updated HOME-specific product/mobile IA validators.
- Added the UI Design Bible to the frontend SSOT pack as a design reference only.

## Visual Evidence

- Final mobile web preview screenshot: `data/artifacts/task_3884_home_design_bible_alignment/home_design_alignment_final_textfit_390x844.png`
- Scope: local web preview evidence only.
- Native iOS, TestFlight, App Store, deployment, paper/live, broker, and real-capital evidence were not produced.

## Validation

Executed:

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run lint`
- `cd apps/ios-trader-brain && npm run validate:home-design-alignment`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:product-ia-reorder`
- `npm run validate:safety`
- `npm run validate:fixtures`
- `cd apps/ios-trader-brain && npm test`
- `python scripts/task_registry_validate.py`

Pending after closeout:

- Native iOS device evidence remains operator-gated.
- Real source-backed QQQ/portfolio chart series remains blocked until authoritative read-model sources are attached.

## P1 Follow-ups

- Reduce above-fold height so `오늘 확인할 것` can appear sooner without hiding QQQ/MDD.
- Replace the source-missing chart panel with a real TradingView-style chart island only after authoritative portfolio equity curve and QQQ benchmark series are attached.
- Continue Korean copy cleanup across PORTFOLIO/BRAIN/ORDERS/SYSTEM to remove older mojibake remnants.

## Safety Boundary

- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- Broker mutation remains forbidden.
- Paper/live permission remains absent.
- Frontend remains read-only and `NOT_AUTHORITY`.
