# Maestro Smoke Flow Preflight Plan

## Purpose

Define future mobile interaction evidence before installing Maestro or implementing product flows.

This document is planning/governance only. It does not install Maestro, add `.maestro` flows, modify package scripts, or prove app runtime readiness.

## Current Status

- Maestro remains `REQUIRED_POST_SCAFFOLD_HARDENING`.
- The frontend remains read-only.
- Product screens, Candidate Detail, broker mutation, paper/live promotion, deployment readiness, and real-capital permission remain forbidden.

## Non-Authorization Rule

Maestro smoke-flow evidence can prove only that a selected flow traversed UI states under a documented environment. It cannot prove source truth, backend truth, broker truth, strategy acceptance, deployment readiness, paper/live readiness, or real-capital permission.

## Future Smoke Flow Targets

| Flow ID | Flow | Required Evidence |
| --- | --- | --- |
| MF-001 | App launch shell | launch succeeds or explicit environment blocker |
| MF-002 | Bottom tab traversal | HOME/BRAIN/PORTFOLIO/ORDERS/SYSTEM traversal, no mutation |
| MF-003 | Candidate Detail route traversal | detail shell/read-only state only |
| MF-004 | Evidence/source drilldown | evidence/source state visible |
| MF-005 | Disabled order action affordance | disabled reason appears, no side effect |
| MF-006 | Blocker visibility | blocker reason visible |
| MF-007 | System health read-only route | governance/source state visible |
| MF-008 | Kill switch/control center blocked surface | blocked/governance modal only |
| MF-009 | Chart missing/source-not-attached state | chart blocker visible |
| MF-010 | Read-only safety sweep | no active BUY/SELL/EXECUTE/LIVE affordance |

## Interaction Evidence Matrix

| Interaction | Required Evidence |
| --- | --- |
| app launch | launch success or explicit blocker |
| tab tap | selected tab visible, no mutation |
| detail route open | detail shell/read-only content visible |
| evidence open | evidence/source state visible |
| disabled action tap | disabled reason appears, no side effect |
| blocker surface open | blocker reason visible |
| back navigation | safe return path |
| chart interaction, if future-selected | chart source state visible |

## Future Flow Artifact Naming Policy

```text
<flow_id>__<flow_slug>__<device>__<runtime>__<yyyymmdd>.yaml
<flow_id>__<flow_slug>__<device>__<runtime>__<yyyymmdd>__result.md
```

Example:

```text
MF-005__disabled-order-action__iphone-15-pro__maestro__20260622.yaml
MF-005__disabled-order-action__iphone-15-pro__maestro__20260622__result.md
```

## Future Run Manifest Fields

`flow_id,flow_name,route_or_story,state,fixture_or_source_artifact,device,runtime,started_at,completed_at,command,pass_fail_blocked,blocker_reason,mutation_attempted,forbidden_claim_detected,artifacts,reviewer,notes`

## Acceptance Criteria

Future Maestro smoke-flow QA can pass only if required flows are executed or blocked with reason, each artifact maps route/state/fixture/source/evidence, disabled actions stay disabled with governance reasons, stale/missing/unknown states remain visible as `UNKNOWN/BLOCKER`, and no mutation path is exercised.

## Failure Criteria

Future Maestro QA must fail if active BUY/SELL/EXECUTE/LIVE/PLACE ORDER appears, approve/reject/cancel/submit/paper promote/live promote/broker sync can mutate, disabled action lacks reason, source-free chart fallback is treated as evidence, or the flow claims trading/deployment/paper/live/real-capital readiness.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, Maestro installation, package script change, or product flow implementation is authorized.
