# L2 News Canonical Path Report

## Decision Summary

- Verdict: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- What changed: L0 news collector events can now be transformed into canonical L2 `news_event` source receipts, primitive batches, primitive facts, lineage, and freshness rows.
- Current completion claim: news L2 canonicalization is implemented for the repo's existing L0 collector-event ledgers and JSON raw payloads. Fresh, source-time-certified news rows can flow to the L3 canonical reader; missing, lagged, blocked, or source-time-uncertified rows remain diagnostic blockers.
- Boundary: this does not parse GDELT historical archive zip payloads into row-level article facts, does not enable microstructure, and does not grant any strategy or deployment permission.
- Next action: wire an operator schedule to run `scripts/ingest_l0_news_to_l2.py` after news collection if continuous DB materialization is desired.

## Quant Expert Report

### Clarified Task List

| Task | Status | Evidence |
|---|---|---|
| Inspect existing L2 market/indicator implementation | Complete | `src/l2/live_runtime.py`, market/indicator builders, L3 reader |
| Inspect L0 news collector and L1 news evaluation | Complete | `tools/db/source_acquisition/news_background_collector.py`, `tools/db/source_acquisition/news_full_backfill.py`, `tools/db/news_l0_l1.py` |
| Define news L2 transformation plan | Complete | Collector event ledger is the source receipt; parsed rows become facts; empty or delayed events become blocker facts |
| Add news primitive builder | Complete | `src/l2/builders/news_event_primitives.py` |
| Add news runtime writer | Complete | `src/l2/news_runtime.py` |
| Add CLI materialization path | Complete | `scripts/ingest_l0_news_to_l2.py` |
| Add news canonical validator | Complete | `scripts/validate_l2_news_canonical_path.py` |
| Preserve L3 default filtering | Complete | L3 canonical reader returns only fresh, source-time-certified rows by default |
| Preserve source reliability labels | Complete | `src/brain/l3/source_reliability.py` maps `news_event` providers to existing authority classes |
| Add regression tests | Complete | `tests/test_l2_news_canonical_path.py`, `tests/test_l3_source_reliability.py` |

### Flow Implemented

`collector_events.jsonl` is treated as the L2 source receipt boundary. Each event carries provider, source id, status, raw path, raw hash, row count, and L1-ready counts.

For raw JSON payloads:

- `official_public_releases` reads `parsed_rows`.
- `gdelt_news_events` reads background API `payload.articles`.
- `marketaux_news_free` reads `payload.data` and entity symbols.

For raw payloads that are empty, missing, delayed, blocked, or not row-parsed, the writer creates a diagnostic blocker fact instead of failing the whole L2 layer. These rows keep `missing_source_is_negative=0`, `trade_output_flag=0`, `score_output_flag=0`, and `order_intent_flag=0`.

### Freshness And Blocker Semantics

- `EXPORTED` rows become `CURRENT_OR_RECENT` unless the collector timestamp is outside the configured freshness window.
- `EMPTY_PROVIDER_RESPONSE` becomes `MISSING`.
- `RATE_LIMITED`, `SKIPPED_QUERY_TOO_BROAD`, and `SKIPPED_EXISTS` become `LAGGED`.
- `CREDENTIAL_BLOCKED`, retryable failures, and other blocked states become `BLOCKED`.
- If a row has no source publication time, `source_time_certified=0`; it remains in L2 lineage but is not passed through the default L3 canonical reader.

### Provider Authority Mapping

- `official_public_releases`: `official_primary`.
- `gdelt_news_events`: `news_discovery_proxy`.
- `marketaux_news_free`: `licensed_metadata_proxy`.

These authority classes are diagnostic evidence labels, not trading authority.

### Data Source And Source Readiness

- Available raw sources: `data/artifacts/l0_news_background_queue/collector_events.jsonl`, `data/artifacts/l0_news_full_backfill/collector_events.jsonl`, and their referenced files under `data/raw/l0_news*`.
- Missing raw sources: no paid microstructure source is included; microstructure remains postponed. GDELT historical archive zip files are present but not row-parsed by this task.
- Exact join keys: not applicable to lifecycle matching. News rows are linked by `source_receipt_id`, `primitive_batch_id`, `primitive_id`, `lineage_edge_id`, `raw_path`, and `raw_sha256`.
- Leakage audit: labels, outcomes, PnL, fills, orders, and strategy acceptance data are not used.
- Split/OOS metrics: not applicable; no strategy performance claim is made.
- Cost/slippage stress: not applicable; no PnL or execution claim is made.

### Current L0 Smoke Result

The command below materialized existing L0 news events into a separate smoke DB:

`python scripts/ingest_l0_news_to_l2.py --db-path data/artifacts/task_l2_news_canonical_path/news_l2_smoke.db --event-path data/artifacts/l0_news_background_queue/collector_events.jsonl --event-path data/artifacts/l0_news_full_backfill/collector_events.jsonl --limit-per-path 50`

Result:

- Input events: 59.
- L2 `news_event` facts: 142.
- Provider counts: `official_public_releases=90`, `gdelt_news_events=51`, `marketaux_news_free=1`.
- Freshness counts: `CURRENT_OR_RECENT=138`, `BLOCKED=4`.
- L3 default canonical news inputs: 88, all from `official_public_releases`.
- Blocker-row safety check: missing-source negative sum `0`, trade output sum `0`, score output sum `0`, order-intent sum `0`.

### Validation Results

- `python -m py_compile src\l2\freshness.py src\l2\builders\news_event_primitives.py src\l2\news_runtime.py src\brain\l3\source_reliability.py scripts\ingest_l0_news_to_l2.py scripts\validate_l2_news_canonical_path.py tests\test_l2_news_canonical_path.py tests\test_l3_source_reliability.py` passed.
- `python -m unittest tests.test_l2_news_canonical_path tests.test_l2_live_runtime_canonical_path tests.test_l2_canonical_primitive_hardening tests.test_l3_source_reliability` passed: 11 tests.
- `python -m unittest tests.test_l0_news_background_collector tests.test_l0_news_full_backfill` passed: 9 tests.
- `python scripts\validate_l2_news_canonical_path.py` passed with `[L2_NEWS_OK]`.
- `python scripts\validate_l2_canonical_primitive_contract.py` passed with `[L2_CONTRACT_OK]`.
- `python scripts\validate_l2_no_trade_outputs.py` passed with `[L2_NO_TRADE_OUTPUT_OK]`.
- `python scripts\validate_l3_inputs_are_l2_canonical.py` passed with `[L3_L2_INPUT_OK]`.
- `python scripts\validate_l2_news_canonical_path.py --db-path data\artifacts\task_l2_news_canonical_path\news_l2_smoke.db` passed with `[L2_NEWS_OK]`.
- `python scripts\validate_l2_canonical_primitive_contract.py --db-path data\artifacts\task_l2_news_canonical_path\news_l2_smoke.db` passed with `[L2_CONTRACT_OK]`.
- `python scripts\validate_l2_no_trade_outputs.py --db-path data\artifacts\task_l2_news_canonical_path\news_l2_smoke.db` passed with `[L2_NO_TRADE_OUTPUT_OK]`.
- `python scripts\validate_l3_inputs_are_l2_canonical.py --db-path data\artifacts\task_l2_news_canonical_path\news_l2_smoke.db` passed with `[L3_L2_INPUT_OK]`.

### Remaining Blockers

- News L2 materialization is available through a deterministic writer and CLI, but the long-running L0 collector loop itself is not changed to mutate a DB during collection.
- Full GDELT archive zip rows are retained as L2 diagnostic lineage/blockers until a row-level archive parser is added.
- Marketaux free-tier and delayed news remain discovery metadata only.
- Microstructure is paid-only and remains postponed.
- This task does not make L2 a strategy signal, does not generate scores, and does not open any broker or capital gate.

### Safety Boundaries Preserved

This task does not grant strategy acceptance.
This task does not grant deployment readiness.
This task does not grant paper trading.
This task does not grant live trading.
This task does not permit broker mutation.
This task does not create order intent.
This task does not make L2 news a trade signal.

## No-Background Decision-Maker Report

News now has the same L2 evidence shape as the other canonical runtime data: receipt, batch, fact, lineage, freshness, and a controlled L3 reader path.

If the news collector has nothing new, is delayed, is rate-limited, or has a provider problem, L2 does not treat that as bad news about a stock. It records a blocker row and keeps moving. Only fresh rows with a real source time are allowed into the default L3 input path.

This is infrastructure readiness only. It does not approve the strategy, deployment, paper trading, live trading, broker mutation, or real capital.

## Artifact Manifest

See `artifact_manifest.csv`.

