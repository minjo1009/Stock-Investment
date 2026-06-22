# Task2121-2150 Free API Full Capture Proxy Replay

## Decision Summary

- Verdict: `free_api_capture_proxy_replay_complete_diagnostic_only`.
- Scope symbols: 48.
- API call rows: 384.
- Downloaded or reused rows: 129.
- Blocked rows: 260.
- Feature rows: 377.
- Replay policy: `free_api_proxy_top5_to_top2_convex_v1`.
- Final equity: 7819.4258.
- CAGR: 0.489592.
- MDD: -0.334944.
- Baseline: `winner_accel_top5_to_top2_convex_v1` final 7816.28, CAGR 0.489476, MDD -0.334944.
- Delta final equity: 3.1458.
- Strict transcript gate pass rows: 0.
- Strict analyst PIT gate pass rows: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task uses the newly provided free API keys with a fixed acquisition rule:

1. Capture raw JSON, hash it, and store a sanitized call ledger.
2. Treat free transcript and analyst-like data as proxy-only unless publication/provider availability and revision timestamps are certified.
3. Build L1/L2/L3/L4 proxy features from captured source fields only.
4. Run one controlled diagnostic replay using the existing frozen winner-acceleration candidate pool and source replay returns.

The replay is diagnostic only. It does not prove paper readiness because transcript and analyst PIT gates remain closed.

## No-Background Decision-Maker Report

1. 무료 API로 받을 수 있는 건 최대한 받았다.
2. 받은 건 원문 raw와 hash로 남겼다.
3. transcript/analyst strict gate는 아직 안 열었다.
4. 무료 API 데이터는 보조 점수로만 넣었다.
5. 그 점수로 다시 top2를 고르는 백테스트를 돌렸다.

## Artifact Manifest

- `task2121_provider_capability_gate.csv`
- `task2122_api_call_ledger.csv`
- `task2123_api_normalized_sources.csv`
- `task2124_l1_api_proxy_features.csv`
- `task2125_l2_api_proxy_semantics.csv`
- `task2126_l3_api_proxy_edges.csv`
- `task2127_l4_api_proxy_score_cards.csv`
- `task2128_api_proxy_replay_trades.csv`
- `task2129_api_proxy_replay_equity.csv`
- `task2130_api_proxy_replay_metrics.csv`
- `task2150_closeout.csv/json`

This task does not change strategy acceptance.
This task does not change deployment readiness.
This task does not permit real capital.
