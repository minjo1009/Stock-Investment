# TASK-4172 Prime Outcome Harness Bootstrap

## 결론

GPT Pro 검수안 기준으로 전체 Prime 하네스의 1차 구현을 완료했다.

이번 작업은 L0~L4 문제 자체를 줄였다고 주장하지 않는다. 한 일은 “앞으로 문제 해결 없이 보고서만 쓰고 닫는 closeout”을 막는 공통 계약과 validator를 만든 것이다.

## 구현 내용

| 영역 | 구현 |
|---|---|
| 공통 계약 | `task_result_contract` 개념과 task type/verdict 규칙 문서화 |
| 템플릿 | 새 작업 시작/종료 때 채울 YAML 템플릿 추가 |
| 스키마 | Prime task result contract JSON schema 추가 |
| Validator | task type, verdict, baseline/after delta, evidence, scope, safety, missing-data semantics 검증 |
| Prevention fixtures | 정상 3개, 비정상 7개 fixture 추가 |
| Tests | 비정상 closeout이 실제로 실패하는 pytest 추가 |

## 차단하는 패턴

| 패턴 | 차단 여부 |
|---|---:|
| 보고서만 쓰고 실제 outcome delta 없이 `ACTUAL_PROGRESS` 주장 | 차단 |
| baseline 없이 after만 보고 진행 주장 | 차단 |
| `DIAGNOSTIC_ONLY`가 실제 문제 해결을 주장 | 차단 |
| `HARNESS_BOOTSTRAP`이 L0~L4 blocker 개선을 주장 | 차단 |
| deployment/live/order 권한 상승 주장 | 차단 |
| task scope 밖 파일 변경 | 차단 |
| missing/stale/incomplete 데이터를 부정 증거로 사용 | 차단 |

## 남은 일

이 하네스는 공통 골격이다. 다음 작업부터는 각 도메인별로 “무엇이 줄어야 실제 진전인가”를 outcome unit으로 박아야 한다.

예: L0 failed shard count, unmapped ticker count, unsupported relation count처럼 하나씩 baseline/after/validator를 붙여서 burn-down해야 한다.
