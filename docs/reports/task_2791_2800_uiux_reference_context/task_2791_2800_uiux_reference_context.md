# Task2791-2800 UIUX Reference Context

## Decision Summary

- Verdict: `PRIMARY_PASS` for UI/UX reference gathering and application plan.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: 12 local reference files, 15 manifest rows, 2 completed subagent reviews, 0 app code changes, 0 live-order capability changes.
- What changed: Toss and TradingView references were gathered into a durable artifact pack, and the next mobile UX application plan was fixed.
- Next action: implement the P0 UI changes in a separate task, then run Expo visual QA.

## Quant Expert Report

### Data Source And Source Readiness

This task is UI/UX reference work, not trading data or replay work.

Official/source-backed inputs:

- Toss Tech UX research: `https://toss.tech/article/uxresearcher-meets-investor`
- Toss Securities investment information service: `https://corp.tossinvest.com/ko/business?tab=investmentInfoService`
- Toss App Store page: `https://apps.apple.com/kr/app/%ED%86%A0%EC%8A%A4/id839333328`
- TradingView watchlists: `https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/`
- TradingView advanced watchlist: `https://www.tradingview.com/support/solutions/43000771546-watchlist-advanced-view-mode/`
- TradingView mobile chart specifics: `https://www.tradingview.com/charting-library-docs/latest/mobile_specifics/`

Downloaded local files:

- 6 Toss official App Store screenshots.
- 4 Toss/TradingView mobile web captures.
- 2 raw iTunes lookup JSON packets.

TradingView iTunes lookup exposed no usable `screenshotUrls`, so TradingView visual context was gathered from official pages, official documentation, and web captures instead.

### Exact Join Keys

Not applicable. This task does not join trading rows.

### Leakage Audit

Not applicable to PnL. The UI plan preserves the existing rule that paper/live status, source readiness, and no-trade reasons must be displayed without using future/outcome information as assignment input.

### Split/OOS Metrics

Not applicable. No replay or backtest was run.

### Failure Decomposition

Previous UI work improved Korean readability, but still missed the actual product rhythm:

1. It was too close to a research cockpit.
2. It did not sufficiently expose `보유 / 관심 / 최근 본`.
3. It did not make `오늘 왜 봐야 하는지` the first-screen behavior.
4. It had TradingView-like chart pieces, but not enough watchlist grouping, column selection, or chart readout behavior.
5. It still risked showing internal benchmark/meta text where a user-facing app needs direct action context.

### Cost/Slippage Stress

Not applicable.

### Remaining Blockers

- No real-order or live automation UI can be introduced.
- Toss/TradingView trademarks, logos, screenshots, and trade dress cannot be copied as app assets.
- Any price alert pattern must be read-only `모의 관찰 조건`, not order routing.
- Actual implementation still needs iPhone visual QA.

## GPT/Subagent Review Summary

### Toss Review

Conclusion: the target is not "look like Toss" but "behave like an easy investment routine."

Apply:

1. Home must split `보유 / 관심 / 최근 본`.
2. Every symbol row should show `다음 확인 이유`.
3. Detail should start with a plain Korean summary, then chart.
4. Risk should become `지금 확인할 일`, not just abstract blockers.
5. Add privacy mode for balances and PnL.

Do not copy:

- Toss logo, brand blue, icons, screenshots, exact typography, or order/condition-order flows.

### TradingView Review

Conclusion: the target is not TradingView cloning; it is high-density read-only scanning.

Apply:

1. Trades needs `간단 / 상세` view.
2. Add watchlist sections: `보유 / 관찰 / 위험 / 거절 후보`.
3. Add controlled columns: `가격 / 등락률 / 손익 / 위험 / 거래량 / 소스`.
4. Detail needs fullscreen chart mode and crosshair-style readout.
5. Source freshness and news/reason feed must be closer to each symbol.

Do not copy:

- TradingView logos, proprietary UI chrome, paid charting trade dress, or real trading controls.

## No-Background Decision-Maker Report

### What Happened

실제 토스/트레이딩뷰 레퍼런스를 더 모아 봤습니다.

결론은 명확합니다.

토스는 `쉽게 이해하고 매일 확인하게 만드는 앱`입니다.
트레이딩뷰는 `빨리 스캔하고 차트로 판독하는 앱`입니다.

우리 앱은 둘을 섞어야 합니다.

### What This Means

홈은 토스처럼 쉬워야 합니다.

- 내 상태
- 오늘 확인할 일
- 보유/관심/최근 본 후보
- 쉬운 매수/매도 근거

종목/상세는 트레이딩뷰처럼 조밀해야 합니다.

- 관심종목 그룹
- 정렬/컬럼
- 차트
- VWAP/거래량/진입가/손절선
- 소스/뉴스/리스크 피드

### Does This Change Capital Or Deployment Readiness?

No.

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

This task only prepares UI/UX application context.

## What To Apply To Our App

### P0

1. Home: `보유 / 관심 / 최근 본` sections.
2. Home: `오늘 확인할 일` cards.
3. Trade row: `다음 확인 이유`.
4. Detail: `쉬운 요약` above the chart.
5. Trades: `간단 / 상세` watchlist mode.
6. Trades: grouped sections `보유 / 관찰 / 위험 / 거절 후보`.
7. Risk: convert the page to `지금 확인할 일`.
8. Keep every action read-only: `모의 관찰`, `근거 보기`, `위험 확인`.

### P1

1. Symbol feed tabs: `근거 / 뉴스·공시 / 위험`.
2. Source freshness ledger in Settings.
3. Watchlist column toggles: `가격 / 등락률 / 손익 / 위험 / 거래량 / 소스`.
4. Chart indicator toggles: `VWAP / 거래량 / 진입가 / 손절 기준선`.
5. Privacy mode for balance/PnL.

### P2

1. Fullscreen chart mode.
2. Crosshair-style readout.
3. Portfolio composition / PnL contribution chart.
4. Read-only observation condition cards.

## What Not To Apply

1. No Toss or TradingView logo/brand/color/typography copying.
2. No screenshot assets inside the app.
3. No order CTA.
4. No condition-order UI.
5. No wording that implies live deployment.
6. No "accepted strategy" language.

## Artifact Manifest

### Inputs

- Official web sources listed above.
- Local screenshots and captures under `data/artifacts/task_2791_2800_uiux_reference_context/`.
- Subagent review outputs.

### Outputs

- `data/artifacts/task_2791_2800_uiux_reference_context/reference_source_manifest.csv`
- `data/artifacts/task_2791_2800_uiux_reference_context/artifact_manifest.md`
- `docs/reports/task_2791_2800_uiux_reference_context/task_2791_2800_uiux_reference_context.md`
- `docs/reports/task_2791_2800_uiux_reference_context/task_2800_decision.csv`

### Row Counts

- Source manifest rows: 15
- Downloaded local files before manifest/report: 12
- App code changes: 0

### Validation Commands

- `python scripts/trader_brain_2791_2800_uiux_reference_context_validate.py`
- `python scripts/task_registry_validate.py`

### Source Hashes

See `data/artifacts/task_2791_2800_uiux_reference_context/artifact_manifest.md`.
