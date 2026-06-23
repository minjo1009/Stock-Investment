Task3841 Loop 5 prompt.

Implement Order Detail v1 hierarchy only.

Allowed:
- Existing `apps/ios-trader-brain/app/orders/[orderId].tsx`.
- Existing fixture fields only.
- Read-only display changes only.

Required:
- `Order Detail v1` badge.
- Keep local order and broker truth blocked.
- Move validation into a named `Validation Status` section.
- Rename Next Action to Review Actions.
- Move Scaffold Boundary after disabled/review sections.

Forbidden:
- No approve/reject/cancel/submit handler.
- No broker mutation.
- No paper/live permission.
- No order acceptance claim.

Validation:
- typecheck, lint, npm test, route/screen/safety validators.
