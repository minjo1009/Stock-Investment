# Task3911 Portfolio Table Layer Restore Fit

## Summary

Task3911 restored the prior Portfolio holdings table layer after user feedback
that the Task3910 vertical summary-row layout was worse. The repair keeps the
fixed-name-column plus horizontally scrollable metric table and applies bounded
text fitting inside cells instead of replacing the table structure.

## User Feedback

- The previous table layer was better than the Task3910 vertical summary rows.
- The correct fix should preserve that layer and make text fit the cells.

## What Changed

- Restored the Portfolio holdings table structure from the pre-Task3910 layer.
- Removed the Task3910 vertical readable-row replacement.
- Kept the fixed-height card and internal vertical scroll behavior.
- Kept the fixed first column for symbol/name context.
- Added bounded text fitting for metric cell primary and secondary values:
  `adjustsFontSizeToFit`, `minimumFontScale`, and one-line bounded text.
- Shortened diagnostic row subtitles from long backtest wording to compact
  `diagnostic` wording for the fixed name column.
- Made metric columns narrower and lower-font so two metric columns are visible
  in the initial phone viewport, while the remaining metrics remain reachable
  by horizontal scroll.
- Kept the two-column backtest KPI card grid from Task3910 because it fixed the
  KPI ellipsis without changing the holdings table layer.
- Updated the mobile product validator to require the restored table layer,
  bounded text fitting, and compact diagnostic row subtitles.

## Screenshot Evidence

- Restored table before final fit:
  `data/artifacts/portfolio_tab_capture_task3911_restored_table.png`
- Final fitted table:
  `data/artifacts/portfolio_tab_capture_task3911_fitted_table.png`

The final viewport shows the prior table layer with visible `diagnostic P/L`
and `trade count` columns, compact row subtitles, and no vertical summary-card
replacement.

## GPT Consult Status

The user requested GPT involvement. Codex classified this as a single GPT
consult with Agent Mode and GitHub repo context, but the current tool surface
does not expose a Chrome/GPT send-and-capture path. The consult is therefore
recorded as blocked.

- GPT capture status: `BLOCKED_AUTOMATION_NO_GPT_CAPTURE`
- GPT response used as source-of-truth: no
- Codex action: user-feedback-driven rollback plus bounded text-fit repair

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
