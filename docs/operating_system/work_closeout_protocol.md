# Work Closeout Protocol

Last updated: 2026-06-03

## Purpose

Every meaningful task must close the operating loop. Code, reports, screenshots, Slack delivery, or paper-trading output are not complete until the repository's operating documents still point to the current truth.

This protocol prevents the project from drifting into chat-only decisions, stale markdown, stale Graphify context, or unmanaged task reports.

## When This Applies

Use this protocol whenever work changes any of these:

- strategy acceptance
- paper readiness
- deployment readiness
- named owner or reviewer
- active or canonical task state
- blocker status
- artifact location
- validation command
- source readiness
- frontend or Slack evidence surface

For tiny code-only fixes that do not change project state, explicitly mark operating updates as not applicable in the final report or final response.

## Mandatory Closeout Checks

| Check | Required Action |
|---|---|
| Current state | Update `docs/ownership/current_operating_model.md` when readiness, lead, gate, or top blocker changes. |
| Readiness registry | Update `docs/ownership/readiness_registry.yaml` when any acceptance status, blocker, owner, artifact, validation command, or next gate changes. |
| Registry | Update `tasks/task_registry.csv` when active/canonical status, acceptance, readiness, report path, decision path, artifact path, or validation command changes. |
| Report | Add or update the task report under `docs/reports/<task_id>/` unless the work is explicitly non-reportable. |
| Manifest | Add or update `artifact_manifest.csv` for generated task artifacts. |
| Owner | Ensure every blocker has a named lead, canonical team, reviewer or reviewer team, next gate, and validation command. |
| Graphify | Do not use Graphify for current state unless regenerated after the relevant task family. |
| Validation | Run the closeout validation commands or record why they could not run. |

## Required Final Response Shape

Every non-trivial work final response must include:

- what changed
- current readiness status if relevant
- files or artifacts updated
- validation commands and results
- remaining blocker and owner
- whether operating updates were completed or not applicable

User-facing final responses must stay plain and quick to read:

- conclusion first
- short Korean sentences
- key numbers before explanation
- `done / failed / next` separated clearly when useful
- no long institutional wording in chat unless explicitly requested
- detailed expert wording belongs in repo reports, not the chat closeout

## Minimum Validation

Run these before claiming closeout:

```powershell
python scripts/task_registry_validate.py
python scripts/codeowners_coverage_validate.py
python validate_readiness_registry.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```

Add task-specific tests from the task report.

## Failure Conditions

Do not claim work is complete if any of these remain true:

- the current operating model points to an older board while a newer board changed readiness
- the readiness registry is missing a blocker owner, artifact, validation command, or next gate
- a blocker exists without owner, artifact path, next gate, or validation command
- a report exists without manifest when artifacts were generated
- Slack, frontend, or Graphify output is presented as strategy acceptance
- proxy PnL is mixed with realized PnL
- Graphify output older than the task family is used as current state
- validation was skipped without a recorded reason

## Ownership

| Lead | Closeout Responsibility |
|---|---|
| 필수 | Final readiness and strategy acceptance language |
| 중훈 | Registry, manifests, operating docs, and closeout validation |
| Team lead | Team-specific report, blocker status, and validation evidence |

If closeout ownership is unclear, 중훈 owns the governance side and 필수 owns the readiness language until a more specific lead is assigned.
