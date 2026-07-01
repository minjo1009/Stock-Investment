# TASK-4121 L0 Stage 3 Realtime Scheduler Setup And Execution

## Goal

Execute Stage 3 of the L0/L1 source-acquisition roadmap after TASK-4120
budget optimization: prove that the real-time scheduler setup can execute
recurring cycles without opening provider collection, DB mutation, broker
mutation, replay, paper/live trading, or real-capital permissions.

## Results

- Repaired scheduler CLI compatibility: `tools.db.run_source_acquisition_once`
  now accepts the existing PowerShell runner flags `--config-path`, `--apply`,
  `--bucket`, `--json`, `--allow-network`, `--family`, `--symbol`, and
  `--macro-series`.
- Guarded the missing `tools.db.run_registered_loop_once` call behind
  `registered_loop_enabled`; the base config keeps it false.
- Built a task-local scheduler proof config and operator override under this
  report folder.
- Ran the PowerShell DB source scheduler for two forced-due cycles.
- Produced 6/6 audit-only execution artifacts for:
  - `official_news_sources_15m`
  - `gdelt_news_discovery_15m`
  - `marketaux_news_free_30m`
- Updated the six-stage management plan: Stage 3 is
  `COMPLETE_REALTIME_SCHEDULER_PROOF_EXECUTED`; Stage 4 is now `NEXT`.

## Source Direction

| Source family | Proof cadence | Proof mode | Runtime implication |
|---|---:|---|---|
| `official_public_releases` | 15m | PowerShell scheduler -> Python audit runner | Official/core API collector remains the preferred real-time primary source path. |
| `gdelt_news_events` | 15m | PowerShell scheduler -> Python audit runner | Discovery-only real-time source; not authority for strict evidence. |
| `marketaux_news_free` | 16m | PowerShell scheduler -> Python audit runner | Free-plan metadata proxy; 90 requests/day against 95/day guard. |

The proof did not run Chrome crawling. Chrome/browser collection remains
classified as smoke-only for `public_headline_browser_watch`; runtime collection
is code-based Python unless a later task explicitly approves a different mode.
Codex/GPT remains planning, recovery, and review only, not a runtime collection
engine or source of truth.

## Boundary

No persistent OS scheduled task was installed. No provider network calls were
made. No DB mutation, broker mutation, replay, paper promotion, live order, or
real-capital permission was added.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
