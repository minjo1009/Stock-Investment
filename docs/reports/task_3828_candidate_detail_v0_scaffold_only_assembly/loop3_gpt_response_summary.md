# Loop 3 GPT Response Summary

GPT recommended implementing `Candidate Detail v0` now as scaffold-only fixture-backed assembly.

Key recommendations:

- route path: `apps/ios-trader-brain/app/brain/candidate/[candidateId].tsx`
- no new top-level tab
- use a typed TypeScript fixture wrapper, not direct JSON import and not package/tsconfig changes
- create `apps/ios-trader-brain/src/read-models/candidateDetailFixture.ts`
- preserve `candidate-detail.json`
- use existing domain components: `DecisionHeader`, `EvidenceList`, `ValidationReadinessPanel`, `RiskGate`, and `DisabledActionBar`
- show the six-section detail frame and visible `NOT_AUTHORITY`/read-only boundaries
- keep route params display-only; do not use them to query data

GPT is review/planning support only and is not source of truth.
