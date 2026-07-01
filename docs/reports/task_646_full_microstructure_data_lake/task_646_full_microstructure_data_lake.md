# Task646 Full Microstructure Data Lake

## Decision Summary

- Verdict: `RAW_DATA_LAKE_PLAN_READY_FEATURE_BUILDER_BLOCKED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Universe symbols: 70
- Date span: 2024-01-02 to 2026-06-03
- Quote coverage: 0.0000
- Trade coverage: 0.0000
- Feature builder allowed: `0`

## Quant Expert Report

Task646 corrects the previous entry-window-only approach. It defines a full raw quote/trade data lake, a backfill command plan, a raw catalog, and a catalog/query contract. It does not build continuation features or reconnect to strategy.

### Universe Scope

| symbol | entry_row_count | first_entry_date | last_entry_date | lake_start_date | lake_end_date | source_panel | assignment_label_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AFRM | 63 | 2024-01-03 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| AMD | 96 | 2024-01-04 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| AMGN | 67 | 2024-01-02 | 2026-02-18 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| AMZN | 72 | 2024-01-10 | 2026-05-21 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ARM | 91 | 2024-01-03 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ASML | 101 | 2024-01-18 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ASTS | 90 | 2024-05-14 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| AVGO | 119 | 2024-01-04 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| BA | 47 | 2024-06-03 | 2026-05-27 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| CEG | 84 | 2024-01-22 | 2026-05-06 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| COIN | 73 | 2024-01-04 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| CRM | 50 | 2024-01-11 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| CRWD | 101 | 2024-01-08 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| DDOG | 68 | 2024-01-09 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| EMR | 83 | 2024-01-02 | 2026-04-08 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ESTC | 53 | 2024-01-11 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ETN | 95 | 2024-02-01 | 2026-05-04 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| F | 42 | 2024-01-02 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| FTNT | 75 | 2024-01-03 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GD | 41 | 2024-05-22 | 2026-03-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GE | 97 | 2024-01-08 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GEV | 127 | 2024-04-25 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GM | 56 | 2024-01-02 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GOOGL | 87 | 2024-01-03 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| GTLB | 52 | 2024-01-24 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| HON | 57 | 2024-01-02 | 2026-03-04 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| HOOD | 114 | 2024-01-04 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| IBIT | 92 | 2024-02-12 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| IR | 64 | 2024-01-02 | 2026-03-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ISRG | 63 | 2024-01-02 | 2026-04-22 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| LCID | 7 | 2025-05-12 | 2025-09-25 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| LLY | 80 | 2024-01-03 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| LMT | 51 | 2024-07-23 | 2026-02-09 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MBLY | 34 | 2024-03-21 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MDB | 58 | 2024-01-22 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| META | 75 | 2024-01-03 | 2026-05-27 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MRNA | 63 | 2024-01-02 | 2026-05-12 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MRVL | 81 | 2024-01-08 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MSFT | 68 | 2024-01-17 | 2026-05-06 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| MSTR | 85 | 2024-01-04 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NEE | 66 | 2024-01-03 | 2026-04-30 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NET | 91 | 2024-01-10 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NOC | 57 | 2024-05-13 | 2026-02-05 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NOW | 63 | 2024-01-16 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NVDA | 121 | 2024-01-08 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| NVO | 57 | 2024-01-04 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| OKTA | 43 | 2024-02-14 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ORCL | 94 | 2024-01-18 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| PANW | 88 | 2024-01-10 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| PH | 83 | 2024-01-08 | 2026-03-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| PLTR | 90 | 2024-01-22 | 2025-11-10 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| PWR | 127 | 2024-02-21 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| PYPL | 52 | 2024-01-08 | 2026-05-04 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| REGN | 61 | 2024-01-02 | 2026-03-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| RIVN | 55 | 2024-05-13 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| RKLB | 111 | 2024-01-02 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ROK | 63 | 2024-01-02 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| RTX | 64 | 2024-01-08 | 2026-02-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| S | 47 | 2024-01-03 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| SNOW | 65 | 2024-01-22 | 2026-06-01 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| SOFI | 79 | 2024-02-14 | 2025-10-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| TEAM | 52 | 2024-01-09 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| TER | 104 | 2024-01-08 | 2026-06-03 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| TSLA | 58 | 2024-06-17 | 2026-05-28 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| TSM | 121 | 2024-01-18 | 2026-06-02 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| UBER | 39 | 2024-02-13 | 2026-05-06 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| VRT | 152 | 2024-01-08 | 2026-05-14 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| VRTX | 46 | 2024-01-02 | 2026-01-08 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| VST | 104 | 2024-01-08 | 2026-01-15 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |
| ZS | 90 | 2024-01-08 | 2026-05-26 | 2024-01-02 | 2026-06-03 | docs\reports\task_636_full_period_content_prediction_backtest\task_636_entry_content_prediction_panel.csv | 0 |

### Backfill Command Plan

| provider | feed | batch_id | batch_symbol_count | start_date | end_date | source_types | command | dry_run_command | secret_in_command_flag | expected_partition_pattern |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alpaca | sip | 1 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols AFRM AMD AMGN AMZN ARM --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_001.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols AFRM AMD AMGN AMZN ARM --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_001.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 2 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols ASML ASTS AVGO BA CEG --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_002.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols ASML ASTS AVGO BA CEG --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_002.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 3 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols COIN CRM CRWD DDOG EMR --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_003.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols COIN CRM CRWD DDOG EMR --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_003.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 4 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols ESTC ETN F FTNT GD --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_004.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols ESTC ETN F FTNT GD --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_004.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 5 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols GE GEV GM GOOGL GTLB --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_005.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols GE GEV GM GOOGL GTLB --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_005.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 6 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols HON HOOD IBIT IR ISRG --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_006.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols HON HOOD IBIT IR ISRG --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_006.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 7 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols LCID LLY LMT MBLY MDB --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_007.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols LCID LLY LMT MBLY MDB --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_007.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 8 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols META MRNA MRVL MSFT MSTR --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_008.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols META MRNA MRVL MSFT MSTR --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_008.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 9 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols NEE NET NOC NOW NVDA --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_009.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols NEE NET NOC NOW NVDA --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_009.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 10 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols NVO OKTA ORCL PANW PH --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_010.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols NVO OKTA ORCL PANW PH --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_010.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 11 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols PLTR PWR PYPL REGN RIVN --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_011.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols PLTR PWR PYPL REGN RIVN --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_011.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 12 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols RKLB ROK RTX S SNOW --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_012.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols RKLB ROK RTX S SNOW --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_012.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 13 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols SOFI TEAM TER TSLA TSM --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_013.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols SOFI TEAM TER TSLA TSM --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_013.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |
| alpaca | sip | 14 | 5 | 2024-01-02 | 2026-06-03 | quotes,trades | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols UBER VRT VRTX VST ZS --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_014.csv | python -m src.data.alpaca_full_microstructure_backfill --feed sip --session regular --chunk-minutes 60 --start-date 2024-01-02 --end-date 2026-06-03 --symbols UBER VRT VRTX VST ZS --audit-out docs/reports/task_646_full_microstructure_data_lake/backfill_audit_batch_014.csv --dry-run | 0 | data/raw/microstructure_full/provider=alpaca/feed=sip/type=*/symbol=*/date=*/chunk=*.parquet |

### Raw Data Catalog

| provider | feed | source_type | symbol | date | chunk_id | path | row_count | first_timestamp | last_timestamp | sha256 | schema_columns | catalog_error | historical_live_ready_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1430_1440 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1430_1440.parquet | 29370 | 2024-01-02T14:30:00.042530597Z | 2024-01-02T14:39:59.998629008Z | 8ee6285b9e7e | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1440_1450 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1440_1450.parquet | 27355 | 2024-01-02T14:40:00.001819326Z | 2024-01-02T14:49:59.984903434Z | 9d7395f2fa8f | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1450_1500 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1450_1500.parquet | 22760 | 2024-01-02T14:50:00.000326227Z | 2024-01-02T14:59:59.842700055Z | 2a4f1c638577 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1500_1510 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1500_1510.parquet | 22806 | 2024-01-02T15:00:00.007591951Z | 2024-01-02T15:09:59.989624515Z | f6e5553f2942 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1510_1520 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1510_1520.parquet | 21288 | 2024-01-02T15:10:00.002711775Z | 2024-01-02T15:19:59.509553549Z | 87ce1b099ceb | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1520_1530 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1520_1530.parquet | 18356 | 2024-01-02T15:20:00.006010481Z | 2024-01-02T15:29:59.547685205Z | 3c1408ee3961 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1530_1540 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1530_1540.parquet | 18049 | 2024-01-02T15:30:00.000245339Z | 2024-01-02T15:39:59.996617255Z | 5ce203d7cacd | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1540_1550 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1540_1550.parquet | 17686 | 2024-01-02T15:40:00.091636105Z | 2024-01-02T15:49:59.567808237Z | af747bd618bf | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1550_1600 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1550_1600.parquet | 15070 | 2024-01-02T15:50:00.109135767Z | 2024-01-02T15:59:59.998162021Z | 326f398651f7 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AFRM | 2024-01-02 | 1600_1610 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AFRM\date=2024-01-02\chunk=1600_1610.parquet | 12277 | 2024-01-02T16:00:00.010359280Z | 2024-01-02T16:09:59.514857573Z | 9f7b5aaeed59 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | quotes | AMD | 2024-01-02 | 1430_1440 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=quotes\symbol=AMD\date=2024-01-02\chunk=1430_1440.parquet | 71421 | 2024-01-02T14:30:00.001278313Z | 2024-01-02T14:39:59.946705237Z | 0cb332cfbfa4 | symbol|quote_ts|bid|ask|bid_size|ask_size|exchange_bid|exchange_ask|quote_conditions|tape|mid|spread_bps|nbbo_size_dollar|nbbo_imbalance|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1430_1530 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1430_1530.parquet | 182016 | 2024-01-02T14:30:00.001178448Z | 2024-01-02T15:29:59.988373715Z | 203ab221af4c | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1530_1630 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1530_1630.parquet | 86874 | 2024-01-02T15:30:00.008396941Z | 2024-01-02T16:29:59.776221700Z | 279f1ea0154b | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1630_1730 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1630_1730.parquet | 57574 | 2024-01-02T16:30:00.030944926Z | 2024-01-02T17:29:59.675963929Z | 5fc1e4c163b1 | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1730_1830 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1730_1830.parquet | 48908 | 2024-01-02T17:30:00.031581635Z | 2024-01-02T18:29:59.739556358Z | a940e98357f3 | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1830_1930 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1830_1930.parquet | 48418 | 2024-01-02T18:30:00.071351379Z | 2024-01-02T19:29:59.981113713Z | 7aab0a7a4543 | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 1930_2030 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=1930_2030.parquet | 63346 | 2024-01-02T19:30:00.074443431Z | 2024-01-02T20:29:59.891278020Z | 8932e85fb081 | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |
| alpaca | sip | trades | AMD | 2024-01-02 | 2030_2100 | data\raw\microstructure_full\provider=alpaca\feed=sip\type=trades\symbol=AMD\date=2024-01-02\chunk=2030_2100.parquet | 53929 | 2024-01-02T20:30:00.003594847Z | 2024-01-02T20:59:59.999305751Z | afa096d3a442 | symbol|trade_ts|price|size|exchange|trade_id|trade_conditions|tape|source|recv_ts_utc|receive_ts_available_flag|provider|feed|source_type|partition_symbol|partition_date|partition_chunk_id|raw_interval_start|raw_interval_end|historical_live_ready_flag |  | 0 |

### Coverage Audit

| provider | feed | source_type | expected_symbol_date_count | covered_symbol_date_count | coverage_rate | missing_symbol_date_count | missing_treated_as_negative_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| alpaca | sip | quotes | 42490 | 2 | 4.706989879971758e-05 | 42488 | 0 |
| alpaca | sip | trades | 42490 | 1 | 2.353494939985879e-05 | 42489 | 0 |

### Integrity Audit

| check_name | pass_flag | bad_rows | observed_value | required_value |
| --- | --- | --- | --- | --- |
| raw_partition_catalog_nonempty | 1 | 0 | 18 partitions | at least one partition for smoke, broad coverage for Task646D |
| catalog_read_errors_zero | 1 | 0 | errors=0 | 0 catalog read errors |
| positive_row_partitions | 1 | 0 | empty_partitions=0 | all existing partitions should contain rows unless explicitly marked empty in download audit |

### Query Contract

| layer_name | allowed_operation | allowed_output | forbidden_operation | source_path | label_used_flag | strategy_assignment_used_flag |
| --- | --- | --- | --- | --- | --- | --- |
| raw_catalog_query_layer | list partitions by provider/feed/type/symbol/date | paths and row metadata | compute continuation or fragile-breakout features | data\raw\microstructure_full | 0 | 0 |
| raw_partition_reader | load exact symbol/date quote or trade parquet rows | raw normalized quote/trade rows | entry/sizing decision | data\raw\microstructure_full | 0 | 0 |

### Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| universe_scope_defined | 1 | symbols=70 | Task646 must define the exact universe and date span before download |
| raw_partition_integrity_smoke | 1 | integrity_pass=1 | catalog exists and existing partitions read cleanly |
| coverage_sufficient_for_feature_builder | 0 | quote_coverage=0.0000; trade_coverage=0.0000 | Task646D feature builder requires at least 80% quote and 80% trade symbol-date coverage |
| no_feature_builder_in_task646c | 1 | catalog/query contract only | Task646C cannot create continuation or fragile-breakout features |
| trading_promotion | 0 | data lake build only | strategy promotion requires later feature validation and live readiness |

## No-Background Decision-Maker Report

- 이번 작업은 매매 룰이 아닙니다.
- 먼저 전체 호가/거래 데이터 창고를 만드는 작업입니다.
- 646C는 feature가 아니라 catalog/query까지만 허용합니다.
- coverage가 충분해지기 전에는 `real_continuation`이나 `fragile_breakout`을 다시 만들면 안 됩니다.

## Operational Update

- 2026-06-08: The live Task646 backfill runner was upgraded from a single worker to 3 bounded workers.
- The runner now uses one shared request rate limiter set to 150 requests per minute by default.
- Existing chunk files are still skipped, failed chunks remain retryable on rerun, and audit rows are written after each partition.
- This changes download throughput only. It does not promote any trading strategy or allow Task646D features before coverage gates pass.

## Artifact Manifest

- `task_646_gpt_design_packet.txt`
- `task_646_gpt_design_response.md`
- `task_646_universe_scope.csv`
- `task_646_backfill_command_plan.csv`
- `task_646_raw_data_catalog.csv`
- `task_646_coverage_audit.csv`
- `task_646_integrity_audit.csv`
- `task_646_catalog_query_contract.csv`
- `task_646_pass_fail_matrix.csv`
- `task_646_decision.csv`
- `artifact_manifest.csv`
