# TASK-4139 Dirty Worktree / Artifact Reconciliation

## 결론

현재 dirty file은 단순 임시파일 묶음이 아니다. 최근 L0/L1 작업 산출물, 과거 삭제 표시, DVC pointer 삭제, L2/L3 코드 삭제 표시, 런타임 인접 변경이 섞여 있다. 그래서 자동 삭제나 자동 restore를 하지 않고 분류표와 P0 review queue를 만들었다.

## 요약

| 항목 | 개수 |
|---|---:|
| 전체 dirty row | 645 |
| P0 review row | 207 |
| 삭제 표시 row | 298 |
| untracked row | 269 |

## 가장 중요한 처리 원칙

| 원칙 | 의미 |
|---|---|
| 삭제 자동 확정 금지 | `D` 표시 파일은 사용자/owner 확인 전 삭제 확정하지 않는다. |
| DVC pointer 우선 확인 | `.dvc` 삭제는 데이터 복구성에 영향을 주므로 restore/retire 결정을 따로 해야 한다. |
| 최근 L0/L1 산출물 보존 | TASK-4116 이후 source acquisition 산출물은 registry/manifest와 맞춰 보존한다. |
| 런타임 인접 변경 주의 | `src/app`, `src/integration`, `src/strategy`, `src/risk` 변경은 별도 owner review 전 커밋/삭제하지 않는다. |

## 다음 액션

1. `dirty_worktree_p0_review_queue.csv`부터 owner 판단을 받는다.
2. DVC pointer 삭제는 restore할지, 명시적으로 retire할지 결정한다.
3. 최근 TASK-4116~TASK-4140 산출물은 manifest/doc registry 기준으로 묶어 보존한다.
4. 삭제 확정은 별도 cleanup task에서만 진행한다.
