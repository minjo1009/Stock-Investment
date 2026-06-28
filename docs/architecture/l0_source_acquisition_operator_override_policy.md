# L0 Source Acquisition Operator Override Policy

## Decision

The repository default is `conservative_default`. News and microstructure jobs are disabled, network access is disabled, and all trading permissions remain closed.

Operator enablement is local-only:

- Base config: `configs/db_source_acquisition_scheduler.json`
- Local override path: `configs/local/db_source_acquisition_scheduler.override.json`
- Example template: `configs/local_templates/db_source_acquisition_scheduler.override.example.json`

`configs/local/` is gitignored and must not contain committed secrets or operator runtime state.

## Allowed Override Scope

An operator override may change only collection posture fields:

- `enabled`
- `allow_network`
- `interval_minutes`
- `symbols`
- `macro_series`
- `feed`
- `mode`
- bounded batch limits such as `max_symbols`, `max_dates`, `max_chunks`, and `max_requests_per_minute`

The override loader writes `data/artifacts/l0_source_acquisition/effective_scheduler_config_audit.json` with enabled jobs, network jobs, enabled families, closed-permission status, preserved readiness status, and secret-detection status.

## Rejected Override Scope

The override loader rejects attempts to open:

- `execution_permitted`
- `broker_mutation_permitted`
- `paper_promotion_permitted`
- `real_capital_permitted`
- `live_order_enabled`
- `replay_permission_granted`
- `buy_sell_signal_generation_permitted`

The loader also rejects secret-like keys or values in override JSON. API keys must stay in local environment files or process environment variables, not scheduler config.

## Safety Boundary

This policy does not grant strategy acceptance. It does not grant deployment readiness. It does not grant paper trading, live trading, broker mutation, real-capital execution, replay permission, or BUY/SELL signal generation.
