# Task3191-3210 Next Cockpit Redesign

## Decision Summary

- Verdict: implemented a new read-only Next.js trading cockpit to replace the failed Expo-native direct-design loop as the primary UI direction.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: Next build pass, TypeScript pass, custom frontend validator pass, desktop and mobile screenshots captured, server running at `http://127.0.0.1:3040/`.
- What changed: added `apps/trader-brain-web` with Next.js 16, Tailwind v4, shadcn-style primitives, TradingView Lightweight Charts, TanStack Table, and an AI research panel surface; connected existing paper runtime/detail catalogs read-only.
- Next action: refine the Next cockpit visual density and then decide whether to retire or wrap the Expo iOS cockpit.

## Quant Expert Report

- Data source and source readiness: reused existing `paper_ops_runtime_catalog.json`, `paper_trade_detail_view.json`, `acceptance_status_catalog.json`, and `readiness_registry.json` by copying them into the new web app `public/catalog` directory. No new raw source acquisition was performed.
- Exact join keys: candidate rows are keyed by `trade_id` or `position_id`; chart bars come from each detail row's `chart.bars`; runtime status comes from paper runtime catalog decision fields.
- Leakage audit: no assignment logic, label logic, lifecycle matching, proximity fallback, replay, or selector tuning was added.
- Split/OOS metrics: not applicable. No backtest or replay was run.
- Failure decomposition: Expo native visual work was too manual and weak. The new web cockpit uses standard web UI composition: shadcn-style primitives for layout, TradingView Lightweight Charts for price visualization, TanStack Table for candidate tables, and Tremor-style KPI cards implemented directly in Tailwind because `@tremor/react` is not compatible with the chosen React 19 / Next 16 runtime.
- Cost/slippage stress: not applicable. No PnL logic changed.
- Remaining blockers: npm audit still reports moderate advisories through Next's internal `postcss` dependency; `npm audit fix --force` proposes a breaking downgrade and was not applied. Strategy remains `NOT_ACCEPTED`; deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`; real capital remains `FORBIDDEN`.

## No-Background Decision-Maker Report

- What happened: a new web trading cockpit was built separately from the Expo app.
- Why it matters: this gives Codex a component-assembly path that is much more likely to reach the requested TradingView/Toss/analysis reference level.
- Whether this changes capital/deployment readiness: no. The UI is read-only and cannot create paper/live orders.
- Plain-language next step: polish this web cockpit, then connect it to live-refreshing read-only runtime catalogs.

## Artifact Manifest

- Inputs:
  - `frontend/trader-terminal/public/catalog/paper_ops_runtime_catalog.json`
  - `frontend/trader-terminal/public/catalog/paper_trade_detail_view.json`
  - `frontend/trader-terminal/public/catalog/acceptance_status_catalog.json`
  - `frontend/trader-terminal/public/catalog/readiness_registry.json`
- Outputs:
  - `apps/trader-brain-web`
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/01_desktop_cockpit.png` size 401061 bytes.
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/02_mobile_cockpit.png` size 171772 bytes.
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/03_desktop_cockpit_responsive.png` size 420766 bytes.
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/04_mobile_cockpit_responsive.png` size 142501 bytes.
  - `data/artifacts/task_3191_3210_next_cockpit_redesign/screenshots_live/05_desktop_cockpit_final.png` size 420852 bytes.
- Row counts: candidate rows rendered from copied catalog detail rows; no row mutation performed.
- Validation commands:
  - `cd apps/trader-brain-web; npm run build`
  - `cd apps/trader-brain-web; npx tsc --noEmit`
  - `python scripts/trader_brain_3191_3210_next_cockpit_redesign_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes: not applicable. No source acquisition was performed.
