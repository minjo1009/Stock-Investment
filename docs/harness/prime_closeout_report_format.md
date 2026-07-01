# Prime Closeout Report Format

## 1. Verdict

- Closeout verdict:
- Progress class:
- Actual underlying progress claimed: YES / NO

## 2. What Changed

- Change scope:
- Files or artifacts changed:
- Non-goals:

## 3. Measured Outcome

| outcome_unit | baseline | after | delta | measurement_method |
|---|---:|---:|---:|---|
|  |  |  |  |  |

For diagnostic, design, review, and harness-bootstrap work, write `N/A` for
underlying problem progress and state what evidence was produced instead.

## 4. Evidence

| evidence | path or command | result | supports |
|---|---|---|---|
|  |  |  |  |

## 5. What Did Not Change

- Remaining blockers or gaps:
- Work explicitly outside this task:
- Claims that are still forbidden:

## 6. Claim Boundary

- Actual underlying progress: YES / NO
- Reason:
- Allowed claims:
- Forbidden claims:

## 7. Validation

| validator | result | note |
|---|---|---|
| prime_task_contract_validator | PASS/FAIL |  |
| outcome_contract_validator | PASS/FAIL |  |
| evidence_delta_validator | PASS/FAIL/N/A |  |
| safety_authority_guard | PASS/FAIL |  |
| report_progress_guard | PASS/FAIL |  |

## 8. Next Concrete Target

- next_task_id:
- next_task_type:
- next outcome_unit:
- required baseline:
- required validator:
