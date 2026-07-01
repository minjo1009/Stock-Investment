# Workstream Surface Inventory

## Purpose

This document is the human-readable summary of Task745.

It answers:

```text
What surfaces exist?
Which workstream owns them?
What needs owner review before the project can keep expanding?
```

The full machine-readable table is:

`docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv`

## Inventory Scope

Task745 scans:

- tracked Git files
- modified/deleted Git files
- untracked Git files

Ignored local-only folders such as raw data, large artifact stores, caches, and `참고 Context/` are excluded from the formal project surface.

## Current Counts

| Class | Count | Meaning |
| --- | ---: | --- |
| summary_commit_candidate | 1,493 | Mostly report markdown, decision CSV, pass/fail CSV, and manifests. |
| needs_owner_review | 1,066 | Code/tests/scripts/docs that need canonical/experiment/archive classification. |
| canonical_candidate | 135 | Likely operating docs, architecture docs, contracts, package code/tests, and skills. |
| local_only | 13 | Should stay local or manifest-only. |

## Top-Level Surface

| Top Level | Count | Current Interpretation |
| --- | ---: | --- |
| docs | 1,600 | Mostly task reports and operating documents. Needs summary-vs-large artifact discipline. |
| src | 558 | Main risk area for 2/5 cleanup. Task-scoped code and package code are mixed. |
| tests | 378 | Main risk area for 3/5 cleanup. Task-scoped tests and canonical tests are mixed. |
| tasks | 58 | Registry and historical task notes. |
| scripts | 36 | Governance, data, orchestration, and utility scripts. |
| frontend | 16 | Small Git-visible surface; large frontend dependencies are ignored. |
| skills | 8 | Project skills and subagent workflows. |

## Workstream Surface

| Workstream | Count | Issue |
| --- | ---: | --- |
| general | 797 | Mixed files need owner routing. |
| backtest_replay | 645 | Many task-scoped code/test files need canonical selection. |
| brain | 287 | Task727-742 brain surface needs active path and supersession notes. |
| regime_intraday | 284 | Intraday/regime task files need package boundary decisions. |
| governance | 265 | Mostly docs/scripts/contracts; should become first stable base. |
| paper_execution | 202 | Execution/risk code and tests need broker-truth ownership review. |
| microstructure_data | 188 | Data/microstructure code needs raw-source readiness classification. |
| frontend_reporting | 39 | Frontend/reporting surface is smaller after fixing short-token workstream matching. |

## Biggest Owner-Review Buckets

| Bucket | Count | Next Owner |
| --- | ---: | --- |
| backtest_replay / task_scoped_code | 287 | Backtest & Simulation Infra |
| general / task_scoped_test | 96 | Research Governance first |
| backtest_replay / package_code | 75 | Backtest & Simulation Infra |
| general / other | 66 | Research Governance first |
| regime_intraday / task_scoped_test | 60 | Regime + Intraday Research |
| brain / task_scoped_code | 40 | Research Governance + Regime Research |
| brain / task_scoped_test | 39 | Research Governance + Backtest Infra |
| general / package_test | 36 | Research Governance first |
| backtest_replay / task_scoped_test | 34 | Backtest & Simulation Infra |
| general / package_code | 28 | Research Governance first |

## Five-Pass Cleanup Loop

### 1/5. Surface Inventory

Status: current pass.

Goal:

- create project-wide inventory
- separate formal surface from ignored local material
- identify owner-review buckets

### 2/5. Source Code Canonicalization

Goal:

- classify `src/` into canonical package code, task-scoped research, experiment, archive candidate, and local-only.
- identify which code path each workstream should use next.

### 3/5. Test And Validation Canonicalization

Goal:

- classify `tests/` into canonical validation suites, task-scoped tests, slow integration tests, and archive candidates.
- define minimum validation commands per workstream.

### 4/5. Skills, MD, And Subagent Canonicalization

Goal:

- repair or retire stale skills and markdown.
- ensure subagent routing is precise.
- ensure GPT/Chrome review packets are bounded and source-safe.

### 5/5. Operating Runbook And Registry Closeout

Goal:

- update registry/current operating model/index.
- write final runbook for how Codex should continue the project.
- lock next development path after cleanup.

## Non-Destructive Rule

During the five-pass cleanup:

- do not delete files
- do not move artifacts
- do not change strategy acceptance
- do not change deployment readiness
- do not promote a task to canonical without owner/reviewer validation

Classification first. Movement later.
