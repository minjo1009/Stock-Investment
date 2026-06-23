# Task3839 Loop 5 Bottom Tab Typography Decision

## Decision Summary

Loop 5 defers bottom tab typography changes.

The issue remains a P2 candidate because current evidence comes from the Task3836 contact sheet, not a focused original-PNG tab-label review.

## Verdict

`DEFERRED`.

## Future Patch Trigger

A future patch may modify only `apps/ios-trader-brain/app/(tabs)/_layout.tsx` if per-screen original PNG review confirms:

- tab labels are hard to read
- tab labels are truncated
- tab labels are crowded
- tab labels are materially too small

## Forbidden Changes

- No tab rename.
- No route rename.
- No IA change.
- No icon change.
- No dependency change.
- No custom tab bar.
- No navigation rewrite.

## Safety Boundary

No broker, DB, runtime, paper/live, deployment, or real-capital permission changed.
