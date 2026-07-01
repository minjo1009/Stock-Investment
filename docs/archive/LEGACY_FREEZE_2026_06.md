# Legacy Freeze 2026-06

This file freezes legacy project-management and historical report material as preserved evidence outside the default Codex read path.

## Decision

Legacy materials are not deleted by A001. They remain available for audit, provenance, and backtest reproducibility.

## Default Read Behavior

Codex should start from `docs/active/` and expand to historical files only when a task needs them.

## Frozen Material Types

- older task reports under `docs/reports/`
- stale Graphify outputs generated on 2026-04-25
- Obsidian navigation files
- duplicate or broad navigation docs
- historical frontend/PWA evidence
- old GPT loop dumps or prompt/response snapshots

## Status Boundary

The freeze does not change these standing statuses:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Next Step

A002 may move approved archive candidates into an agreed archive structure. A003 may delete approved `DELETE_SAFE` candidates. Neither step should run without user approval.

