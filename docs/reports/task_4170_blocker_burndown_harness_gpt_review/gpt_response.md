# TASK-4170 GPT Response

## 핵심 세 줄

1. 반복 원인은 Codex 작업의 종료 기준이 `validator PASS / 보고서 작성`이었고, blocker count 감소, terminal 처리, reclassification이 필수 조건이 아니었기 때문이다.
2. 앞으로 모든 작업은 `blocker_family -> before_count -> target_after_count -> after_count -> delta 검증` 구조의 burn-down 계약으로 닫아야 한다.
3. 즉시 구현할 것은 실제 L0/L1/L4 blocker 해결이 아니라, `task template + blocker taxonomy + burn-down ledger + delta validator + report-only progress guard` 최소 하네스다.

## Root Cause

| 반복 issue | 실제 구조적 원인 | 왜 반복됐나 |
|---|---|---|
| L0 incomplete | public newswire가 52.5482%, BW/PRN pending 존재 | L0가 닫히지 않았는데 L2/L3/L4 상태 보고를 반복 |
| failed/retryable | market/macro `FAILED_RETRYABLE`, Federal Register offset pending | retryable을 terminal status로 닫는 기준이 없음 |
| unmapped | L3 gap 4,627 중 3,999가 L1 unmapped | L3 문제가 아니라 L1 mapping burn-down 대상인데 L3/L4에서 반복 노출 |
| unsupported relation | L4 `UNSUPPORTED_RELATION_FAMILY` 18,610 | support/terminal/reclassify 없이 보고서만 반복 |
| contradiction not scanned | `CONTRADICTION_NOT_SCANNED` 11,079와 `L0_INCOMPLETE_COVERAGE` 11,079 공존 | L0 coverage가 닫히기 전 downstream blocker로 재진단 |

GPT 판단:

> Codex가 “작업을 했다”는 증거는 만들었지만, “blocker가 줄었는지”를 작업 종료 조건으로 강제하지 않았다.

## Required Harness Design

### Task Types

| task_type | 의미 | progress 인정 |
|---|---|---|
| `BURN_DOWN` | blocker count 실제 감소 | YES |
| `TERMINALIZE` | retryable/pending/unsupported를 terminal status로 닫음 | YES |
| `RECLASSIFY` | 잘못된 blocker를 올바른 family/status로 이동 | 조건부 YES |
| `HARNESS_BOOTSTRAP` | template/validator/ledger 같은 운영 장치 구현 | blocker progress로는 NO |
| `DIAGNOSTIC_ONLY` | 원인 설명, 영향 분석, 현황 정리 | NO |

### Mandatory Rule

One task = one primary `blocker_family`.

예외적으로 여러 family를 건드릴 수 있지만, 각 family별 `before_count`, `after_count`, `delta`, `terminalized_count`, `reclassified_count`가 따로 있어야 한다.

### Baseline Snapshot

작업 시작 전 반드시 아래가 고정되어야 한다.

- `task_id`
- `blocker_family`
- `layer`
- `source_artifact`
- `before_count`
- `subreason_breakdown`
- `snapshot_timestamp`
- `snapshot_command`
- `upstream_dependencies`

### Closeout 인정 조건

작업 closeout은 아래 중 하나를 반드시 포함해야 한다.

| 인정 조건 | 예시 |
|---|---|
| count 감소 | before 3,999 -> after 3,421 |
| terminalized | retryable 125건 중 40건을 terminal status로 닫음 |
| reclassified | unsupported 300건을 proto event identity로 재분류 |
| upstream blocked 명시 | L0 running 때문에 L4 blocker는 UPSTREAM_BLOCKED |

인정 불가:

- 보고서 작성
- validator PASS만 있음
- 원인 파악 완료
- 향후 작업 제안
- L0 running 중 L4 incomplete coverage 재분석

## Required Validators

| Validator | 목적 | FAIL 조건 |
|---|---|---|
| `blocker_snapshot.py` | family/layer/subreason별 count snapshot 생성 | before/after snapshot 없음 |
| `blocker_delta_validator.py` | before/after count 비교 | delta 없음인데 PASS 주장 |
| `blocker_ledger_validator.py` | burn-down ledger와 snapshot 일치 검증 | ledger 누락/불일치 |
| `report_progress_guard.py` | 보고서가 progress를 과장하는지 검사 | report-only인데 PASS 표기 |
| `blocker_taxonomy_validator.py` | 허용 family/status/transition만 사용 | 임의 status 생성 |
| `upstream_dependency_gate.py` | downstream 재진단 반복 방지 | upstream-blocked L3/L4 작업을 burn-down으로 표기 |
| `terminal_status_validator.py` | terminalized count의 status 정합성 검증 | terminal 근거 없이 count 제거 |
| `stale_baseline_validator.py` | 오래된 before_count 사용 방지 | baseline snapshot 불일치 |
| `no_trading_authority_validator.py` | hard state 보호 | trading/order/broker/paper/live/deployment 권한 생성 |

## GPT Review Rubric

GPT 리뷰의 첫 질문은 항상 이것이어야 한다.

> 이번 task의 target blocker_family는 무엇이고, before_count / after_count / delta는 얼마인가?

이 답이 없으면:

- `FAIL_REPORT_ONLY`
- 또는 `DIAGNOSTIC_ONLY`

### Verdicts

| Verdict | 조건 |
|---|---|
| `PASS_BURN_DOWN` | target blocker count가 목표만큼 감소 |
| `PASS_TERMINALIZED` | retryable/pending/unsupported가 terminal status로 정리 |
| `PASS_RECLASSIFIED` | 잘못된 family가 올바른 blocker로 이동 |
| `CONDITIONAL_PASS` | delta는 있으나 metadata 일부 부족 |
| `UPSTREAM_BLOCKED` | target이 L0/L1에 막혀 downstream 작업 금지 |
| `DIAGNOSTIC_ONLY` | 설명은 유용하지만 blocker progress 아님 |
| `FAIL_REPORT_ONLY` | 보고서/validator만 있고 count 변화 없음 |
| `FAIL_SCOPE_DRIFT` | target family 외 작업으로 퍼짐 |
| `FAIL_UNSAFE_AUTHORITY` | trading/order/broker/paper/live/deployment 침범 |

## Immediate Next Codex Task

GPT 추천:

`TASK-4171 Blocker Burn-down Harness Bootstrap`

목표:

- 실제 blocker 해결이 아님.
- 앞으로 Codex가 report-only progress를 PASS로 닫지 못하게 하는 운영 장치를 repo에 넣는 것.
- 이 task는 `HARNESS_BOOTSTRAP`으로 닫고, `blocker_progress: NO`라고 명시해야 한다.

### TASK-4171 포함 범위

| 구성요소 | 포함 |
|---|---|
| mandatory task template | YES |
| blocker taxonomy registry | YES |
| burn-down ledger | YES |
| snapshot script | YES |
| delta validator | YES |
| report progress guard | YES |
| closeout report template | YES |
| full dashboard | NO |
| 실제 L0/L1/L4 blocker 해결 | NO |
| relation taxonomy 대규모 정리 | NO |

### TASK-4171 권장 산출물

- `docs/task_templates/blocker_burndown_task_template.yaml`
- `docs/report_templates/blocker_burndown_closeout.md`
- `config/blocker_taxonomy.yaml`
- `reports/blocker_burndown/ledger.jsonl`
- `scripts/audit/blocker_snapshot.py`
- `scripts/audit/blocker_delta_validator.py`
- `scripts/audit/blocker_ledger_validator.py`
- `scripts/audit/report_progress_guard.py`
- `tests/test_blocker_burndown_harness.py`

## After Harness Bootstrap

첫 실제 burn-down target은 L3/L4가 아니라 L1이다.

추천:

`TASK-4172 L1_BLOCKED_UNMAPPED_ROWS_PRESENT Burn-down`

- before_count: 3,999
- target_after_count 예시: 3,200 이하
- completion: mapped / terminalized / reclassified count 증명
- L0 backfill이 running 중이므로 baseline cohort와 new cohort를 분리해야 한다.

## Final GPT Judgment

현재 문제는 Codex의 분석 능력 부족이 아니라 작업 종료 계약 부재다.

앞으로:

- 보고서는 progress가 아니다.
- validator PASS도 progress가 아니다.
- progress는 blocker count 감소, terminal 처리, reclassification으로만 인정한다.
