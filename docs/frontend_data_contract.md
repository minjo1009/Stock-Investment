# Frontend Data Continuity Contract

This contract prevents the UI from mixing legacy backtest files, research task artifacts, and live/paper capture data without explicit provenance.

## Source Tiers

| Tier | Example | UI status | Rule |
| --- | --- | --- | --- |
| Legacy portfolio source | `data/backtest/trades.json`, `trading.db` fallback | Legacy / not task artifact | May be shown only with explicit source warning and file hash. |
| Research task artifact | `docs/reports/task_*/artifact_manifest.csv`, `task_*_decision.csv`, assignment/quality CSVs | Diagnostic / task-versioned | Must show `task_id`, upstream task, decision file, report file, artifact manifest, and fingerprint. |
| Paper/shadow capture | Task531/547 decision/order/fill/capture logs | Paper/shadow / not deployment | Must show receive timestamp readiness, order/fill lineage status, and deployment blocker. |
| Deployment/live source | Broker-truth order/fill plus live microstructure archive | Deployment candidate only after hard gates | Must not be implied from historical OHLCV or simulated fills. |

## Required UI Provenance

Every performance number shown to an investor or trader must sit under a visible provenance block with:

- Page name
- Source tier
- `task_id` or `NOT_TASK_ARTIFACT`
- Strategy or policy version when available
- Source path
- Source modified time
- Source hash or artifact fingerprint
- Whether the result is diagnostic-only, paper/shadow, blocked, or deployment-ready

## Screen Rules

### Portfolio Overview

- Reads legacy portfolio trade data.
- Must say `NOT_TASK_ARTIFACT`.
- Must not be described as Task489/505/521/547 performance.
- Must show source path and hash before metrics.

### Research Reports

- Reads `tasks/task_registry.csv`, task decision CSV, report markdown, and artifact manifest.
- Must show selected task provenance before metrics.
- If a selected task has no PnL artifact, the UI must not invent a performance dashboard.
- If performance is loaded from another task artifact, the UI must warn that selected task and performance source differ.

### Trader Dashboard

- May calculate trade count, win rate, average net, drawdown proxy, symbol/theme breakdown, and rationale only from an explicitly selected performance artifact.
- Must show the PnL column used.
- Must show leakage/fallback/data-quality checks when fields are reported.
- Must mark proxy metrics as proxy until portfolio capital path and broker-truth fills are attached.

### React Trader Terminal

- Lives in `frontend/trader-terminal`.
- Must read `frontend/trader-terminal/public/catalog/trader_terminal_catalog.json`, not raw task CSVs directly.
- Catalog generation is owned by `python scripts/build_trader_terminal_catalog.py`.
- Required pages are `Account`, `Strategy`, `Trade Evidence`, and `Tasks`.
- Every page must keep visible provenance for task, artifact, PnL column, strategy status, and source hash.
- Internal strategy keys may remain as audit fields, but primary visible labels must be human-readable.

## Update Discipline

When a new task is added:

1. Add the row to `tasks/task_registry.csv`.
2. Generate `artifact_manifest.csv`.
3. Ensure the decision CSV has a clear strategy/data readiness status.
4. If the task should appear in Trader Dashboard performance selection, emit a trade/lifecycle-level artifact with a supported PnL column and explicit `symbol`, `theme_id`, and rationale fields when available.
5. If the task is source/infrastructure only, do not emit fake PnL columns to make it look like a performance task.

## Prohibited

- Mixing `data/backtest/trades.json` metrics with research task metrics without a visible warning.
- Treating missing labels as losses.
- Showing historical OHLCV replay as live-equivalent capture.
- Showing simulated fills as broker-truth fills.
- Hiding source blockers behind empty charts or generic dashboard cards.
