# Loop 2 GPT Response Summary

GPT recommended implementing `HOME v0` now as scaffold-only fixture-backed assembly.

Key recommendations:

- use a typed TypeScript fixture wrapper, not direct JSON import and not package/tsconfig changes
- edit only `apps/ios-trader-brain/app/(tabs)/index.tsx`
- create `apps/ios-trader-brain/src/read-models/homeFixture.ts`
- preserve `home.json`
- show scaffold-only, read-only, and `NOT_AUTHORITY` boundaries
- show `UNKNOWN`, `STALE`, freshness, blocker, and disabled action states
- do not add navigation handlers, DB/runtime/broker imports, package changes, validator changes, or product readiness claims

GPT is review/planning support only and is not source of truth.
