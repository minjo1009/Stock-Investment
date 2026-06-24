# Task3903 — UI Alignment & Scroll Fix

## Summary

Task3903 repaired the mobile tab alignment regression for HOME, PORTFOLIO, BRAIN, ORDERS, and SYSTEM.

- Shared top headers now use the same centered structure: left back affordance, centered Korean tab title, right search and menu affordances.
- HOME, PORTFOLIO, and BRAIN use the same mobile content alignment posture: `#F9FAFB` page background, stretched content, 20px horizontal content padding, and full-width cards.
- PORTFOLIO holdings now render a fixed-height table card with three visible rows, internal vertical scrolling for rows four through seven, a horizontally scrollable metrics area, and a fixed first column for asset identity.
- BRAIN and support surfaces avoid user-visible internal status strings such as `NOT_AUTHORITY`, `BLOCKED`, and `FORBIDDEN`; these remain internal governance markers only.

## Safety State

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Frontend authority: fixture-backed read-only, not source of truth
- DB/runtime/broker/API connection: not added
- Broker mutation, paper/live order, and real-capital action: not added

## Visual QA Evidence

Screenshots captured from the local mobile web preview at 390x844:

- `data/artifacts/task_3903_ui_alignment_scroll_fix/screenshots/home_390x844.png`
- `data/artifacts/task_3903_ui_alignment_scroll_fix/screenshots/portfolio_390x844.png`
- `data/artifacts/task_3903_ui_alignment_scroll_fix/screenshots/brain_390x844.png`

Observed visual results:

- HOME, PORTFOLIO, and BRAIN show the same top header structure.
- Cards are centered within the same mobile-width column and no longer appear stuck to the left edge.
- BRAIN starts with user-facing Korean issue/interpretation copy rather than a large left-aligned system title.
- PORTFOLIO shows exactly three holdings rows in the first table viewport.

## Scroll Evidence

DOM inspection of the captured PORTFOLIO preview found:

- Table body vertical viewport height: `228`
- Table body scroll height: `532`
- Metrics visible width: `206`
- Metrics scroll width: `520`
- Header metrics horizontal overflow: present
- Body metrics horizontal overflow: present

This supports the requested fixed-height card plus internal vertical and horizontal scroll behavior. The first asset-name column remains outside the metrics horizontal scroller.

## Validation

Executed from `apps/ios-trader-brain`:

- `npm run typecheck` — PASS
- `npm run validate:safety` — PASS
- `npm run validate:mobile-product-v1` — PASS
- `npm run validate:product-ia-reorder` — PASS
- `npm run validate:mobile-scan-list-v1` — PASS
- `npm run validate:frontend-governance` — PASS

Pending repository-level validation before final commit:

- `python scripts/task_registry_validate.py`
- `git diff --check`
- `git diff --cached --check` after staging

## Notes

This task did not redesign IA. It only repaired header alignment, shared margins, user-visible internal copy, and PORTFOLIO table scroll mechanics.
