# TASK-4160 L0-L4 Structure Cleanup GPT Review

## 결론

GPT Pro 검수 결과는 조건부 통과입니다.

이번 구조 정리는 코드 이동, 삭제, rename, 대규모 refactor가 아니라 L0-L4의 active 기준을 명확히 고정하는 작업으로 진행했습니다. 이유는 현재 백필과 레이어 개발 산출물이 아직 진행 중이고, 기존 dirty file이 많아 파일을 물리적으로 정리하면 오히려 추적성과 런타임 안정성을 해칠 수 있기 때문입니다.

## GPT Pro 검수 요지

| 항목 | GPT 판단 | 적용 |
|---|---|---|
| 기존 코드 이동/삭제 | 금지 | 적용하지 않음 |
| active 기준 문서화 | 필요 | `active_layer_handoff.md` 작성 |
| machine-readable manifest | 필요 | `active_layer_manifest.json` 작성 |
| 레이어별 역할 경계 | 필요 | L0-L4 ownership matrix로 고정 |
| entrypoint/validator 명시 | 필요 | layer별 active script/validator를 manifest에 명시 |
| 런타임 가속/스케줄러 변경 | 이번 범위 아님 | 변경하지 않음 |
| PRNewswire split/BW daily default | 이번 범위 아님 | 변경하지 않음 |

## 이번에 정리한 것

| 구분 | 내용 |
|---|---|
| 읽기 순서 | AGENTS, task registry, doc registry, active handoff, active manifest 순서로 고정 |
| L0 역할 | raw 수집, 백필, scheduler proof, raw integrity, runtime status |
| L1 역할 | source packet, raw lineage, ticker/entity mapping, blocker status |
| L2 역할 | event primitive, diagnostic feature candidate, dedup/stale/effect-window, L3 handoff |
| L3 역할 | relation graph, event cluster, relation quality, coverage gap |
| L4 역할 | diagnostic thesis bundle, evidence linkage, contradiction/blocker visibility |
| 금지 경계 | signal, order, sizing, broker mutation, live order, paper promotion은 계속 금지 |

## 의도적으로 하지 않은 것

| 하지 않은 일 | 이유 |
|---|---|
| 오래된 파일 삭제 | dirty worktree와 진행 중 백필 때문에 감사 trail 훼손 위험 |
| 코드 rename/refactor | 구조 정리 목적에 비해 리스크가 큼 |
| L0 runtime 재시작 | 수집 중인 백그라운드 작업을 건드리지 않는 것이 안전 |
| BW4 적용 | TASK-4159 controller 결정에 맡김 |
| PRNewswire offset/range split | GPT Pro와 기존 판단 모두 아직 금지 |
| L2/L3/L4 최종 품질 통과 선언 | L0 백필이 아직 진행 중이라 진단/구조 기준만 고정 |

## 산출물

| 산출물 | 역할 |
|---|---|
| `gpt_prompt.md` | GPT Pro에 전달한 검수 프롬프트 |
| `gpt_response.md` | GPT Pro 원문 응답 |
| `active_layer_handoff.md` | 사람이 먼저 읽는 L0-L4 active handoff |
| `active_layer_manifest.json` | 자동 검증/후속 작업용 active layer manifest |
| `artifact_manifest.csv` | TASK-4160 산출물 목록 |
| `validation_results.md` | 검증 결과 |

## 현재 판단

L0-L4 구조 정리는 "물리적 청소"가 아니라 "작업자가 헷갈리지 않도록 active 기준을 박는 정리"로 완료했습니다. 다음 작업부터는 새로 만든 handoff/manifest를 먼저 읽으면 기존 L1/L2/L3/L4 파일 중 무엇을 active로 봐야 하는지 더 명확해집니다.
