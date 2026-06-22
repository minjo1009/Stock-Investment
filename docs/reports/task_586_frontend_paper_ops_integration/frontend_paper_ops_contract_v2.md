# Frontend Paper Ops Contract V2

- UI reads `frontend/trader-terminal/public/catalog/trader_terminal_catalog.json` only.
- Task583 provides data freshness.
- Task584 provides runtime decision and no-trade reason.
- Task585 provides order/fill/lifecycle lineage.
- Task587 provides Slack send state.
- No raw CSV is read directly by React.
