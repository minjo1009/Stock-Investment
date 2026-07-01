# L0 Collection Status

- Updated at: 2026-06-29T06:43:37.553284Z
- Status: DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY

## Management Plan
- Plan status: PRESENT
- Active task: TASK-4117
- Roadmap: docs/architecture/l0_source_acquisition_project_management_plan.md
- Stage count: 6, blocked stages: 5
- Next stage: 1 official_core_api_smoke_stabilization status=NEXT
- Runtime collection mode: python_collectors=8, chrome_smoke_only=['public_headline_browser_watch'], codex_gpt_role=planning_review_recovery_only_not_runtime_collection

## Background
- daily: pid=10804 running=False started_at=2026-06-28T02:22:34Z
- daily_shards: workers=4 running=0
- five_min: pid=12680 running=False started_at=2026-06-28T07:16:29Z
- news: pid=16056 running=False started_at=2026-06-28T07:18:13Z
- public_newswire: pid=9456 running=False started_at=2026-06-28T21:52:31Z
- public_newswire_backfill: pid=16756 running=False started_at=2026-06-28T21:52:36Z
- public_context_news: pid=23960 running=False started_at=2026-06-28T19:29:58Z
- public_context_news_backfill: pid=21940 running=False started_at=2026-06-28T19:30:03Z
- public_market_macro_news: pid=8052 running=False started_at=2026-06-28T22:27:49Z
- public_market_macro_news_backfill: pid=3504 running=False started_at=2026-06-28T22:27:50Z
- public_industry_dive_news_backfill: pid=22692 running=False started_at=2026-06-28T21:08:56Z
- keep_awake: detected_running=False detected_pids=[] recorded_pid=18532 recorded_pid_running=False

## Bars
- Daily: 11963/12040 symbols, progress=99.3605%, files=11963, failed=0, rate_limited=0.
- 5m: progress=5.4054%, processed_events=20876, failed=115, rate_limited=0, observed_rpm=18.2338.
- market_bars_5m: rows=3151185, symbols=186, range=2020-07-27T13:00:00Z to 2026-06-26T20:04:59Z.
- 1m: included=False, status=NOT_IN_CURRENT_L1_L2_MINIMUM_SCOPE, estimated_rows_upper_bound=12847161600.
- 1m rationale: Current L1/L2 consumers are wired to daily CSV and trading.db::market_bars_5m. Full-universe 1m bars are about 5x the 5m request and storage surface, so they were excluded from the minimum required backfill while quote/trade ticks are postponed.

## News And Reference
- News: processed=14150, exported=13907, failed=127, GDELT cursor=20160524233000, Marketaux cap date=2026-06-28.
- Reference: status=PRIMARY_PASS, exported=5, failed=0, raw_dir=data\raw\l0_reference.

## News By Source
- Official: status=ENABLED_ENDPOINT_REFRESH_DONE_WITH_RETRYABLE_FAILURES, endpoint_refresh=7/7 (100.0%), symbols_with_known_endpoint=1, missing_symbols=12040, latest_statuses=EXPORTED:5, FAILED_RETRYABLE:2.
- GDELT: status=RUNNING, chunks=13918/367872 (3.7834%), cursor=20160524233000, event_statuses=EMPTY_PROVIDER_RESPONSE:20, EXPORTED:13898, SKIPPED_EXISTS:1.
- Marketaux: status=DAILY_CAP_EXHAUSTED_WAITING_NEXT_UTC_DAY, units=94/26499 (0.3547%), window_start=2016-01-01, symbol_index=470, page=1, daily_cap=95, cap_date=2026-06-28, event_statuses=CREDENTIAL_BLOCKED:1, EMPTY_PROVIDER_RESPONSE:94, RATE_LIMITED:123.
- Newswire: status=PRIMARY_PASS, sources=3/3 (100.0%), rows=4750, l1_ready_discovery=2186, l1_context_ready=919, l1_blocked=2564, event_statuses=EMPTY_PROVIDER_RESPONSE:16, EXPORTED:95.
- Newswire backfill: status=RUNNING, archives=1761/4099 (42.9617%), pending_archives=2338, unavailable_archives=1740, active_offsets=3, rows=15970, l1_ready_discovery=3611, l1_context_ready=965, l1_blocked=12359, event_statuses=EMPTY_PROVIDER_RESPONSE:12, EXPORTED:177.
- Context news: status=PRIMARY_PASS, sources=17/17 (100.0%), rows=3598, l1_ready_discovery=3598, l1_context_ready=3332, l1_blocked=0, backfill_status=SUPPORTED_FOR_FEDERAL_REGISTER_FEDERAL_RESERVE_CFTC_AND_WORLDBANK_ARCHIVES, event_statuses=EMPTY_PROVIDER_RESPONSE:1, EXPORTED:243, FAILED_RETRYABLE:1.
- Context news backfill: status=RUNNING, units=79/149 (53.0201%), pending_units=70, active_page_offsets=2, rows=125115, l1_ready_discovery=125115, l1_context_ready=116847, l1_blocked=0, event_statuses=BACKFILL_COMPLETE:205, EXPORTED:171.
- Market/macro news: status=PRIMARY_PASS, sources=68/68 (100.0%), rows=17820, l1_ready_discovery=17820, l1_context_ready=17820, l1_blocked=0, event_statuses=EXPORTED:598, FAILED_RETRYABLE:1.
- Market/macro news backfill: status=RUNNING, units=760/2611 (29.1076%), pending_units=1851, active_page_offsets=41, rows=96246, l1_ready_discovery=96246, l1_context_ready=96246, l1_blocked=0, event_statuses=BACKFILL_COMPLETE:3, EMPTY_PROVIDER_RESPONSE:1, EXPORTED:307, FAILED_RETRYABLE:9.
- Industry Dive backfill: status=RUNNING, units=11/2338 (0.4705%), pending_units=2327, active_page_offsets=17, rows=983, l1_ready_discovery=983, l1_context_ready=983, l1_blocked=0, event_statuses=EXPORTED:51.

## Postponed
- Quote/trade ticks: status=STOP_REQUESTED, stop_file_exists=True, processed_chunks=1727.
