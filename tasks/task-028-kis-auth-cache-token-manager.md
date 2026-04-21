# Task 028 - KIS Auth Cache / Token Manager

## Goal
- Remove per-run token issuance bottleneck.
- Separate auth lifecycle from trade execution path.

## Scope
- Added `src/integration/kis_auth_manager.py`.
- Updated `src/integration/kis_client.py` to consume auth manager only.
- Added tests for cache reuse / reissue / non-leakage.
- Added docs and ignore entries:
- `.kis_token_cache.json` in `.gitignore`
- README section for token cache policy.

## Token Policy
- Default: reuse cached token.
- Reissue only when missing or near-expiry.
- If issue request is rate-limited and cached token is still valid, keep using cached token.
- No infinite retry loop.

## Validation
- `python -m unittest tests.unit.test_structure -v` passes with token-manager tests.

## Notes
- This is foundation-level cache management; multi-process lock/rotation is deferred.
