Task3841 Loop 4 prompt.

Implement Position Detail v1 hierarchy only.

Allowed:
- Existing `apps/ios-trader-brain/app/portfolio/position/[positionId].tsx`.
- Existing fixture fields only.
- Read-only display changes only.

Required:
- `Position Detail v1` badge.
- Keep broker truth missing/blocked visible.
- Move validation into a named `Validation Status` section.
- Rename Next Action to Review Actions.
- Move Scaffold Boundary after the review sections.

Forbidden:
- No broker truth claim.
- No broker sync handler.
- No DB/runtime/API/broker.
- No new account fields.

Validation:
- typecheck, lint, npm test, route/screen/safety validators.
