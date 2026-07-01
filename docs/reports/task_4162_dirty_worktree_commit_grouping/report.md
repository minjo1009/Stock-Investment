# TASK-4162 Dirty Worktree Commit Grouping

## 결론

Dirty worktree 정리는 두 갈래로 나눴습니다.

1. 최근 active 산출물은 stage/commit 가능한 후보로 묶는다.
2. 삭제 표시 파일은 자동 처리하지 않고 review matrix로 분리한다.

이번 작업은 삭제/복구를 수행하지 않습니다. `D` 상태 파일은 모두 stage 후보에서 제외했습니다.

## Stage 후보

| 구분 | 개수 |
|---|---:|
| 전체 stage 후보 | 288 |
| 최근 task script | 97 |
| 최근 task report | 61 |
| active doc | 46 |
| L0 script | 23 |
| L0/L1 source code | 19 |
| current task src | 12 |
| current task config | 10 |
| current task test | 7 |
| L0 source config | 6 |
| frontend/catalog | 3 |
| root governance or ignore rule | 2 |
| task/governance output | 2 |

## 삭제 Review 대상

| 구분 | 개수 | 처리 |
|---|---:|---|
| deleted L2/L3 code/test | 135 | owner review 후 복구/삭제 확정 |
| deleted historical report | 92 | doc registry/archive 기준 판단 |
| deleted DVC pointer | 39 | DVC/artifact retention 기준 판단 |
| deleted other | 31 | owner review |
| local archive file | 1 | ignore/register/delete 판단 |

## 안전 기준

| 기준 | 적용 |
|---|---|
| `git add .` 사용 금지 | 적용 |
| `D` 파일 stage 금지 | 적용 |
| paper/KIS/broker 인접 파일 stage 제외 | 적용 |
| broker/live/order 관련 변경 금지 | 적용 |
| deletion/restore 자동 수행 금지 | 적용 |
| stage 전 후보 목록 생성 | 적용 |

## Stage 결과

| 항목 | 결과 |
|---|---:|
| staged name-status rows | 605 |
| staged deleted rows | 0 |
| staged paper/KIS/broker adjacent rows | 0 |

커밋은 실행하지 않았습니다. 이유는 `git diff --cached --check`가 기존 생성 문서/응답 파일의 trailing whitespace 및 extra blank line 문제로 실패했기 때문입니다. 검증 실패 상태에서 커밋하지 않는 것이 맞습니다.

## 산출물

- `stage_candidate_matrix.csv`
- `stage_candidate_paths.txt`
- `deletion_review_matrix.csv`
- `staged_scope_summary.json`
- `report.md`
- `artifact_manifest.csv`
- `validation_results.md`
