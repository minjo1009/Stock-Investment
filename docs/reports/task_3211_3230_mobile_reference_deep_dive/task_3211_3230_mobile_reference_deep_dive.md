# Task3211-3230 Mobile Reference Deep Dive

## Decision Summary

- Verdict: the current `apps/trader-brain-web` UI is not a failed color polish pass; it is the wrong mobile information architecture. It renders a desktop dashboard in a narrow viewport instead of a mobile trading cockpit.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: target mix is TradingView-style Scanner/Chart 70%, Toss-style Home 20%, Analysis/Risk audit 10%; first implementation gate is the Scanner screen at 430x932.
- What changed: no app code, replay, selector, paper order, live order, source acquisition, deployment readiness, or real-capital status changed. This task records the developer-level UI/UX, tool, and read-model investigation that supersedes ad hoc visual polishing.
- Next action: rebuild the Next cockpit as a mobile-first five-tab app, starting with the Scanner screen and `CockpitReadModelV2`.

## Quant Expert Report

### Data Source And Source Readiness

- Visual references:
  - Reference 1: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-ff378cc6-9b75-4070-9acd-a9b5ed0c73bd.png`
  - Reference 2: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`
  - Reference 3: `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7861d17d-2f17-4482-93fd-00f81457e599.png`
- Current implementation screenshot:
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/04_mobile_cockpit_responsive.png`
- Current app data files:
  - `apps/trader-brain-web/public/catalog/paper_ops_runtime_catalog.json`
  - `apps/trader-brain-web/public/catalog/paper_trade_detail_view.json`
  - `apps/trader-brain-web/public/catalog/acceptance_status_catalog.json`
  - `apps/trader-brain-web/public/catalog/readiness_registry.json`
- Source readiness is partial for high-end UI. Trade detail bars and runtime status exist, but portfolio/account truth, market indices, theme heat, scanner freshness, source blockers, policy compare, and system health are not yet elevated into a mobile read model.

### Exact Join Keys

- Current frontend candidate key: `trade_id` or `position_id`, falling back to `${symbol}-${index}` in `apps/trader-brain-web/src/lib/cockpit-data.ts`.
- Required v2 keys:
  - `scannerCandidates[].tradeId`
  - `scannerCandidates[].symbol`
  - `scannerCandidates[].routeTarget.selectedTradeId`
  - `chartFrame.symbol`
  - `chartFrame.sourceHash`
  - `eventOverlays.*.tradeId`
  - `sourceBlockers[].sourceFamily`
  - `policyCompare.baselineVariantId`
  - `policyCompare.challengerVariantId`

### Leakage Audit

- No inferred lifecycle matching was used.
- No symbol/date/price/time proximity fallback was added.
- No missing-label negative conversion was added.
- No unavailable raw source was approximated.
- No strategy acceptance, deployment readiness, broker-truth completion, paper-order permission, live-order permission, or real-capital permission changed.

### Split/OOS Metrics

- Not applicable. This was UI/UX, tool, and read-model investigation only.
- No replay, backtest, policy compare, selector tuning, sizing change, or cost/slippage stress was run.

### Failure Decomposition

1. Mobile architecture failure.
   - Current `page.tsx` is a single desktop tactical dashboard with responsive stacking.
   - Reference 2 is a mobile scanner-first app: header, filter chips, theme strip, dense watchlist, selected chart, event/status cards, and bottom nav all share one mobile task flow.

2. Density failure.
   - Reference 2 fits title/mode/update, filters, sector strip, watchlist header, and about 5-6 candidate rows before the selected chart.
   - Current mobile screenshot spends the first viewport on a large product title, implementation copy, and oversized KPI cards.

3. Table failure.
   - Current `CandidateTable.tsx` uses a `min-w-[720px]` desktop table. That produces horizontal-scroll behavior instead of native mobile scanner rows.
   - Target rows must be dense mobile rows: favorite icon, ticker, company, sparkline, price, change, RelVol, rank, freshness, one-line reason, and chevron.

4. Chart interaction failure.
   - Current `TradingChart.tsx` renders candles, VWAP, and volume.
   - Reference 2 requires a complete chart module: symbol header, status/action chip, interval controls, VWAP/volume/marker toggles, crosshair OHLC/VWAP tooltip, entry/block/current markers, range scrubber, event overlay strip, and bottom chart status bar.

5. Read-model failure.
   - Current `CockpitModel` has `summary`, `candidates`, `market`, `risk`, and `execution`.
   - The target app needs `portfolioSnapshot`, `scannerCandidates`, `marketSnapshot`, `tradeReview`, `chartFrame`, `eventOverlays`, `sourceBlockers`, `systemHealth`, and `policyCompare`.

6. Tool-use failure.
   - Figma MCP was checked. The user's file `7Rbtg734UfuXD8iqcneEyE` already has Apple iOS/iPadOS, Material 3, and Simple Design System libraries.
   - Figma MCP hit the Starter plan call limit before component search. Therefore, Figma can support the workflow, but current access cannot be treated as unlimited.

### Tool And Library Conclusions

1. Keep `Next 16 / React 19 / Tailwind v4`.
   - The stack is sufficient. The issue is not that Next cannot reach the target.

2. Use actual shadcn/ui patterns, not only hand-rolled shadcn-like primitives.
   - Required patterns: `Tabs`, `Drawer/Sheet`, `ScrollArea`, `Tooltip`, `ToggleGroup`, `Badge`, `Separator`, and command/filter surfaces.
   - Official source: [shadcn/ui blocks](https://ui.shadcn.com/blocks), [shadcn data table](https://ui.shadcn.com/docs/components/radix/data-table).

3. Use Tremor Raw patterns only.
   - Avoid `@tremor/react` in this app because Task3191-3210 already found React 19/Next 16 SSR trouble.
   - Use copy-paste KPI, status, table, and chart composition patterns instead.
   - Official source: [Tremor](https://tremor.so/), [Tremor installation](https://www.tremor.so/docs/getting-started/installation), [Tremor Blocks](https://blocks.tremor.so/).

4. Keep TradingView Lightweight Charts for now.
   - It is small, fast, open-source, and controllable with local read-only data.
   - Required next work is a custom chart shell around it, not a plain embedded chart.
   - Official sources: [Lightweight Charts](https://www.tradingview.com/lightweight-charts/), [markers](https://tradingview.github.io/lightweight-charts/tutorials/how_to/series-markers), [tooltips](https://tradingview.github.io/lightweight-charts/tutorials/how_to/tooltips), [panes](https://tradingview.github.io/lightweight-charts/docs/panes).

5. Do not adopt TradingView Advanced Charts yet.
   - It is closer visually, but it requires the private library path and a custom datafeed.
   - Official docs state Advanced Charts and Trading Platform do not include market data, so our own datafeed is mandatory.
   - Official sources: [Advanced Charts datafeed API](https://www.tradingview.com/charting-library-docs/latest/connecting_data/datafeed-api/), [Advanced Charts quick start](https://www.tradingview.com/charting-library-docs/latest/quick-start/).

6. Add TanStack Virtual when scanner rows move beyond the small current fixture.
   - TanStack Table does not include virtualization itself; TanStack Virtual is the correct headless companion.
   - Official sources: [TanStack Table virtualization guide](https://tanstack.com/table/v8/docs/guide/virtualization), [TanStack Virtual](https://tanstack.com/virtual/latest).

7. Use assistant-ui later for a read-only research panel only.
   - It is not part of the Scanner P0 surface.
   - It must not expose replay, selector, paper-order, live-order, or execution actions.
   - Official source: [assistant-ui docs](https://www.assistant-ui.com/docs).

8. Use Figma MCP as a design verification and token source, not as a magic UI generator.
   - Current Figma file libraries found: Material 3 Design Kit, Simple Design System, iOS 18/iPadOS 18, iOS/iPadOS 26, watchOS 26, visionOS 26, macOS 26.
   - Tool blocker: Figma MCP Starter plan limit blocked `search_design_system`.

### Required Mobile Acceptance Gates

1. Scanner first viewport gate at 430x932:
   - 0-80px: app title, mode dropdown, updated time, status dot, menu badge.
   - 80-130px: 6-7 filter chips.
   - 130-220px: theme strip with 4 sectors and tiny sparklines.
   - 220-300px: scanner table header.
   - 300-760px: at least 5 dense candidate rows visible.
   - Selected chart starts within one scroll from the first viewport.

2. Dense row gate:
   - Row height target: 64-72px.
   - Required fields: ticker, company, status, sparkline, price, market value, change percent, RelVol, rank, freshness, one-line reason, route chevron.
   - No horizontal table scroll.

3. Chart gate:
   - Chart card height: 560-700px including controls.
   - Candles, VWAP, volume, price axis, time axis, crosshair tooltip, marker labels, range scrubber, chart status bar.
   - VWAP must not be silently approximated. Missing VWAP must render as missing or source-gated.

4. Navigation gate:
   - Bottom tabs: `홈 / 스캔 / 분석 / 시장 / 위험`.
   - Home uses Reference 3.
   - Scanner uses Reference 2.
   - Analysis/Risk use Reference 1.

5. Copy gate:
   - No visible implementation copy such as `Next.js`, `Tailwind`, `shadcn`, `Tremor`, or `Read-only by contract` in the main product surface.
   - Governance statuses remain visible where useful: `NOT_ACCEPTED`, `DIAGNOSTIC ONLY`, `LIVE ORDERS 0`, `실주문 없음`.

6. Visual gate:
   - Reference and implementation screenshots must be compared side by side at the same viewport before handoff.
   - Screenshots alone are not QA.

### Proposed `CockpitReadModelV2`

```ts
type CockpitReadModelV2 = {
  contractVersion: "trader-brain-web-read-model-v2";
  generatedUtc: string;
  routeTarget: {
    defaultTab: "home" | "scanner" | "analysis" | "market" | "risk";
    selectedTradeId?: string;
    selectedSymbol?: string;
  };
  freshness: {
    catalogGeneratedUtc: string;
    sourcePriceUtc?: string;
    latestRuntimeDecisionUtc?: string;
    latestEodSession?: string;
    status: "FRESH" | "STALE" | "SOURCE_GATED" | "PARTIAL";
    ageSec?: number;
    blockers: string[];
  };
  acceptance: {
    strategy: "NOT_ACCEPTED";
    deployment: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
    realCapital: "FORBIDDEN";
    paperStatus?: string;
  };
  portfolioSnapshot: {
    totalAssetsUsd: number;
    cashUsd?: number;
    marketValueUsd: number;
    realizedPnlUsd: number;
    unrealizedPnlUsd: number;
    totalReturnPct?: number;
    openPositions: number;
    exposurePct?: number;
    accountTruthSource: string;
    pnlPolicy: string;
  };
  scannerCandidates: ScannerCandidate[];
  marketSnapshot: MarketSnapshot;
  tradeReview: TradeReview;
  chartFrame: ChartFrame;
  eventOverlays: EventOverlays;
  sourceBlockers: SourceBlocker[];
  systemHealth: SystemHealth;
  policyCompare: PolicyCompare;
};
```

### Subagent Packets Used

Packet 1:

```text
Objective: Decompose Reference 1/2/3 and current mobile screenshot into measurable UI acceptance criteria.
Owner Team: Frontend UI / Product Design
Reviewer Team: Research Governance
Read Scope: reference images, current mobile screenshot, Task3191-3210 report, trader-brain-web source.
Write Scope: none.
Inputs: three user reference images and current screenshot.
Required Outputs: screen anatomy, current gaps, measurable gates.
Forbidden Actions: no file edits, no replay, no selector change, no order mutation.
Validation Command: not applicable, explorer packet.
Validation Authority: REPORTING_HEALTH for UI report evidence only.
Report Requirement: return concise findings for integration.
```

Packet 2:

```text
Objective: Review the feasible frontend stack for reaching high-end mobile trading UI.
Owner Team: Frontend Web
Reviewer Team: Research Governance
Read Scope: package.json, current app source, official/public docs where needed.
Write Scope: none.
Inputs: Next cockpit source and user target direction.
Required Outputs: adopt/avoid list, blockers, next implementation stack.
Forbidden Actions: no file edits, no dependency install, no replay, no order mutation.
Validation Command: not applicable, explorer packet.
Validation Authority: REPORTING_HEALTH for stack recommendation only.
Report Requirement: return concise findings for integration.
```

Packet 3:

```text
Objective: Design the read-only mobile page-map and DB/read-model contract needed for the target UI.
Owner Team: Frontend Data Contract
Reviewer Team: Research Governance
Read Scope: cockpit-data.ts and copied public catalog JSON files.
Write Scope: none.
Inputs: current catalog shape and target mobile page map.
Required Outputs: CockpitReadModelV2 proposal, DB/API field gaps, page-to-model mapping.
Forbidden Actions: no file edits, no inferred matching, no raw source approximation, no replay, no order mutation.
Validation Command: not applicable, explorer packet.
Validation Authority: REPORTING_HEALTH for frontend data-contract evidence only.
Report Requirement: return concise findings for integration.
```

## No-Background Decision-Maker Report

- What happened: the current UI was investigated against the three supplied reference screens, available Figma/MCP options, open-source UI/chart/table tools, and the current app read model.
- Why it matters: the problem is now scoped correctly. The next build should not polish the current page. It should replace it with a mobile-first five-tab trading cockpit.
- Whether this changes capital/deployment readiness: no. Strategy remains `NOT_ACCEPTED`, deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and real capital remains `FORBIDDEN`.
- Plain-language next step: build the Scanner tab first. If Scanner does not approach Reference 2, stop and fix it before Home/Analysis/Risk work.

## Artifact Manifest

- Inputs:
  - `docs/operating_system/project_operating_state.md`
  - `docs/reports/task_3191_3210_next_cockpit_redesign/task_3191_3210_next_cockpit_redesign.md`
  - `apps/trader-brain-web/package.json`
  - `apps/trader-brain-web/src/app/page.tsx`
  - `apps/trader-brain-web/src/components/CandidateTable.tsx`
  - `apps/trader-brain-web/src/components/TradingChart.tsx`
  - `apps/trader-brain-web/src/lib/cockpit-data.ts`
  - `apps/trader-brain-web/public/catalog/paper_ops_runtime_catalog.json`
  - `apps/trader-brain-web/public/catalog/paper_trade_detail_view.json`
  - `apps/trader-brain-web/public/catalog/acceptance_status_catalog.json`
  - `apps/trader-brain-web/public/catalog/readiness_registry.json`
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-ff378cc6-9b75-4070-9acd-a9b5ed0c73bd.png`
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7bac662e-c666-4e2f-a875-fe9bb523f577.png`
  - `C:/Users/minjo/AppData/Local/Temp/codex-clipboard-7861d17d-2f17-4482-93fd-00f81457e599.png`
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/04_mobile_cockpit_responsive.png`
- Outputs:
  - `docs/reports/task_3211_3230_mobile_reference_deep_dive/task_3211_3230_mobile_reference_deep_dive.md`
  - `docs/reports/task_3211_3230_mobile_reference_deep_dive/task_3230_decision.csv`
  - `data/artifacts/task_3211_3230_mobile_reference_deep_dive/artifact_manifest.csv`
  - `scripts/trader_brain_3211_3230_mobile_reference_deep_dive_validate.py`
- Row counts:
  - Subagent explorer packets: 3.
  - User reference images: 3.
  - Current implementation screenshot reviewed: 1.
  - App code files reviewed directly: 5.
  - Catalog JSON files reviewed directly: 4.
- File sizes:
  - Recorded in `data/artifacts/task_3211_3230_mobile_reference_deep_dive/artifact_manifest.csv`.
- Validation commands:
  - `python scripts/trader_brain_3211_3230_mobile_reference_deep_dive_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Not applicable. No new source acquisition was performed.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
