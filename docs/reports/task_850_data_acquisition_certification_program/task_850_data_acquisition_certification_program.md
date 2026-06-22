# Task850 Data Acquisition Certification Program

## Decision Summary

- Verdict: open Task850-Task859 as the data acquisition and certification extension of Task840-Task849.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key metrics: existing candidate inventory contains 23 daily Yahoo CSV symbols, 513 daily breadth CSV files, 170 intraday CSV files, and Alpaca SIP historical parquet for AFRM and AMD.
- What changed: the program now defines the required data families, structures, periods, reuse-vs-redownload decision tree, and market data gate handoff path before any controlled replay can run.
- Next action: Task851 defines required data; Task852 audits existing data; Task853 creates the canonical certification manifest.

## Quant Expert Report

### Required Data Families

| family | required_for_first_controlled_replay | minimum use | target period | required structure |
| --- | --- | --- | --- | --- |
| `daily_ohlcv_adjusted` | yes | split/OOS regime context, daily bars, corporate-action-safe replay | `2021-01-01` through latest certified completed US session | one row per symbol/session date with explicit symbol, OHLCV, adjustment policy, source id, raw hash |
| `intraday_15m_bars` | yes | tradable-after entry windows and execution-timing replay | `2024-01-02` through latest certified completed US session for first controlled replay; extend to `2023-01-01` when feasible | one row per symbol/bar interval with UTC start/end, session date, session label, OHLCV, source id, raw hash |
| `market_calendar` | yes | tradable-after timestamp resolution | `2021-01-01` through latest certified completed US session plus next 30 calendar days | exchange session date, open/close UTC, early close flag, holiday flag |
| `corporate_actions` | yes for adjusted replay claim | split/dividend adjustment proof | same as daily coverage | symbol, action date, action type, factor/source, source hash |
| `symbol_master` | yes | no filename-only or proximity symbol inference | all certified symbols | symbol, exchange, asset type, active interval, source |
| `point_in_time_universe` | yes | survivorship-bias control | same as replay period | universe id, membership date, availability timestamp, inclusion reason |
| `benchmark_context` | yes | market/sector context only | same as daily and 15m where used | SPY, QQQ, SMH/SOXX, XLK, IWM, TLT if explicitly listed in universe manifest |
| `microstructure_quotes_trades` | no for first controlled replay | research-only slippage diagnostics after replay skeleton is stable | event windows only, not full-universe first replay | provider/feed/type/symbol/date/chunk with quote/trade ts and no live-ready claim |

### Canonical Bar Structure

Required canonical market bar columns:

```text
dataset_id
source_provider
source_family
granularity
symbol
exchange
ts_start_utc
ts_end_utc
session_date
session_label
open
high
low
close
volume
vwap
trade_count
adjustment_policy
adjusted_flag
corporate_action_source_id
source_file_path
source_file_sha256
ingestion_ts_utc
data_available_ts_utc
schema_version
schema_fingerprint
certification_state
certification_blocker
```

Allowed `certification_state` values:

```text
certified_for_controlled_replay
certified_reference_only
blocked_missing_adjustment_proof
blocked_missing_symbol_namespace
blocked_mixed_schema
blocked_coverage_gap
blocked_timestamp_policy
blocked_source_unknown
```

### Existing Data Preliminary Classification

| existing path | preliminary class | keep/delete | reason |
| --- | --- | --- | --- |
| `data/raw/us_daily` | `reference_or_smoke_candidate` | keep | clean schema with symbol and adj_close, but only 23 symbols and Yahoo adjustment policy needs proof |
| `data/raw/us_daily_breadth_top500` | `daily_replay_candidate_pending_manifest` | keep | broad 513-file coverage, clean schema, but no symbol column and adjustment policy unclear |
| `data/raw/us_intraday` | `15m_replay_candidate_pending_normalization` | keep | broad 170-file intraday coverage, but mixed schema and session/timezone policy needs proof |
| `data/raw/microstructure_full` | `microstructure_research_only_pending_scope` | keep | strong parquet partitioning, but only AFRM/AMD and historical flags are not live-ready |

### Reuse vs Redownload Decision

Do not delete existing data. Do not redownload everything by default.

Reuse existing raw data when all are true:

- source family and provider are identified;
- symbol namespace is explicit in the row or certified manifest;
- point-in-time universe membership is defined for any universe-level claim;
- timestamps are sorted, duplicate-free, and mapped to a session calendar;
- data availability timestamp is defined for every replay join;
- coverage satisfies the harness universe and period;
- adjustment policy is proven or the dataset is explicitly unadjusted and not used for adjusted replay;
- source file hashes are recorded.

Redownload only the failing slice when any of these remain unresolved after audit:

- split/dividend adjustment cannot be proven for a family that claims adjusted replay;
- harness symbols or dates are missing;
- mixed schema cannot be normalized without losing required fields;
- timestamps cannot be mapped to regular-hours/session policy;
- provider/source cannot be identified;
- corporate-action source cannot be attached.

### First Controlled Replay No-Go Gates

The first controlled replay remains no-go if any gate below fails:

- no certified market data manifest;
- no point-in-time universe or explicit harness universe;
- no regular-session calendar id and version;
- no corporate-action proof for adjusted replay;
- daily and 15m adjustment policies conflict;
- 15m schema remains mixed without an exact normalization map;
- symbol is missing and only filename/path inference is available;
- raw source checksum is missing;
- OOS split and final holdout are not frozen before results;
- microstructure is required as a common input for the first replay.

### GPT / Expert Panel Review Packet

Review roles assigned for Task850:

| role | review focus | authority |
| --- | --- | --- |
| Goldman-style institutional quant | whether period, universe, split/OOS, cost/slippage data are sufficient | review-only |
| BofA-style market strategist | whether sector/benchmark context is enough for macro-theme candidate bundles | review-only |
| JPM-style risk reviewer | whether data readiness wording overclaims acceptance | review-only |
| Morgan Stanley-style execution reviewer | whether 15m and microstructure scope are overfit-prone | review-only |
| Citadel-style data engineer | whether manifest/hash/schema controls prevent silent data drift | review-only |
| political expert | whether policy-event bundles need event timestamp precision | review-only |
| macro expert | whether macro context belongs in first replay or later feature panel | review-only |
| semiconductor expert | whether SMH/SOXX/NVDA/AMD/TSM context should be explicit | review-only |
| AI sector expert | whether AI capex baskets require infrastructure/utility context | review-only |
| space industry expert | whether RKLB/ASTS/LUNR/defense benchmarks need universe inclusion | review-only |

GPT/Chrome or agent review is not source-of-truth. Final authority remains repo-native manifests, validators, and explicit user approval.

### Expert Review Synthesis

The review panel converged on four upgrades:

1. Require point-in-time universe data before any universe-level backtest claim.
2. Require calendar, corporate-action, data-availability, and schema-fingerprint fields in the certification manifest.
3. Keep Alpaca SIP parquet out of the first controlled replay; use it later for narrow slippage diagnostics only.
4. Treat Task859 as `MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY` unless every required data gate passes.

## No-Background Decision-Maker Report

- What happened: the data work was converted into a 10-task program, not a broad redownload.
- Why it matters: the next bottleneck is not lack of data; it is certifying which existing data can safely feed the first controlled replay.
- Whether this changes capital/deployment readiness: no. `NOT_ACCEPTED`, `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`, and `FORBIDDEN` remain.
- Plain-language next step: audit existing data, certify usable slices, and redownload only proven gaps.

## Artifact Manifest

- Inputs: Task840-849 harness gate state; existing raw market data inventory observations.
- Outputs: Task850-859 plan tables, data requirement contract, period/universe contract, decision tree, subagent packet plan.
- Row counts: see CSV artifacts in this directory.
- Validation command: `python scripts/trader_brain_850_859_data_program_validate.py`.
- Source hashes: generated in `artifact_manifest.csv`.
