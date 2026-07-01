# TASK-4170 Blocker Burn-down Harness GPT Review

## 결론

GPT Pro 검수 결과, 반복 문제의 근본 원인은 “분석 부족”이 아니라 “작업 종료 계약 부재”다.

앞으로 Codex 작업은 `상태 보고 -> 검수 -> 보고서`가 아니라 `blocker_family 선택 -> before_count 고정 -> 작업 -> after_count 측정 -> delta/terminal/reclass 검증`으로 닫아야 한다.

## 핵심 변경 방향

| 항목 | 기존 | 변경 |
|---|---|---|
| 완료 기준 | validator PASS, report 작성 | blocker count 감소 / terminal 처리 / reclassification |
| 보고서 첫 줄 | L0-L4 전체 상태 | 이번에 몇 개 줄었는가 |
| GPT 검수 | 방향성 검토 | before/after/delta 검증 |
| 반복 방지 | 없음 | upstream dependency gate |
| 진단 작업 | progress처럼 보일 수 있음 | `DIAGNOSTIC_ONLY`, progress 아님 |

## GPT가 요구한 하네스

1. Mandatory blocker burn-down task template
2. Blocker taxonomy registry
3. Burn-down ledger
4. Before/after snapshot script
5. Delta validator
6. Ledger validator
7. Report progress guard
8. Upstream dependency gate
9. Terminal status validator
10. No trading authority validator

## 다음 구현 권고

`TASK-4171 Blocker Burn-down Harness Bootstrap`

범위:

- template, taxonomy, ledger, snapshot, delta validator, report guard, closeout template 구현
- 실제 L0/L1/L4 blocker 해결은 하지 않음
- `HARNESS_BOOTSTRAP`으로 닫고 `blocker_progress: NO`라고 명시

그 다음 실제 burn-down:

`TASK-4172 L1_BLOCKED_UNMAPPED_ROWS_PRESENT Burn-down`

- before_count: 3,999
- baseline cohort와 L0 running 중 신규 cohort 분리
- mapped / terminalized / reclassified count로 완료 증명

## Chrome GPT

- relay mode: `single_gpt_consult`
- GPT capture status: captured
- tab cleanup status: `closed_or_released_by_finalize`

## Safety

- Strategy remains `NOT_ACCEPTED`.
- Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital remains `FORBIDDEN`.
- No broker mutation.
- No live order.
- No paper promotion.
- Missing/stale/incomplete data remains `UNKNOWN/BLOCKER`, not negative evidence.
