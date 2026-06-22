# Task3721-3760 Source Acquisition Runtime Loop

## Decision Summary

- Verdict: `SOURCE_ACQUISITION_RUNTIME_LOOP_INSTALLED_WITH_BLOCKERS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- What changed:
  - Added governed source tables for `daily_ohlcv`, `macro_rates`, and `sec_events`.
  - Added `tools.db.run_source_acquisition_once` for provider/fixture acquisition with idempotent upserts, raw receipts, reference hashes, lineage edges, freshness rows, and scheduler ledger rows.
  - Ran actual provider acquisition for `market_bars_5m`, `market_ticks_intraday`, `daily_ohlcv`, and `macro_rates`.
  - Attached cached SEC normalized packets from Task2545 into `sec_events`.
  - Extended `tools.db.run_registered_loop_once` so all 12 registered jobs now have adapter evidence.
  - Added blocked `authority_evidence_ledger` generation and read-only frontend/catalog lineage adapters.
- Key metrics:
  - Registered jobs after closeout: 12 seen, 12 success, 0 skipped.
  - Active row counts: `market_bars_5m=31,190`, `market_ticks=5,822`, `daily_ohlcv=20`, `macro_rates=16,817`, `sec_events=138,049`.
  - Duplicate key rows: `daily_ohlcv=0`, `macro_rates=0`, `sec_events=0`.
  - Authority evidence rows: 4, latest gate remains `BLOCKED`.
  - Raw completeness: source acquisition metadata now points to full raw CSV files with `full_raw_path`, `full_raw_sha256`, `full_raw_row_count`, and `truncated_raw_rows=0`.
- Next action:
  - Add operator-owned recurring invocation for `tools.db.run_source_acquisition_once`.
  - Configure `SEC_USER_AGENT` before live SEC API acquisition.
  - Refresh indicator/runtime/broker truth paths from fresh market/source evidence.

## Quant Expert Report

### Data Source And Source Readiness

- `market_bars_5m`: yfinance 5m provider path ran for AAPL/QQQ. Rows were upserted into the existing runtime table. Freshness remains `STALE` because the latest provider bar is older than the 20-minute SLA on a weekend/closed-market run.
- `market_ticks_intraday`: yfinance latest 5m bar was used as a quote proxy. It is explicitly tagged as provider latest-bar timestamp, not exchange tick truth.
- `daily_ohlcv`: yfinance daily provider path ran for AAPL/QQQ.
- `macro_rates`: FRED CSV path ran for DGS10. No vintage certification is claimed; `vintage_ts` uses a deterministic no-vintage sentinel.
- `sec_events`: live SEC API path is implemented but skipped without `SEC_USER_AGENT`; cached Task2545 SEC normalized packets were attached as fixture/cache source evidence.
- `authority_evidence_ledger`: latest runtime decision is reviewed into blocked authority evidence. No paper/live permission is opened.
- `frontend_read_models` and `catalog_report_artifacts`: derived read-only file-hash lineage only. These are not source truth.

### Exact Join Keys

- `daily_ohlcv`: `(provider, symbol, session_date)`.
- `macro_rates`: `(provider, series_id, observation_date, vintage_ts)`.
- `sec_events`: `(provider, accession_no, form_type, event_type)`.
- `market_bars_5m`: existing key `bar_id = symbol:bar_start_ts`.
- `market_ticks`: existing key `tick_id = symbol:timestamp:yfinance`.

### Leakage Audit

- Missing sources remain neutral blockers.
- Raw provider/cached artifacts are stored with `raw_path` and `raw_sha256`.
- Large raw rows are not truncated: metadata JSON stores preview rows only and references the full raw CSV via `full_raw_path` / `full_raw_sha256`.
- Same-bucket fixture re-runs keep source table keys and evidence counts stable in package tests.
- `strict_gate_allowed=0` and `proxy_allowed=0` remain closed for all 12 freshness families.
- GPT/Chrome review was advisory only and not used as source truth.
- No replay, selector change, sizing change, broker submit, paper order, live order, or real-capital permission occurred.

### Split/OOS Metrics

Not applicable. This task is data/DB operations infrastructure only.

### Failure Decomposition

- SEC live provider is blocked until `SEC_USER_AGENT` is configured.
- Several freshness rows remain `STALE` because source timestamps are older than runtime SLA:
  - broker truth reconciliation
  - daily OHLCV
  - indicator snapshots
  - macro rates
  - market bars
  - market ticks
  - runtime strategy decisions
  - SEC events
- This is expected evidence behavior, not a failure-to-load.

### Remaining Blockers

- No operator-owned recurring source acquisition schedule is installed yet.
- Live SEC provider is not enabled without user-agent configuration.
- Broker truth is still stale.
- Runtime decisions and indicator snapshots still need fresh upstream runtime loops.
- Data freshness does not imply strategy acceptance or deployment readiness.

## No-Background Decision-Maker Report

- What happened: DB acquisition is now systematic for market bars, ticks, daily OHLCV, macro rates, SEC events, authority evidence, frontend read models, and catalog artifacts.
- Why it matters: the project now has table-level idempotent storage, raw evidence, hashes, lineage, freshness, and scheduler evidence for every registered DB job.
- Whether this changes capital/deployment readiness: no. The system remains diagnostic only.
- Plain-language next step: install the recurring source-acquisition schedule and configure live SEC user-agent before expecting SEC live refresh.

## Artifact Manifest

- Inputs:
  - `tools/db/apply_management_schema.py`
  - `tools/db/run_source_acquisition_once.py`
  - `tools/db/run_registered_loop_once.py`
  - `data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/task2545_normalized_sec_financing_dilution_packets.csv`
- Outputs:
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/artifact_manifest.csv`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/source_acquisition_provider_run.json`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/sec_events_cached_fixture_run.json`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/registered_loop_all_adapters_after_sec.json`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/source_freshness_after_closeout.csv`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/table_counts.csv`
  - `data/artifacts/task_3721_3760_source_acquisition_runtime_loop/gpt_chrome_review.md`
- Validation commands:
  - `python -m unittest tests.test_db_registered_loop_runner tests.test_db_source_acquisition_runner`
  - `python scripts/trader_brain_3721_3760_source_acquisition_runtime_loop_validate.py`
  - `python scripts/task_registry_validate.py`
  - `python scripts/operating_closeout_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
