# Project Structure & Operating Model Audit (2026-04-24)

## Scope
This audit covers:
1. Folder/file organization and artifact hygiene
2. Storage/management consistency risks
3. Orchestrator vs sub-agent operating model readiness

---

## 1) Structure Check (Current State)

### Strengths
- Top-level boundaries are mostly clear: `src/`, `tests/`, `docs/`, `data/`, `tasks/`, `phases/`, `context/`, `scripts/`.
- Research outputs are generally collected in `docs/` with task-based naming (`task_066B_*`, `task_068B_*`).
- Core architecture split exists in code:
  - `src/strategy`, `src/execution`, `src/risk`, `src/analytics`, `src/experiments`.

### Friction Points
1. Mixed artifact classes in `docs/`
- durable specs/contracts and ephemeral run artifacts/logs are mixed together.
- examples: `execution_state_contract.md` and `task_068B_risk_grid.run.log` live side-by-side.

2. Temporary files mixed with official outputs
- `tmp_pre_068c_validation.json`, `tmp_post_068c_validation.json` are in `docs/`.

3. Execution caches are heavily present under source tree
- many `__pycache__` directories exist under `src/`, `tests/`, and `data/`.
- `.gitignore` excludes them, but working tree readability is reduced.

4. Task/process docs show encoding inconsistency risk
- several files under `tasks/` and `context/workflow/` render garbled in current shell output.
- this can break shared understanding of process contracts.

5. Reference corpus mixed into active repo root
- `참고 Context/` holds large external source trees under the same root as active code/artifacts.
- this increases navigation noise and accidental scope drift risk.

---

## 2) Storage / Management Assessment

### Verdict
`PARTIALLY_ORDERED`

The project is not chaotic, but artifact lifecycle is not fully managed yet.

### Key Risks
1. Auditability risk
- hard to separate "official decision artifact" vs "temporary debug/run file".

2. Discoverability cost
- operator/researcher spends extra time locating latest canonical report.

3. Process-contract drift risk
- workflow templates/contracts exist, but operational records are not stored in the expected structured artifact path.

### Immediate Fixes (No code refactor required)
1. Split docs by lifecycle:
- `docs/reports/` (task outputs)
- `docs/contracts/` (state/cancel/policy contracts)
- `docs/audits/` (architecture/execution audits)
- `docs/tmp/` (scratch and transient files)

2. Add a simple index:
- `docs/INDEX.md` with "latest canonical outputs" by task id.

3. Enforce UTF-8 normalization for process docs:
- `tasks/*.md`, `context/workflow/*.md` first priority.

4. Keep external references in dedicated archive root:
- move/alias `참고 Context/` under a clearly non-runtime path (e.g., `references/`).

5. Add a housekeeping script:
- clean `__pycache__` and rotate oversized run logs.

---

## 3) Orchestrator / Sub-Agent Operating Model Check

### What Exists
- Process design artifacts exist:
  - `tasks/task-013-artifact-layout-convention.md`
  - `tasks/task-014-subagent-handoff-template.md`
  - `context/workflow/execution-rules.md`
  - `context/workflow/state-management.md`

### What Is Missing in Practice
1. Missing structured execution trail
- expected `artifacts/<task-id>/...` handoff chain is not populated.
- no active artifact directory evidence for stage-by-stage handoff snapshots.

2. Missing explicit ownership registry per task
- no visible "orchestrator owns X, sub-agent owns Y" ledger for recent tasks.

3. Missing unified task state board
- no machine-readable task state file showing `created/in_progress/done/blocked` at run-time.

### Verdict
`PARTIALLY_READY`

The design for orchestrator/sub-agent collaboration exists, but operational enforcement evidence is weak.

---

## Recommended Responsibility Split (Actionable)

### Orchestrator (Single owner)
- Task scope lock (hard constraints)
- Final decision gates (`PASS/WARNING/FAIL`)
- Integration consistency checks across strategy/execution/risk/ui
- Canonical report publication to `docs/reports/`

### Sub-Agents (Parallel bounded work)
- Bounded analyzers:
  - `backtest scenario runner`
  - `risk attribution runner`
  - `UI data-binding verifier`
- Each sub-agent output must include:
  - changed files
  - assumptions
  - validation command/result
  - unresolved risks

### Mandatory Handoff Contract
- use one file per stage:
  - `artifacts/<task-id>/clarify.md`
  - `artifacts/<task-id>/context-gather.md`
  - `artifacts/<task-id>/plan.md`
  - `artifacts/<task-id>/generate.md`
  - `artifacts/<task-id>/evaluate.md`

---

## Priority Plan (Short)

1. **P0**: create `docs/INDEX.md` and lifecycle subfolders.
2. **P0**: move tmp/log artifacts from `docs/` root to `docs/tmp/`.
3. **P1**: enable `artifacts/<task-id>/` logging for next task onward.
4. **P1**: add `tasks/state.json` (single source of task status truth).
5. **P2**: UTF-8 normalize legacy process docs to remove encoding noise.

---

## Bottom Line
- Folder structure is fundamentally usable, but artifact governance needs tightening.
- Orchestrator/sub-agent model is documented, not yet fully operationalized.
- If we apply the P0/P1 steps above, management quality moves quickly from `PARTIALLY_ORDERED` to `WELL_GOVERNED`.
