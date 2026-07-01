# TASK-4169 GPT Response

## 한줄 결론

지금은 `L0 미완료/실패 복구 -> L1 unmapped 회수 -> feature/검토 대기 정리 -> L3/L4 의미론 확장` 순서가 맞고, L4 thesis, 신호, 랭킹, 배포는 아직 건드리면 안 된다.

## 문제별 해결 방향

| 문제 | 현재 의미 | 해결 방향 | 우선순위 | 지금 하면 안 되는 것 | 검증 방법 |
|---|---|---|---|---|---|
| 3,999 L1 blocked unmapped rows | L0/L1/L2 trace는 연결됐지만 L1 issuer/entity 매핑이 막힘 | unmapped review pack, source/title/entity 후보 빈도표, deterministic alias/ticker/issuer/headline parser 최소 확장 | P0 | LLM 자동 추론, vector DB, 전체 매핑 rewrite, 애매한 keyword 강제 매핑 | subreason 감소, 신규 mapped row lineage, L0-L2/L3 validator PASS |
| 447 recall/entity review pending | 회수 후보지만 entity 판단이 끝나지 않은 검토 대기 | `ACCEPT_MAPPED`, `NEEDS_ALIAS`, `AMBIGUOUS_BLOCKER`, `NON_ISSUER`, `INSUFFICIENT_CONTEXT` 상태로 종료 | P1 | pending drop, 임의 매핑, 과한 수동 리뷰 시스템 | 447건이 명시 상태로 전환, ambiguous는 blocker 유지 |
| 181 mapped but no article/entity feature | 매핑은 됐지만 L2/L3 feature가 없음 | feature builder/backfill 보강, article body 없으면 `ARTICLE_UNAVAILABLE` blocker | P1 | entity 재매핑부터 다시 하기, headline만으로 feature 꾸미기 | 181건 감소, feature 또는 명시 blocker 존재 |
| 18,610 unsupported relation family | L3 relation을 L4 taxonomy가 아직 해석하지 못함 | relation family frequency matrix 후 상위 family부터 diagnostic taxonomy 추가 | P1 | catch-all 통과, graph DB, 의미 왜곡 coercion | unsupported 감소, family schema/validator PASS |
| 11,079 contradiction not scanned | 아직 contradiction scan coverage가 없음 | supported family부터 deterministic contradiction scanner 추가. L0 incomplete는 clean으로 바꾸지 않음 | P1, L0 이후 | not scanned를 no contradiction으로 해석, LLM contradiction 판정 | scan coverage, blocker 감소, L0 incomplete 유지 |
| 11,079 L0 incomplete coverage | L4에 필요한 원천 데이터가 부족 | BW/PRN/context/market macro terminal status 정리 | P0 | incomplete를 negative evidence로 사용, L4 thesis로 우회 | L0 incomplete 감소, source inventory 원인 명시 |
| 6,913 proto event identity | event identity가 canonical하지 않음 | deterministic event identity v1: source + article_id + date + entity_id + event_type + normalized_title_hash | P2 | ML/LLM clustering, 기존 ID 대량 변경 | ID stability test, duplicate sample QA |
| BW/PRN backfill incomplete | public newswire 52.5482%, BW/PRN 미완료가 L0 incomplete 핵심 원인 | 기존 runner 유지, source-specific resume/retry/partial tracking 강화 | P0 | worker 전면 rewrite, 무리한 concurrency, partial/stale guard 제거 | completed/pending/partial 추세, failed=0 유지 |
| public market/macro FAILED_RETRYABLE | 재시도 가능한 실패 상태 | 실패 unit/source 분리, bounded retry, 반복 실패는 terminal blocker | P0 | complete 처리, 임의 데이터 대체, macro source 무시 | `COMPLETED` 또는 명시 terminal blocker 전환 |
| Federal Register 2020-10 pending offset | 2020-10 offset 32가 empty response로 막힌 단일 pending unit | offset 32 재요청, raw response/pagination proof 저장. 증거 있으면 `EMPTY_PAGE_CONFIRMED` | P0-fast | empty 1회로 complete, hardcode skip | pending 해소, pagination proof 존재 |

## 실행 순서

### P0

1. L0 incomplete/failed recovery
   - BusinessWire pending 1,821 계속 회수
   - PRNewswire pending 125 / partial 11 stall 원인 분리
   - public market/macro `FAILED_RETRYABLE` 재시도 또는 terminal blocker화
   - Federal Register 2020-10 offset 32 evidence 기반 종료
2. L1 blocked unmapped 3,999 회수
   - source/title/entity 후보 빈도표
   - deterministic alias/parser 최소 확장
   - affected rows만 rerun

### P1

1. 447 recall/entity review pending을 명시 decision state로 종료
2. 181 mapped-but-no-feature row에 feature builder/backfill 적용
3. L4 relation family frequency matrix 생성 후 상위 family부터 diagnostic-only 지원
4. 지원된 family에 대해서만 contradiction scanner coverage 추가

### P2

1. proto event identity 6,913 안정화
2. deterministic v1로 좁게 시작
3. LLM/cluster 기반 병합 금지

## Overengineering Cut

- GitHub 확인 금지: 로컬 상태가 더 최신
- L0-L4 전면 rewrite 금지
- vector DB / graph DB 금지
- LLM entity extraction / LLM thesis generation 금지
- trading signal / ranking / sizing / order logic 금지
- paper/live promotion 금지
- missing data를 negative evidence로 사용 금지
- unsupported relation family catch-all 통과 금지
- empty response를 evidence 없이 complete 처리 금지
- 무리한 BusinessWire/PRNewswire concurrency 확대 금지

## Recommended Next Tasks

### TASK-4170 L0 Source Recovery and Terminal Status Cleanup

Scope:
- BusinessWire pending 상태 점검
- PRNewswire pending/partial stall 원인 분리
- public market/macro `FAILED_RETRYABLE` bounded retry
- Federal Register 2020-10 offset 32 재요청 및 pagination proof 저장
- terminal status는 `COMPLETED`, `EMPTY_PAGE_CONFIRMED`, `RETRY_EXHAUSTED_BLOCKER`, `SOURCE_UNAVAILABLE_BLOCKER` 중 하나만 사용
- L1/L2/L3/L4 로직 변경 금지

### TASK-4171 L1 Newswire Recall Mapping and Feature Gap Repair

Scope:
- 3,999 L1 blocked unmapped triage pack
- source/title/entity 후보 빈도표
- deterministic alias/ticker/issuer/headline parser 최소 확장
- 447 recall/entity pending decision state 전환
- 181 mapped-but-no-feature feature backfill
- affected rows만 rerun

### TASK-4172 L4 Diagnostic Blocker Taxonomy and Scanner Coverage V1

Scope:
- unsupported relation family 18,610 frequency matrix
- 상위 relation family만 diagnostic taxonomy에 최소 지원
- supported family에 대해서만 contradiction scanner 추가
- proto event identity v1은 deterministic key 기반으로 제한
- L4 thesis generation, investment conclusion, ranking, sizing 금지
