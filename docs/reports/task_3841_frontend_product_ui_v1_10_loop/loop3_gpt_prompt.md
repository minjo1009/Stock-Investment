Task3841 Loop 3 prompt.

Implement Chain Detail v1 hierarchy only.

Allowed:
- Existing `apps/ios-trader-brain/app/brain/chain/[chainId].tsx`.
- Existing fixture fields only.
- Read-only display changes only.

Required:
- `Chain Detail v1` badge.
- Put summary and layer validation before scaffold boundary.
- Keep missing/stale/blocked/unknown layer states visible.
- Keep disabled actions disabled.
- Keep scaffold boundary visible.

Forbidden:
- No DB/runtime/API/broker.
- No new confidence/rank/score fields.
- No trading action handler.
- No product readiness claim.

Validation:
- typecheck, lint, npm test, route/screen/safety validators.
