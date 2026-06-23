Task3841 Loop 8 prompt.

Harden screenshot target evidence checks.

Allowed:
- Existing screenshot QA validator only.

Required:
- Keep screenshot target manifest as NOT_AUTHORITY.
- Ensure every target route file exists.
- Ensure every target route preserves read-only and NOT_AUTHORITY boundary text.

Forbidden:
- No screenshot capture in this loop.
- No native simulator dependency.
