# TASK-4173 Prime Harness Enforcement

## 결론

요청한 5개 미구현 항목을 강제 적용 단계로 올렸다.

| 항목 | 이전 상태 | 현재 상태 |
|---|---|---|
| 모든 신규 task가 contract 사용 | 권장 수준 | `create_task.py`가 `task_result_contract.yaml` 자동 생성 |
| L0~L4 전용 outcome validator | 없음 | `prime_layer_outcome_unit_validator.py` 추가 및 Prime validator에 연결 |
| closeout validator에 contract 필수화 | 없음 | `validate_codex_closeout.py`가 `validate_prime_task_contracts.py --task` 실행 |
| task 시작 시 contract 생성 | 없음 | task 생성 스크립트가 starter contract 생성 |
| task 종료 시 contract 없으면 실패 | 없음 | Prime task contract validator가 contract 누락/불일치/검증 실패를 closeout 실패로 처리 |

## 실제로 막는 것

| 차단 조건 | 처리 |
|---|---|
| TASK-4172 이후 task의 required artifacts에 `task_result_contract.yaml` 없음 | `validate_task_registry.py` 실패 |
| task contract 파일 없음 | `validate_prime_task_contracts.py` 실패 |
| contract.task_id가 registry task id와 다름 | 실패 |
| contract 자체가 Prime validator를 통과하지 못함 | 실패 |
| L0~L4 task가 허용되지 않은 outcome_unit으로 progress 주장 | 실패 |

## 주의

이번 작업은 Prime 하네스 운영 규칙을 강화한 것이다. L0~L4 데이터 문제 자체가 줄었다는 주장은 하지 않는다.
