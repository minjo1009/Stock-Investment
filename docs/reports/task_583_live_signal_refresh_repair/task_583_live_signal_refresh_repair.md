# Task583 - Live Signal Refresh Repair

## Decision Summary

- decision_status=LIVE_SIGNAL_REFRESH_REPAIRED
- universe_scope=theme_10x7
- universe_coverage=FULL_UNIVERSE_EVALUATED
- evaluated_symbol_count=70/70
- fresh_rows=70
- paper_order_candidate_rows=0
- stale data cannot produce paper order candidates.

## Quant Expert Report

Task089 now feeds KIS runtime price/tick data into the decision snapshot path instead of relying only on stale daily bars.
The audit separates fresh runtime rows from stale rows and records source timestamp, source price, source type, freshness age, and stale reason.
The source inventory identifies KIS current quote, raw intraday history, daily history, and missing local source status per expected theme_10x7 symbol.
The stale source closure scoreboard names blocked symbols, owner, unblock condition, and next action without approximating missing sources.
No data_fresh manual override or dummy fallback was used.

## No-Background Decision-Maker Report

이번 단계는 주문 전 신호가 최신인지 확인하는 단계입니다.
데이터가 오래되면 주문 후보가 만들어지지 않으며, 그 이유가 artifact와 프론트엔드에 남습니다.
fresh 신호가 생겨야 다음 Task584/585에서 주문 판단과 모의 주문이 가능합니다.

## Artifact Manifest

See `artifact_manifest.csv`.
