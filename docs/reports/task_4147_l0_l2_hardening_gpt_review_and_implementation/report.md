# TASK-4147 L0-L2 Production Hardening

## 결론

TASK-4147은 L0 raw를 L1/L2가 더 넓게 먹도록 만드는 보강 작업이다. 기존 4146의 batch-level handoff 위에 article-level packet, 뉴스와이어 mapping proof, 안전한 실시간 config, 15분 durable loop, backfill proof, diagnostic feature schema를 추가했다.

| 항목 | 값 |
|---|---:|
| l1_article_packets | 6036 |
| l1_article_ready_packets | 6036 |
| raw_article_packet_blockers | 0 |
| newswire_mapping_queue_rows | 6447 |
| newswire_l0_mapped_rows | 126540 |
| l2_diagnostic_feature_rows | 4959 |
| backfill_proof_rows | 5 |
| trading_eligible_rows | 0 |
| signal_order_export_allowed_rows | 0 |
| broker_mutation_permitted_rows | 0 |

## 중요한 해석

- L1은 이제 batch 하나가 아니라 raw 기사/행 하나를 packet으로 만들 수 있다.
- L2 diagnostic feature row는 실제 schema row지만 trading feature/signal/order는 아니다.
- 뉴스와이어 raw가 느리거나 hydrate되지 않는 경우 15분 loop를 막지 않고 review/blocker 증거로 남긴다.
- L0 실시간 collector용 config는 별도 파일로 분리했고 기존 보수 config를 직접 enable하지 않았다.
- Windows Task Scheduler 등록 증거는 `windows_task_scheduler_registration.json`에 남긴다.
