# TASK-4144 L1/L2 Compatibility Bridge

## 결론

현재 문제는 L2 로직 자체의 실패라기보다, L1이 L2가 바로 읽을 수 있는 packet/handoff를 충분히 만들어주지 못한 호환성 gap이다. 그래서 L2가 L0 raw를 직접 읽지 않도록, L1 packet에서 온 행과 L0 audit에만 남아 있는 후보를 분리한 bridge artifact를 만들었다.

| 항목 | 값 |
|---|---:|
| l1_target_packet_rows | 3 |
| l0_audit_target_rows | 30 |
| compatibility_matrix_rows | 33 |
| l2_handoff_allowed_rows | 2 |
| l2_review_allowed_rows | 1 |
| blocked_l0_audit_candidate_rows | 30 |
| capture_only_publication_promotions | 0 |

## 처리 원칙

- L2는 L0 raw/headlines를 직접 읽지 않는다.
- capture time은 availability hint로만 남기고 publication/source time으로 승격하지 않는다.
- source time이 없는 L0 audit row는 L2-ready가 아니라 blocked/gap 후보로 둔다.
- L1 packet으로 이미 검문된 row만 L2 handoff/review 대상으로 넘긴다.
- score, signal, return, ranking, order, broker, paper/live 권한은 열지 않는다.
