# Universal Detail Frame V2

Every detail workspace must use this six-section frame:

1. `Decision Summary`
2. `Thesis / Logic`
3. `Validation / Readiness`
4. `Evidence`
5. `Risk`
6. `Next Action`

## Section Rules

`Decision Summary` shows the current read-only decision state and its authority.

`Thesis / Logic` explains the economic or policy reasoning without hiding source gaps.

`Validation / Readiness` shows split/OOS, leakage, cost/slippage, source freshness, and gate status when available.

`Evidence` lists source-backed observations and provenance.

`Risk` shows blockers, stale data, unknown states, exposure warnings, and kill-switch/control-state implications.

`Next Action` shows allowed next human or engineering actions. Under current governance, trading actions remain disabled.

## Current Permission Boundary

The frame may show blocked action affordances for explanation, but those affordances must remain disabled while project status is `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, and `FORBIDDEN`.

