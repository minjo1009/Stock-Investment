# TASK-4117 L0 Source Acquisition Project Management Integration

## Goal

Integrate the TASK-4116 recovered L0/L1 source acquisition assets into the
active project-management system so source code, scheduler posture, roadmap
docs, task records, status reporting, and validators stay aligned.

## Results

- Added the canonical six-stage L0/L1 source acquisition roadmap at
  `docs/architecture/l0_source_acquisition_project_management_plan.md`.
- Embedded the same stage plan and source implementation modes into
  `configs/db_source_acquisition_scheduler.json`.
- Updated active docs so L0/L1 source acquisition now points to TASK-4116
  recovery evidence and TASK-4117 project-management integration evidence.
- Updated existing L0 policies for operator override staging, news/newswire
  mapping boundaries, and microstructure backfill/coverage gates.
- Updated L0 collection status reporting to expose the scheduler management
  plan and current next stage.
- Added `scripts/validate_l0_source_acquisition_project_management.py` so config,
  roadmap, active docs, policy references, closed permissions, and conflict-copy
  cleanup are checked together.
- Removed restored OneDrive conflict-copy files with `-DESKTOP-2R00TB4` suffix
  from active L0 paths.

## Six-Stage Direction

| Stage | Direction | Current TASK-4117 status |
|---:|---|---|
| 1 | Official/core API smoke stabilization | Next |
| 2 | Real-time source budget optimization | Blocked until Stage 1 validates |
| 3 | Real-time scheduler setup and execution | Blocked until Stage 2 validates |
| 4 | Historical backfill optimization | Blocked until Stage 3 validates |
| 5 | Background historical backfill from 2016 | Blocked until Stage 4 validates |
| 6 | L1 quality/coverage audit and L2 handoff | Blocked until Stage 5 validates |

## Runtime Boundary

The collectors are code-based Python HTTP/RSS/API/page collectors except for
`public_headline_browser_watch`, which is Chrome/Node smoke only. Codex/GPT is
limited to planning, recovery, review, and documentation; it is not a runtime
collection engine or source of truth.

## Mapping Boundary

Ticker/entity/news mapping exists as an initial L0/L1 gate in
`tools/db/news_l0_l1.py`. It is not yet final L2-ready disambiguation. Stage 6
must audit publication time, raw reference, entity ambiguity, ticker collisions,
macro-context bypasses, and coverage before L2 handoff.

## Safety

The committed scheduler baseline remains disabled by default with
`allow_network=false`. No scheduler recurrence, network collection, DB mutation,
replay, broker mutation, paper promotion, live order, or real-capital permission
was enabled by this task.

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
