# Task746 Source Code Canonicalization

## Decision Summary

- Verdict: `PRIMARY_PASS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Scope: `src/` classification only
- Key metric: 558 `src` rows classified
- What changed: Added a reproducible `src` canonicalization inventory and a human-readable architecture map.
- Next action: Task747 must classify `tests/` against the Task746 buckets.

Task746 does not delete, move, promote, or change trading logic.

## Quant Expert Report

### Data Source And Source Readiness

Input:

- `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv`
- `tasks/task_registry.csv`

Task746 uses repository metadata only. It does not use market data, PnL, labels, broker fills, or source-event contents.

### Exact Join Keys

- Source rows are filtered with `top_level == src`.
- Task registry lookup uses extracted `Task###` identifiers when a task number is present in a path.
- There is no lifecycle, trade, symbol, price, or timestamp join.

### Leakage Audit

No outcome fields are used.

Forbidden inputs not used:

- realized PnL
- return labels
- accepted trade labels
- broker truth rows
- source interpretation scores
- strategy results

### Classification Results

| Bucket | Count | Meaning |
| --- | ---: | --- |
| historical_task_code_review | 346 | Historical task research code. Preserve for traceability. |
| owner_review_package_candidate | 119 | Package-looking code that still needs owner review. |
| supporting_task_code_review | 44 | Supporting task code for current content, microstructure, paper execution, or acceptance lanes. |
| canonical_package_candidate | 33 | Smallest stable package candidate set. |
| active_task_code_review | 16 | Current brain Task727-742 builder files. |

### Main Finding

The project has a small likely-package core and a very large task-code surface.

`src/backtest/` contains 444 of 558 `src` rows. It currently carries:

- reusable backtest engine files
- historical structural breakout research
- continuation/microstructure research
- content-signal backtests
- current brain-layer builders

This is the main source-code management risk.

### Current Brain Layer Finding

Task727-742 brain builder files are classified as `active_task_code_review`.

They are not canonical package modules yet. They require supersession notes and output-contract validation before future code imports them as stable brain components.

### GPT/Chrome Review

GPT/Chrome review was attempted.

- existing ChatGPT tab found: yes
- existing tab used: no, claim failed
- fresh tab attempted: yes
- fresh tab response captured: no
- status: `ATTEMPTED_BUT_CHROME_CONTROL_FAILED`

The review packet was generated at:

- `docs/reports/task_746/gpt_chrome_review_packet.md`

No GPT finding is used as source-of-truth for Task746.

### Remaining Blockers

- No files have been promoted to canonical runtime status.
- Test coverage is not yet mapped to the 33 package candidates.
- Historical task code still needs owner-level supersession decisions before any movement or archival plan.

## No-Background Decision-Maker Report

### What Happened

We cleaned up the map of `src/`.

The codebase has 558 visible source files. Only 33 look like the first stable package core. Most of the rest are task research files.

### Why It Matters

Until this is clear, new work keeps getting built on top of old experiments.

This task does not fix strategy quality directly. It prevents the project from mixing old experiments, current brain code, and real runtime code.

### Whether This Changes Capital Or Deployment Readiness

No.

Strategy remains `NOT_ACCEPTED`.

Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

### Plain-Language Next Step

Next, classify the tests.

We need to know which tests protect the 33 stable candidates and which tests only preserve old task behavior.

## Artifact Manifest

### Inputs

| Artifact | Purpose |
| --- | --- |
| `docs/reports/task_745_project_surface_inventory/task745_project_surface_inventory.csv` | Project surface inventory |
| `tasks/task_registry.csv` | Task status and canonical-state lookup |

### Outputs

| Artifact | Rows | Purpose |
| --- | ---: | --- |
| `docs/reports/task_746_src_canonicalization/task746_src_canonicalization_inventory.csv` | 558 | File-level `src` classification |
| `docs/reports/task_746_src_canonicalization/task746_src_canonicalization_summary.md` | n/a | Summary counts |
| `docs/architecture/src_canonicalization_map.md` | n/a | Human-readable architecture map |
| `scripts/src_canonicalization_inventory.py` | n/a | Reproducible classifier |
| `docs/reports/task_746/gpt_chrome_review_packet.md` | n/a | GPT review packet |

### Validation Commands

```powershell
python scripts/src_canonicalization_inventory.py
python -m py_compile scripts/src_canonicalization_inventory.py
python scripts/task_artifact_manifest.py --task-dir docs/reports/task_746_src_canonicalization
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```
