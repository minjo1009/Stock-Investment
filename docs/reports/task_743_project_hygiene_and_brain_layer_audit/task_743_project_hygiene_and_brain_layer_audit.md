# Task743 Project Hygiene And Brain Layer Audit

## Decision Summary

- Verdict: `PROJECT_CLEANUP_REQUIRED_BEFORE_MORE_BRAIN_FEATURES`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Current tracked files: 124
- Dirty worktree: 983 untracked, 16 modified, 3 deleted
- Largest local areas: `data` about 7.8GB, `docs` about 5.9GB, `frontend` about 341MB
- Next action: commit only cleanup policy, brain layer map, and selected canonical code after review.

## Quant Expert Report

### Data Source And Source Readiness

This audit used local Git and filesystem metadata only:

- `git status --porcelain=v1`
- `git ls-files`
- top-level directory file counts and byte sizes
- Task727 through Task742 source/report/test inventory

No market outcome, PnL, forward return, account, broker, or live trading source was used.

### Exact Join Keys

Not applicable. This is a repository hygiene audit, not a market data join task.

### Leakage Audit

No strategy assignment logic was created.

No outcome, PnL, label, score, rank, buy/sell, sizing, or backtest eligibility output was created.

### Failure Decomposition

| Area | Finding | Risk |
| --- | --- | --- |
| Git control | Git tracks only 124 files while 983 files are untracked. | Reproducibility, review, rollback, and GitHub push safety are weak. |
| Artifact boundary | `data` and `docs` contain multi-GB local outputs. | Large files can pollute GitHub and make the repo hard to clone. |
| Report layout | Task reports mix small decisions with large CSV/JSONL panels. | It is unclear what should be committed. |
| Brain layers | Task727 through Task742 are conceptually coherent but not canonicalized. | Multiple layers can coexist and confuse downstream use. |
| Registry discipline | Registry exists, but commit eligibility and brain-layer ownership are not explicit enough. | Future tasks can keep adding code without cleanup gates. |

### Brain Layer Audit

The conceptual structure is directionally correct:

```text
source evidence -> primitive fact -> economic meaning -> relation edge -> candidate bundle -> slot decision
```

The management issue is not the idea. The issue is that task outputs, reports, tests, and generated panels are not separated cleanly.

Task742 is the active practical economic meaning candidate. Task741 remains a denominator audit, but it is too blocker-heavy to serve as the active practical economic interpretation layer.

### Cleanup Decision

Do not delete local artifacts yet.

First, add repository policy:

- strengthen `.gitignore`
- add brain layer map
- add task registry contract
- keep GitHub focused on code, tests, small contracts, small decisions, and manifests

### Remaining Blockers

- No canonical subset of Task727 through Task742 has been selected for commit.
- Large existing `docs/reports` and `data/artifacts` outputs remain local.
- Modified/deleted tracked files still need a separate review before staging.

## No-Background Decision-Maker Report

The project is not broken because one model is wrong.

The project is messy because too many experiments were added without a strong repo boundary.

The next move is not another trading rule. The next move is cleanup:

1. keep code and tests
2. keep small contracts and summaries
3. keep large raw/artifact files local
4. choose one current brain path instead of treating every task as active

## Artifact Manifest

- `docs/architecture/brain_layer_map.md`
- `docs/contracts/task_registry_contract.md`
- `docs/reports/task_743_project_hygiene_and_brain_layer_audit/task_743_project_hygiene_and_brain_layer_audit.md`
- `docs/reports/task_743_project_hygiene_and_brain_layer_audit/task_743_decision.csv`
- `docs/reports/task_743_project_hygiene_and_brain_layer_audit/task_743_pass_fail_matrix.csv`

## Validation Commands

```powershell
python scripts\task_registry_validate.py
git status --porcelain=v1
```
