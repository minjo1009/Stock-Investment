# Task3910 Portfolio Capture Readability Fix

## Summary

Task3910 repaired the Portfolio tab after a screenshot review showed that the
diagnostic backtest KPIs and holdings table still rendered as clipped mobile
content.

## User-Visible Problem

- Backtest KPI values could render with ellipsis on mobile width.
- The holdings table could clip the right edge of columns.
- Row subtitles could truncate diagnostic labels.
- The wide-table pattern was too fragile for the current phone-first Portfolio
  tab.

## What Changed

- Reworked the Portfolio diagnostic holdings area from a clipped horizontal
  table into readable vertical mobile rows.
- Kept the card fixed-height with an internal vertical scroll area for
  additional holdings.
- Replaced dense metric columns with two-column chips for trade count, invested
  amount, average holding period, and worst trade return.
- Kept row selection local and read-only; selecting a row still updates the
  detail card.
- Changed the backtest KPI summary to a two-column mobile grid so CAGR, MDD,
  trade count, and QQQ comparison values fit without ellipsis.
- Updated the mobile product validator to block regressions back to the clipped
  wide-table pattern.

## Screenshot Evidence

- Before: `data/artifacts/portfolio_tab_capture_task3910.png`
- Intermediate: `data/artifacts/portfolio_tab_capture_task3910_after.png`
- Readable rows full-page evidence:
  `data/artifacts/portfolio_tab_capture_task3910_readable_rows.png`
- Final phone viewport evidence:
  `data/artifacts/portfolio_tab_capture_task3910_viewport.png`

The final viewport DOM text contains full values such as `+43.88%`, `+84.70%`,
`AVGO - diagnostic`, and visible row chips without visual ellipsis in the
captured viewport.

## GPT Loop Status

The user requested a GPT-loop review from the Portfolio tab screenshot. Codex
captured the screen and prepared the GPT expert prompt, but the available local
automation could not capture a GPT response in this turn.

- GPT capture status: `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`
- GPT role intended: Principal Mobile Product Designer + React Native Layout
  Architect
- Codex action: screenshot-derived UI repair only

No GPT recommendation is treated as source-of-truth for this task because no
GPT response artifact was captured.

## Safety Boundary

- Displayed rows remain diagnostic backtest summaries, not broker/account
  positions.
- Strategy acceptance remains `NOT_ACCEPTED`.
- Deployment readiness remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No active DB, runtime API, broker, paper/live, or real-capital system was
  connected.

## Validation

- `cd apps/ios-trader-brain && npm run typecheck`
- `cd apps/ios-trader-brain && npm run validate:mobile-product-v1`
- `cd apps/ios-trader-brain && npm run validate:backtest-snapshot`
- `cd apps/ios-trader-brain && npm run validate:safety`
- `cd apps/ios-trader-brain && npm run lint`
- `python scripts/task_registry_validate.py`
- `git diff --check`
