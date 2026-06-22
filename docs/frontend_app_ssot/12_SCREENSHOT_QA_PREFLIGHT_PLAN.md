# Screenshot QA Preflight Plan

## Purpose

Define the future visual QA evidence contract before product screens are implemented.

This is a preflight plan only. It does not install screenshot tooling, run captures, implement screens, or prove UI quality.

## Current Status

- Screenshot QA remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- Current frontend fixtures are scaffold-only and `NOT_AUTHORITY`.
- No product screen, Candidate Detail screen, DB connection, runtime API connection, broker connection, paper/live path, deployment readiness, or real-capital path is authorized by this document.

## Non-Authorization Rule

Screenshot QA evidence can show what is visible. It must not be treated as strategy acceptance, deployment readiness, paper readiness, live readiness, broker readiness, source truth, backend truth, broker truth, order execution permission, or real-capital permission.

## Target Surfaces

| Surface ID | Surface | Current Status | Required State Coverage |
| --- | --- | --- | --- |
| SS-001 | Home | future required | normal, stale source, blocked |
| SS-002 | Brain Overview | future required | normal, missing source, unknown |
| SS-003 | Candidate Detail | future required | decision summary, evidence, disabled action |
| SS-004 | Portfolio Overview | future required | normal, stale or missing source |
| SS-005 | Position Detail | future required | position verdict, risk, source state |
| SS-006 | Orders Overview | future required | read-only order states |
| SS-007 | Order Detail | future required | disabled approve/reject/cancel |
| SS-008 | System Overview | future required | system health, blockers |
| SS-009 | Stale Source State | required special state | stale visible above fold |
| SS-010 | Disabled Action State | required special state | disabled reason plus governance change visible |

## Device / Browser Matrix

Required baseline:

| Axis | Required Value |
| --- | --- |
| Device | iPhone 15 Pro |
| Theme | Light |
| Scale | 100% |
| Orientation | Portrait |

Future optional matrix:

| Tier | Target |
| --- | --- |
| P0 | iPhone 15 Pro, Light, Portrait |
| P1 | iPhone SE width stress, Light, Portrait |
| P1 | iPhone 15 Pro Max, Light, Portrait |
| P2 | Dark theme, only after theme support is explicitly selected |
| P2 | Android, only after iOS-first baseline is stable |

## State Matrix

| State | Required Visual Evidence |
| --- | --- |
| `fresh` | source freshness visible |
| `stale` | stale badge/warning visible |
| `missing` | missing source visible, not hidden |
| `unknown` | unknown state visible as blocker/unknown |
| `blocked` | blocker reason visible |
| `disabled_action` | disabled action plus reason and required governance change visible |
| `chart_missing` | chart unavailable state visible |
| `source_not_attached` | source-not-attached visible |
| `read_only` | no active trading action affordance |
| `safety_boundary` | `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN` visible where relevant |

## Artifact Naming Policy

Future screenshot files must use deterministic names:

```text
<surface_id>__<surface_slug>__<state>__<device>__<theme>__<orientation>__<yyyymmdd>.png
```

Example:

```text
SS-003__candidate-detail__disabled-action__iphone-15-pro__light__portrait__20260622.png
```

## Storage Locations

| Artifact Type | Path |
| --- | --- |
| Preflight plan | `docs/frontend_app_ssot/12_SCREENSHOT_QA_PREFLIGHT_PLAN.md` |
| Future screenshot outputs | `docs/reports/task_<id>_screenshot_qa_run/screenshots/` |
| Screenshot manifest | `docs/reports/task_<id>_screenshot_qa_run/screenshot_manifest.csv` |
| Vision review notes | `docs/reports/task_<id>_screenshot_qa_run/vision_review.md` |

## Future Run Manifest Fields

`screenshot_id,surface_id,surface_name,route_or_story,state,fixture_or_source_artifact,device,theme,orientation,scale,captured_at,capture_command,pass_fail,failure_reason,reviewer,notes`

## Acceptance Criteria

Future screenshot QA can pass only if:

1. Required surfaces are captured or explicitly blocked with reason.
2. Device preset matches iPhone 15 Pro / Light / 100% / Portrait.
3. Stale/missing/unknown/source-not-attached states are visible.
4. Disabled actions show `actionState = disabled`, `disabledReason`, `requiredGovernanceChange`, and current hard boundary.
5. No active BUY/SELL/EXECUTE/LIVE/PLACE ORDER affordance appears.
6. Charts do not silently use synthetic source-free fallback.
7. Every image maps to surface, state, fixture/source, device, date, and pass/fail.
8. Missing/stale remains `UNKNOWN/BLOCKER`.

## Failure Criteria

Screenshot QA must fail or block if required surfaces are unavailable without explicit blocker evidence, forbidden active trading affordances appear, source-free charts are treated as evidence, stale/missing/unknown states are hidden, or screenshots are used to imply trading/deployment readiness.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, DB/runtime connection, or product screen implementation is authorized.
