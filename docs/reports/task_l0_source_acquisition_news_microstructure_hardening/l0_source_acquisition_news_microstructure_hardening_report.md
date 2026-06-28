# L0 Source Acquisition News Microstructure Hardening

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed: L0 news and microstructure collection are operator-enableable, observable, checkpoint-aware, and validator-backed; an operator local override was used to run a real Alpaca IEX quote/trade smoke collection.
- Next action: review the IEX smoke evidence, then decide whether to run a bounded SIP entitlement smoke or keep IEX-only diagnostic scope.

This task does not grant strategy acceptance.
This task does not grant deployment readiness.
This task does not grant paper trading.
This task does not grant live trading.
This task does not permit broker mutation.
This task does not permit real-capital execution.
This task does not enable microstructure feature builder.

## Goal Intake Contract

| Field | Value |
|---|---|
| Objective | Make L0 news and microstructure collection operator-enableable, observable, resumable, auditable, and safe while keeping downstream trading gates closed. |
| Target Metrics | Conservative default disabled; diagnostic override template present; L1 statuses implemented; checkpoint schema present; real quote/trade smoke chunks exported; coverage artifacts present; validators pass. |
| Forbidden Actions | No broker submit, cancel, mutation, paper promotion, live order, strategy promotion, controlled replay permission, feature builder permission, BUY/SELL signal generation, missing-source approximation, or inferred lifecycle matching. |
| Available Raw Sources | Existing Alpaca historical microstructure raw files under `data/raw/alpaca_historical_microstructure`; existing Alpaca exporter `src/data/alpaca_historical_microstructure_export.py`; readiness registry and task registry. |
| Missing Raw Sources | Operator-run current news rows; SIP entitlement smoke if full-market historical coverage is required; real L2/depth provider; full live-source source-health history. |
| Owner Team | Data & Market Microstructure |
| Reviewer Team | Research Governance; Execution & Risk |
| Output Directory | `docs/reports/task_l0_source_acquisition_news_microstructure_hardening/` |
| Large Artifact Directory | `data/artifacts/l0_source_acquisition/` and `data/artifacts/microstructure/` |
| Validation | L0 validators, py_compile, management schema apply, diagnostic script, and unit tests listed below. |
| Completion Criteria | All default gates remain closed; operator diagnostic enablement is possible; real IEX quote/trade smoke chunks are checkpointed; artifacts and validators exist; report and registry are updated. |
| Failure Criteria | Any permission opens, any token is committed/logged, yfinance proxy is called orderflow, missing data is treated as negative evidence, or feature builder is enabled. |

## Quant Expert Report

### Files Changed

- Scheduler and registries: `configs/db_source_acquisition_scheduler.json`, `configs/local_templates/db_source_acquisition_scheduler.override.example.json`, `configs/source_registry/l0_official_public_releases.json`, `configs/source_registry/l0_gdelt_queries.json`, `configs/source_registry/l0_marketaux_queries.json`
- L0 tooling: `tools/db/news_l0_l1.py`, `tools/db/apply_management_schema.py`, `tools/db/run_source_acquisition_once.py`, `tools/db/run_registered_loop_once.py`, `tools/db/source_acquisition/*.py`
- Scripts: `scripts/validate_news_ops_scope_a_b.py`, `scripts/validate_l0_news_enablement_readiness.py`, `scripts/validate_l0_microstructure_collection_readiness.py`, `scripts/validate_l0_source_acquisition_hardening.py`, `scripts/diagnose_l0_microstructure_collection_state.py`, `scripts/run_task646_full_microstructure_backfill.py`
- Tests: `tests/test_db_source_acquisition_runner.py`, `tests/test_db_source_acquisition_scheduler_scripts.py`, `tests/test_l0_source_acquisition_hardening.py`
- Policy docs: `docs/architecture/l0_news_enablement_policy.md`, `docs/architecture/l0_microstructure_collection_policy.md`, `docs/architecture/l0_source_acquisition_operator_override_policy.md`

### News Changes

`official_public_releases`, `gdelt_news_events`, and `marketaux_news_free` stay disabled in the repository default with `allow_network=false`.

The local override template can enable diagnostic collection, but `execution_permitted`, `broker_mutation_permitted`, `paper_promotion_permitted`, `real_capital_permitted`, `live_order_enabled`, `replay_permission_granted`, and `buy_sell_signal_generation_permitted` stay closed.

Provider authority roles are formalized:

- `official_public_releases`: `official_primary`, structurally valid rows become `READY_DIAGNOSTIC_ONLY`.
- `gdelt_news_events`: `news_discovery_proxy`, structurally valid rows become `READY_DISCOVERY_ONLY`.
- `marketaux_news_free`: `licensed_news_metadata_proxy`, structurally valid rows become `READY_DISCOVERY_ONLY`.

Missing publication time, source URL, title, or entity/ticker mapping remains `BLOCKED`.

Marketaux hardening includes local-only token loading, metadata redaction, masking, a daily request ledger, a request cap, and a recommended 120-minute batch cadence with max 3 articles per request.

### Microstructure Changes

The scheduler now has a disabled-by-default `microstructure_backfill_batch` job with quote/trade families, `allow_network=false`, `diagnostic_only=true`, and `feature_builder_enabled=false`.

Terminology is explicit:

- `market_bar_proxy_intraday` is a bar proxy and not exchange tick truth.
- `microstructure_quotes` and `microstructure_trades` are true L0 quote/trade families.
- `microstructure_orderbook_depth` remains out of scope without a real provider.
- `broker_truth` remains separate from market microstructure.

Task646-compatible backfill is exposed through `scripts/run_task646_full_microstructure_backfill.py`. It supports `smoke`, `bounded_batch`, and `historical_backfill` modes. Dry-run does not write checkpoint rows. Actual operator execution writes chunk checkpoint rows and coverage artifacts.

Chunk checkpoint schema is available in `tools/db/source_acquisition/microstructure_checkpoint.py` with `EXPORTED`, `SKIPPED_EXISTS`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `RATE_LIMITED`, `CREDENTIAL_BLOCKED`, `EMPTY_PROVIDER_RESPONSE`, and `QUARANTINED`.

The first real network smoke completed with Alpaca IEX:

- Symbol/date/window: `AAPL`, `2026-06-26`, `2026-06-26T14:30:00Z` to `2026-06-26T14:31:00Z`.
- Quote chunk: `EXPORTED`, 2,991 rows, SHA-256 `d534a79aa3ac728fc2f7b5929a01ce184ed7f6e48b6b91d2c580333c41962e87`.
- Trade chunk: `EXPORTED`, 89 rows, SHA-256 `29bba6c2d18fc48eafa534421dc3d874c9245a3ac00cc53120d11d93c29ba6fd`.
- Coverage: quote coverage `1.0`, trade coverage `1.0`.
- Integrity: readable files, parseable timestamps, no duplicate timestamp/trade-id issue, no future data, no open-bar proxy, no yfinance proxy, no secret logged, feature builder blocked.

Coverage artifacts are generated under `data/artifacts/microstructure/`:

- `microstructure_raw_catalog.csv`
- `microstructure_coverage_by_symbol.csv`
- `microstructure_coverage_by_date.csv`
- `microstructure_coverage_by_symbol_date.csv`
- `microstructure_integrity_audit.csv`
- `microstructure_missing_reason.csv`
- `microstructure_collection_heartbeat.json`
- `microstructure_collection_failure_ledger.csv`

### Scheduler Override Policy

The common loader `tools/db/source_acquisition/scheduler_override.py` reads the base config, reads an optional local override, safely merges allowed fields, rejects permission-opening fields, rejects secret-like override fields, and writes an effective-config audit artifact.

DB reconciliation is implemented in `tools/db/apply_management_schema.py`. Conservative seed remains safe, and `apply_operator_scheduler_override()` updates only collection fields while forcing diagnostic-only and closed execution permissions.

For the real smoke run, `configs/local/db_source_acquisition_scheduler.override.json` was created locally and remains gitignored. It enables only `microstructure_backfill_batch` in `smoke` mode with `feed=iex`, `AAPL`, `max_chunks=1`, `allow_network=true`, and closed permissions. The effective audit reports `override_present=true`, `jobs_enabled=["microstructure_backfill_batch"]`, `permissions_closed=true`, `status_preserved=true`, and `secrets_detected_false=true`.

### Data Source And Source Readiness

No inferred lifecycle matching was used.
Missing labels were not treated as negatives.
Missing raw sources were reported, not approximated.
The result is diagnostic-only and `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.

Official source registry entries were externalized. Unverified MSFT, NVDA, AMD, and QQQ/Invesco entries are disabled placeholders with `TODO_VERIFY_ENDPOINT`.

### Validation Commands And Results

| Command | Result |
|---|---|
| `python -m py_compile tools/db/news_l0_l1.py tools/db/run_source_acquisition_once.py tools/db/apply_management_schema.py` | PASS |
| `python -m tools.db.apply_management_schema --apply` | PASS: `[MANAGEMENT_SCHEMA_OK] db=trading.db` |
| `python scripts/validate_news_ops_scope_a_b.py --mode conservative` | PASS: `[NEWS_OPS_SCOPE_OK] mode=conservative` |
| `python scripts/validate_news_ops_scope_a_b.py --mode news_enabled_diagnostic` | PASS: `[NEWS_OPS_SCOPE_OK] mode=news_enabled_diagnostic` |
| `python scripts/validate_l0_news_enablement_readiness.py` | PASS: `[L0_NEWS_READINESS_OK]` |
| `python scripts/validate_l0_microstructure_collection_readiness.py` | PASS: `[L0_MICROSTRUCTURE_READINESS_OK]` |
| `python scripts/validate_l0_source_acquisition_hardening.py` | PASS: `[L0_SOURCE_ACQUISITION_HARDENING_OK]` |
| `python scripts/diagnose_l0_microstructure_collection_state.py` | PASS: reports job present, disabled, `allow_network=false`, credentials present as boolean only, feature builder 0, broker mutation 0 |
| `python scripts/run_task646_full_microstructure_backfill.py --mode smoke --symbols AAPL --session-dates 2026-05-15 --feed iex --max-chunks 1` | PASS dry-run: planned 2 chunks, no network, feature builder 0, broker mutation 0 |
| `python scripts/run_task646_full_microstructure_backfill.py --mode smoke --execute --force --symbols AAPL --session-dates 2026-06-26 --feed iex --max-chunks 1 --out-dir data/raw/alpaca_historical_microstructure_smoke` | PASS real network smoke: planned 2 chunks, exported 2, failed 0, skipped 0, feature builder 0, broker mutation 0 |
| `python scripts/diagnose_l0_microstructure_collection_state.py` after smoke | PASS: latest quote/trade chunks `EXPORTED`, quote coverage `1.0`, trade coverage `1.0`, override exists, feed `iex`, feature builder 0, broker mutation 0 |
| `python -m unittest tests.test_db_source_acquisition_runner tests.test_db_source_acquisition_scheduler_scripts tests.test_l0_source_acquisition_hardening` after local override | PASS: 13 tests |
| `python -m unittest tests.test_db_source_acquisition_runner tests.test_db_source_acquisition_scheduler_scripts tests.test_l0_source_acquisition_hardening` | PASS: 13 tests |
| `python scripts/task_registry_validate.py` | PASS: `[REGISTRY_OK] tasks\task_registry.csv` |
| `python scripts/active_task_registry_validate.py` | PASS: `[ACTIVE_REGISTRY_OK] tasks\active_task_registry.csv` |
| `python scripts/codeowners_coverage_validate.py` | PASS: `[CODEOWNERS_OK] .github\CODEOWNERS` |
| `python validate_readiness_registry.py` | PASS: `[READINESS_REGISTRY_OK] docs\ownership\readiness_registry.yaml` |
| `python scripts/operating_closeout_validate.py` | PASS: `[OPERATING_CLOSEOUT_OK]` |
| `python scripts/governance_completion_audit.py` | PASS with existing warning: `[ARTIFACT_GUARD_WARN] protected DB authority not DVC-tracked: data/task388_intraday_canonical_continuation_engine.db`; final status `[GOVERNANCE_COMPLETE]` |

### Safety Boundaries Preserved

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No paper order intent was added.
- No live order path was added.
- No broker mutation path was added.
- No replay permission was added.
- No BUY/SELL signal generation was added.
- No microstructure feature builder permission was added.

### Remaining Blockers

- Alpaca IEX smoke collection completed, but SIP entitlement/full-market smoke has not been run. IEX is suitable for initial diagnostic collection, not full-market NBBO deployment evidence.
- Windows ScheduledTask existence is reported as `NOT_CHECKED_NON_MUTATING_DIAGNOSTIC`; the script does not mutate or register tasks.
- Full source scheduler lease, duplicate input hash skip, and failure-ledger-on-every-exception are documented as Phase 2 hardening outside this minimal L0 implementation.
- GDELT and Marketaux remain discovery/metadata only and cannot support thesis or trade evidence without official/source-time-certified cross-verification.
- L2 order book depth remains out of scope until a real depth provider exists.

### Next Recommended Tasks

1. Decide whether to run a bounded SIP entitlement smoke after reviewing the IEX evidence.
2. Run the news diagnostic collector from a local operator override when ready.
3. Add scheduler lease/idempotency/failure ledger hardening after the first scheduled operator loop is exercised.
4. Verify disabled official source placeholders for MSFT, NVDA, AMD, and QQQ/Invesco before enabling them.

## No-Background Decision-Maker Report

This work does not make the strategy tradable. It makes the raw data collection layer safer and more visible.

Before this task, news and microstructure collection could be confused with trading readiness or with proxy data. Now the repo default remains shut, and an operator can locally enable diagnostic collection without opening execution, paper promotion, live trading, or real-capital permissions.

The important practical result is that missing data stays a blocker instead of being guessed. GDELT and Marketaux can help discover candidate evidence, but they are not official truth. yfinance-style 5m bars are explicitly not orderflow. Alpaca quote/trade collection now has real IEX smoke evidence with checkpoint hashes and coverage artifacts.

## Artifact Manifest

| Artifact | Role |
|---|---|
| `configs/db_source_acquisition_scheduler.json` | Conservative default scheduler config |
| `configs/local_templates/db_source_acquisition_scheduler.override.example.json` | Secret-free operator override template |
| `data/artifacts/l0_source_acquisition/effective_scheduler_config_audit.json` | Effective scheduler audit |
| `data/artifacts/microstructure/microstructure_collection_heartbeat.json` | Microstructure collection heartbeat scaffold |
| `data/artifacts/microstructure/microstructure_collection_failure_ledger.csv` | Failure ledger scaffold |
| `data/artifacts/microstructure/microstructure_backfill_checkpoint.jsonl` | Real quote/trade chunk checkpoint evidence |
| `data/raw/alpaca_historical_microstructure_smoke/feed=iex/quotes/AAPL.csv` | Real Alpaca IEX quote smoke raw file |
| `data/raw/alpaca_historical_microstructure_smoke/feed=iex/trades/AAPL.csv` | Real Alpaca IEX trade smoke raw file |
| `docs/reports/task_l0_source_acquisition_news_microstructure_hardening/microstructure_smoke_collection_evidence.csv` | Compact smoke evidence table |
| `docs/reports/task_l0_source_acquisition_news_microstructure_hardening/task_l0_source_acquisition_news_microstructure_hardening_decision.csv` | Task decision |
| `docs/reports/task_l0_source_acquisition_news_microstructure_hardening/artifact_manifest.csv` | Report-directory artifact manifest |

Source hashes for report-directory artifacts are recorded in `artifact_manifest.csv`.
