# TASK-4171 GPT Response

## 핵심 3줄

1. `blocker`는 전체 Prime Harness의 최상위 개념으로는 너무 좁다.
2. 최상위 추상화는 `task_result_contract`가 맞고, `outcome_unit`은 그 계약 안에서 움직여야 할 단위다.
3. 다음 구현은 `TASK-4172 Prime Outcome Harness Bootstrap`으로, 실제 L0-L4 문제 해결이 아니라 invalid closeout을 막는 스키마/검증기/fixture/test를 만드는 bounded harness task가 맞다.

## 올바른 추상화

| 후보 | 판단 |
|---|---|
| `blocker` | L0-L4, scheduler, data quality에는 맞지만 UI/docs/research/GPT review/harness에는 좁음 |
| `outcome_unit` | 무엇이 움직였는지는 표현하지만 진단/설계/리뷰/harness 작업의 claim 통제가 약함 |
| `evidence_unit` | 증거는 표현하지만 무엇의 진행을 입증하는지 빠짐 |
| `task_result_contract` | task type, domain, outcome unit, baseline, evidence, allowed/forbidden claim, closeout verdict를 함께 묶을 수 있음 |

결론:

```text
task_result_contract
  ├─ task identity
  ├─ task type
  ├─ domain
  ├─ outcome_unit
  ├─ baseline
  ├─ intended_change
  ├─ measurement_method
  ├─ allowed_actions / forbidden_actions
  ├─ evidence_artifacts
  ├─ validators
  ├─ progress_claim_policy
  ├─ closeout_verdict
  └─ next_target
```

## Universal Task Type

| task_type | 의미 | underlying progress claim |
|---|---|---|
| `OUTCOME_CHANGE` | 실제 outcome unit을 움직임 | 가능 |
| `TERMINALIZE` | pending/stale/retryable을 terminal state로 확정 | 가능, terminal 범위 내 |
| `RECLASSIFY` | unknown/unmapped/unsupported 등을 근거 있게 재분류 | 가능, reclassification 범위 내 |
| `DIAGNOSTIC_ONLY` | 원인/범위/재현 조건 확정 | 금지 |
| `HARNESS_BOOTSTRAP` | schema/validator/fixture/guard 구축 | underlying progress claim 금지 |
| `EXPLORATORY_RESEARCH` | 출처 조사, claim/source gap 식별 | 금지 |
| `DESIGN_ONLY` | 설계/계약/ADR 작성 | 금지 |
| `REVIEW_ONLY` | GPT/patch/acceptance review | 금지 |

## Domain별 Outcome Unit 예시

| Domain | 대표 outcome_unit | 유효한 progress claim | 무효한 progress claim |
|---|---|---|---|
| code bug fix | failing_test_count, repro_case_status | failing test before fail -> after pass | 코드 수정/로그 추가만 |
| backend/data pipeline | blocked_rows, unmapped_rows, coverage_gap_rows | 같은 query 기준 row/state count 개선 | validator만 PASS |
| scheduler/ops | pending_jobs, stale_jobs, retryable_jobs, runtime | pending/stale/retryable 감소 또는 terminalized | ETA 보고만 |
| UI/frontend | ui_defect_count, visual_diff_status | viewport/route defect 해결 | CSS 리팩터만 |
| docs/governance | stale_doc_violations, registry_mismatch_count | stale doc/registry mismatch 감소 | 새 문서 추가만 |
| quant/research | claim_source_gap_count, unsupported_claim_count | 출처 없는 claim 감소 | narrative 강화만 |
| GPT review | unresolved_p0_count, next_task_contract_status | P0/P1/P2와 next bounded task 명확화 | 긴 설명 |
| harness/bootstrap | invalid_closeout_cases_blocked | report-only closeout을 validator가 차단 | 원칙 문서만 |
| trading-system safety | safety_violation_count, forbidden_authority_exposure | hard state 차단 유지 | strategy/paper/live readiness 암시 |

## Prime Closeout Verdict

| Verdict | 의미 | underlying progress claim |
|---|---|---|
| `ACTUAL_PROGRESS` | outcome_unit이 측정 가능하게 움직임 | 가능 |
| `ACTUAL_PROGRESS_WITH_RESIDUAL_BLOCKERS` | 일부 개선됐지만 blocker가 남음 | 가능, 범위 제한 |
| `VALID_TERMINALIZATION` | pending/stale/retryable 등이 terminal state로 정리됨 | 가능, terminal 범위 내 |
| `VALID_RECLASSIFICATION` | unknown/unmapped 등이 근거 있게 재분류됨 | 가능, reclassification 범위 내 |
| `VALID_DIAGNOSTIC_ONLY` | 원인/범위/재현 조건만 확정 | 금지 |
| `VALID_DESIGN_ONLY` | 설계/계약/ADR만 확정 | 금지 |
| `VALID_REVIEW_ONLY` | 리뷰 verdict와 next task만 확정 | 금지 |
| `VALID_HARNESS_BOOTSTRAP` | harness guard/test가 생김 | underlying problem progress 금지 |
| `BLOCKED_BY_UPSTREAM` | 상위 입력/데이터가 없어 진행 불가 | 금지 |
| `INVALID_CLOSEOUT` | 증거/baseline/scope/claim 위반 | 금지 |

## Prime Validators / Guards

| Validator | 목적 |
|---|---|
| `outcome_contract_validator` | task_result_contract 필수 필드, task_type/verdict 호환성 검증 |
| `evidence_delta_validator` | OUTCOME_CHANGE/TERMINALIZE/RECLASSIFY의 before/after/evidence 검증 |
| `report_progress_guard` | report claim이 evidence보다 과장되지 않도록 차단 |
| `diagnostic_only_guard` | diagnostic/design/review가 actual progress 주장하지 못하게 함 |
| `upstream_dependency_gate` | missing/stale/incomplete를 negative evidence로 쓰지 못하게 함 |
| `safety_authority_guard` | trading safety hard state 위반 차단 |
| `stale_baseline_guard` | 오래된 baseline으로 progress 주장 방지 |
| `scope_guard` | 허용 범위 밖 변경 방지 |
| `terminal_state_validator` | TERMINALIZE status 정합성 검증 |
| `reclassification_integrity_guard` | reclassify가 blocker 은폐가 아닌지 검증 |
| `research_source_gap_validator` | source gap, fact/inference 분리 검증 |
| `ui_evidence_guard` | UI 변경에 screenshot/e2e/viewport 증거 요구 |
| `harness_prevention_test_guard` | invalid closeout fixture가 실제 실패하는지 검증 |

## GPT Review Rubric

GPT 리뷰는 앞으로 아래를 먼저 물어야 한다.

1. 이 task의 `task_type`은 무엇인가?
2. 이 task가 claim할 수 있는 progress 범위는 어디까지인가?
3. `outcome_unit`은 무엇인가?
4. baseline은 있는가?
5. before/after measurement는 같은가?
6. 증거 artifact가 존재하는가?
7. report가 evidence보다 과장되었는가?
8. hard safety state를 위반했는가?
9. next target이 concrete한가?

GPT verdict:

- `PASS_ACTUAL_PROGRESS`
- `PASS_DIAGNOSTIC_ONLY`
- `PASS_DESIGN_ONLY`
- `PASS_REVIEW_ONLY`
- `PASS_HARNESS_BOOTSTRAP`
- `CONDITIONAL_PASS`
- `FAIL_INVALID_CLOSEOUT`
- `FAIL_SAFETY_P0`

## Immediate Implementation

추천 작업:

`TASK-4172 Prime Outcome Harness Bootstrap`

목표:

- Prime harness의 최소 outcome contract, closeout report format, validator, invalid/valid fixtures, tests를 만든다.
- 실제 L0-L4 blocker를 직접 줄이지 않는다.
- 이 작업은 `HARNESS_BOOTSTRAP`이며, `VALID_HARNESS_BOOTSTRAP`으로 닫아야 한다.

권장 산출물:

- `docs/harness/prime_outcome_harness.md`
- `docs/harness/prime_task_template.yaml`
- `docs/harness/prime_closeout_report_format.md`
- `schemas/prime_task_result_contract.schema.json`
- `src/validation/prime_outcome_contract_validator.py`
- `tests/test_prime_outcome_contract_validator.py`
- `tests/fixtures/prime_contracts/*.yaml`

필수 테스트:

- valid OUTCOME_CHANGE fixture passes
- OUTCOME_CHANGE without baseline fails
- OUTCOME_CHANGE without after/evidence fails
- DIAGNOSTIC_ONLY with ACTUAL_PROGRESS verdict fails
- DESIGN_ONLY claiming underlying fix fails
- REVIEW_ONLY claiming implementation fixed fails
- HARNESS_BOOTSTRAP valid fixture passes
- HARNESS_BOOTSTRAP claiming L0-L4 blocker reduction fails
- safety authority violation fails
- forbidden scope/action fails
- report-only closeout fails
- missing/stale/incomplete data treated as negative evidence fails

## Final Judgment

Prime harness는 다음 계층이어야 한다.

```text
Prime Harness
  ├─ Task Intake Contract
  ├─ Execution Guard
  ├─ Evidence Contract
  ├─ Closeout Guard
  ├─ Safety Guard
  └─ GPT Review Rubric
```

최종 원칙:

> 모든 작업은 “실제 outcome이 움직였는가?” 또는 “진단/설계/리뷰/하네스였으므로 underlying progress를 주장하지 않는가?” 둘 중 하나로만 닫혀야 한다.
