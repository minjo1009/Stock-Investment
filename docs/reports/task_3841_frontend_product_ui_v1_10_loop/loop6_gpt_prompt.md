Task3841 Loop 6 prompt.

Add a detail v1 route validator.

Allowed:
- `apps/ios-trader-brain/src/qa/*`
- `apps/ios-trader-brain/package.json`

Required:
- Ensure Candidate, Chain, Position, and Order detail routes preserve v1 labels and read-only/NOT_AUTHORITY boundaries.
- Ban score/rank/confidence/order submit terms.
- Add the validator to `npm test`.

Forbidden:
- No UI business logic.
- No DB/runtime/broker.
- No product readiness claim.
