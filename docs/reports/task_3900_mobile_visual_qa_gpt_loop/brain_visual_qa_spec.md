# BRAIN Visual QA Revision Spec

## Scope

Mobile-first Brain V5 cleanup based on 390x844 screenshot QA and GPT expert-agent feedback.

## Safety

- Brain UI is interpretation support only.
- It must not imply strategy acceptance, candidate promotion, live/paper trading permission, broker mutation, or real-capital authorization.

## Required UI Changes

1. Fix right-edge clipping in the issue card, news cards, badges, and interpretation boxes.
2. Header keeps title and recent update; only one search affordance remains in the first viewport.
3. Today issue card must show theme, one-line interpretation, state badge, and conviction gauge without clipping.
4. News card hierarchy must be:
   - title,
   - source/time,
   - summary,
   - `브레인 해석` label,
   - interpretation body,
   - `원문 보기`.
5. Relation copy must use `→` and remain readable in two lines.
6. Candidate card wording must avoid lifecycle-promotion language:
   - use `검토 유지`, `검토 필요`, `주의`,
   - avoid `승격 가능`.
7. Risk summary must stay soft and explanatory.
8. Support/governance state must remain below the product content.
9. Candidate detail should use `검토 유지` instead of `승격 예정 아님`.
10. Evidence detail should use `텍스트 복사 준비 중`, not `텍스트 복사 disabled`.

## Acceptance

- 390x844 screenshot has no right-edge text clipping.
- First viewport emphasizes issue and news interpretation, not governance state.
- Lv2/Lv3 copy is Korean user-facing copy and not internal execution wording.
