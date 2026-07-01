# Brain Code Operating Loop

## Purpose

This runbook keeps backend brain contracts, runtime catalogs, frontend read models, and governance closeout moving as one repeatable loop.

It is not a command center and not a source of truth. Current truth remains in:

- `docs/operating_system/project_operating_state.md`
- `tasks/task_registry.csv`
- `docs/reports/<task_id>/`
- artifact manifests
- validator outputs

## Standing Boundaries

- Strategy: `NOT_ACCEPTED`
- Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real Capital: `FORBIDDEN`

No brain/code loop may change these statuses from test success alone.

## Ten-Loop Operating Pattern

| Loop | Task | Purpose | Validation Authority |
| --- | --- | --- | --- |
| 1 | Task3181 | Confirm current brain/code source-of-truth files before editing. | `GOVERNANCE_HEALTH` |
| 2 | Task3182 | Route subagent exploration through bounded read-only packets. | `GOVERNANCE_HEALTH` |
| 3 | Task3183 | Verify package exports for `src/brain` remain narrow and non-executional. | `PACKAGE_HEALTH` |
| 4 | Task3184 | Verify L3-L7 contract invariants and no assignment leakage. | `PACKAGE_HEALTH` |
| 5 | Task3185 | Verify L6/L7 runtime catalog adapter stays read-only. | `REPORTING_HEALTH` |
| 6 | Task3186 | Verify frontend gets versioned read models, not raw task artifacts. | `REPORTING_HEALTH` |
| 7 | Task3187 | Keep external tools as optional diagnostic infrastructure only. | `GOVERNANCE_HEALTH` |
| 8 | Task3188 | Keep Obsidian and LLM wiki as navigation layers only. | `GOVERNANCE_HEALTH` |
| 9 | Task3189 | Run registry and governance closeout validation. | `GOVERNANCE_HEALTH` |
| 10 | Task3190 | Record final blockers, next action, and status boundaries. | `GOVERNANCE_HEALTH` |

## Required Local Commands

Run these when this loop changes code, reports, registry rows, or operating documents:

```powershell
python -m unittest tests.test_brain_runtime_contracts tests.test_brain_runtime_catalog_adapter
python scripts/trader_brain_3164_runtime_catalog_adapter_validate.py
python scripts/trader_brain_3181_3190_brain_code_operating_loop_validate.py
python scripts/task_registry_validate.py
python scripts/operating_closeout_validate.py
python scripts/governance_completion_audit.py
```

## Allowed Work

- Add or tighten typed contracts.
- Add package-health tests around promoted contracts.
- Add read-only adapters from versioned runtime catalogs.
- Add validator outputs under `data/artifacts/<task_id>/`.
- Update task reports, manifests, registry rows, and navigation links.

## Forbidden Work

- No replay or backtest.
- No selector, ranking, sizing, or order mutation.
- No paper order or live order creation.
- No source gap approximation.
- No broker-truth claim from shadow, simulated, fallback, or UI rows.
- No acceptance, deployment, or real-capital claim from validator success.

## Closeout Rule

Every loop must leave a reviewer able to answer:

1. Which layer changed?
2. Which report and registry row record it?
3. Which validator ran?
4. What does PASS mean?
5. What does PASS not mean?

