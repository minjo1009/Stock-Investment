# TASK-4171 Prime Outcome Harness GPT Review

## 결론

GPT Pro 재검수 결과, 사용자의 정정이 맞다.

`blocker burn-down harness`는 L0-L4에 잘 맞는 부분집합일 뿐이고, 전체 Prime Harness의 최상위 개념은 `task_result_contract`여야 한다.

즉 모든 Codex 작업은 다음 중 하나로만 닫혀야 한다.

1. 실제 outcome이 움직였다.
2. 진단/설계/리뷰/하네스 작업이므로 underlying progress를 주장하지 않는다.

## 핵심 구조

| 개념 | 역할 |
|---|---|
| `task_result_contract` | 모든 task의 최상위 계약 |
| `outcome_unit` | 움직여야 할 단위 |
| `evidence_unit` | 움직임을 입증하는 증거 |
| `progress_claim_policy` | 이 task가 무엇을 progress라고 말할 수 있는지 제한 |
| `closeout_verdict` | 실제 진행/진단/설계/리뷰/하네스/무효 closeout 구분 |

## 중요한 교정

| 이전 좁은 해석 | 올바른 전역 해석 |
|---|---|
| blocker count burn-down | outcome contract |
| L0-L4 blocker 중심 | 모든 task domain 적용 |
| 숫자 delta만 progress | task type별 evidence-based progress |
| report-only 방지 | overclaim 전체 방지 |
| L0-L4 하네스 | Prime Harness |

## GPT 권고

다음 구현은:

`TASK-4172 Prime Outcome Harness Bootstrap`

범위:

- Prime task result contract schema
- Prime task template
- Korean closeout report format
- outcome contract validator
- report progress guard
- diagnostic/design/review/harness claim guard
- safety authority guard
- invalid/valid fixture tests

금지:

- L0-L4 blocker 직접 수정
- dashboard-first 구현
- giant platform rewrite
- strategy/deployment/paper/live/broker authority 확장

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
