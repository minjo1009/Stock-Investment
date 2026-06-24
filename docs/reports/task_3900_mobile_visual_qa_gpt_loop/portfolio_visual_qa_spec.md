# PORTFOLIO Visual QA Revision Spec

## Scope

Mobile-first Portfolio V2 table/detail cleanup based on 390x844 screenshot QA and GPT expert-agent feedback.

## Safety

- Frontend remains read-only and fixture-backed.
- No broker truth, broker mutation, order submit, paper/live permission, or real-capital control is added.

## Required UI Changes

1. Holdings table must remain the first card and stock detail must remain the second card.
2. The table must fit 390px width without right-edge clipping:
   - name column near 148px,
   - metric columns near 104px,
   - horizontal metric scroll must take remaining width.
3. Table card should be shorter and denser so the detail card starts earlier.
4. User-facing raw state strings must be softened:
   - `UNKNOWN` -> `확인 대기` or `연결 대기`,
   - `SOURCE_NOT_ATTACHED` -> `출처 연결 대기`,
   - prominent `NOT_AUTHORITY` -> `검증 전 데이터`.
5. Detail marker must be `선택 종목`, not `Stock Detail`.
6. Current price copy must be `현재가 확인 대기 · 일간 변동 확인 대기`.
7. Chart placeholder must say values are not estimated before authority is connected.
8. `NOT_AUTHORITY` and read-only posture must remain in the lower support layer.

## Acceptance

- 390x844 screenshot shows table and the start of selected detail without visual clipping.
- First column remains understandable while horizontal metrics are browsed.
- No prominent English/internal state label dominates the product content.
