# Task 581 - Quote Pressure x Price Response Microstructure Refinement

## Decision Summary

- task_id: Task581
- strategy_acceptance_status: DIAGNOSTIC_PASS_QUOTE_PRESSURE_PRICE_RESPONSE_TESTED
- deployment_ready_flag: 0
- diagnostic_only_flag: 1
- total_rows: 9478
- selected_rows: 2108
- quote_response_covered_rows: 9222
- trade_response_source_rows: 3168
- candidate_set_count: 5
- best_candidate_set: capital_flow_pullback_price_response
- best_count: 22
- best_avg_net: 0.11914318020137647
- best_win_rate: 0.7272727272727273
- best_entry_reduce_rate: 0.2727272727272727
- receive_ts_live_ready_flag: 0
- missing_source_approximated_flag: 0
- next_action: start_safe_kis_paper_bridge_and_live_capture

## Quant Expert Report

Task581 tests whether pre-entry NBBO pressure is confirmed by pre-entry mid/trade price response.
Historical quotes/trades are diagnostic only because receive timestamps and broker-truth fills are unavailable for this sample.
Trade response is used only when raw historical trade files exist; missing trade data is not approximated.

## No-Background Decision-Maker Report

진입 직전 호가 압력이 실제 가격 반응으로 이어졌는지 확인했다.
진입 이후 정보는 신호 생성에 쓰지 않았고, 없는 trade 데이터는 없는 것으로 보고했다.
이 결과는 한국투자 모의계좌 연결과 live receive timestamp 축적의 다음 입력이다.

## Artifact Manifest

See `artifact_manifest.csv`.
