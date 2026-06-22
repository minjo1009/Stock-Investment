# Task 495 - Microstructure Live Source Readiness

## Quant Expert Report

- raw receive timestamp: implemented through live WebSocket archive metadata
- status/LULD: implemented as live Alpaca stock stream archive channels
- quote/spread/NBBO size: implemented through Alpaca quotes, historical and live
- full depth book: not available from Alpaca stock API; direct-depth provider integration required
- fake/inferred microstructure: NO
- Status: LIVE_QUOTE_STATUS_LULD_ARCHIVE_READY_FULL_DEPTH_PROVIDER_REQUIRED

## Source Contract

```csv
source_name,source_type,implementation_status,historical_backfill_available_flag,live_capture_available_flag,fake_or_inferred_flag,implementation_detail
raw_receive_timestamp,local_archive_metadata,implemented_in_live_archive,0,1,0,recv_ts_utc and recv_monotonic_ns are attached at WebSocket receive time.
stock_quotes_nbbo,alpaca_stock_stream,implemented_in_live_archive,1,1,0,quotes channel archived as raw JSONL with event timestamp and local receive timestamp.
stock_trading_status,alpaca_stock_stream,implemented_in_live_archive,0,1,0,statuses channel can be subscribed and archived; historical status is not reconstructed.
stock_luld,alpaca_stock_stream,implemented_in_live_archive,0,1,0,lulds channel can be subscribed and archived; historical LULD is not reconstructed.
full_depth_book,external_direct_depth_provider_required,provider_required_not_available_from_alpaca_stock_api,0,0,0,"Alpaca stock quotes provide NBBO bid/ask and size, not full depth book levels."
```

## Archive Contract

```csv
feed,symbols,channels,output_dir,archive_format,required_fields,exact_replay_note
sip,"AAPL,AMD,NVDA","quotes,statuses,lulds",data\raw\alpaca_stock_stream_archive,jsonl_partitioned_by_trade_date_channel_symbol,recv_ts_utc|recv_monotonic_ns|event_ts_utc|raw_message_json|raw_message_hash|channel|symbol,Replay may use only archived messages with recv_ts_utc <= decision_cutoff_recv_ts_utc.
```

## No-Background Decision-Maker Report

실시간 quote/status/LULD는 저장할 수 있게 만들었다. 각 메시지에는 우리가 받은 시각을 붙인다. 하지만 full depth book은 Alpaca 주식 API에 없어서 가짜로 만들지 않았다. 이건 별도 direct-depth 데이터 공급자가 필요하다.