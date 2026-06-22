# Task603 - Registry Consumption Audit

## Decision Summary

- Verdict: `PRIMARY_PASS` for consumption audit.
- Scope: grep-based audit for `NOT_ACCEPTED`, `BLOCKED`, and `READY_FOR_CONTROLLED_PAPER_RUN`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Finding: registry/readiness files are validated and partially consumed by catalog/governance tooling, but current frontend readiness display and several report builders still depend on generated artifacts or hardcoded status strings.
- Next action: create a follow-on implementation task that makes frontend/catalog readiness read from `docs/ownership/readiness_registry.yaml` or a derived canonical JSON, rather than re-deriving readiness independently.

## Quant Expert Report

### Audit Method

Commands used:

```powershell
rg -n "NOT_ACCEPTED|BLOCKED|READY_FOR_CONTROLLED_PAPER_RUN" src scripts frontend tests validate_readiness_registry.py -g "*.py" -g "*.jsx" -g "*.js" -g "*.ts" -g "*.tsx"
rg -n "readiness_registry|task_registry|current_operating_model|load_task_registry|CatalogPaths|validate_readiness_registry" src scripts frontend tests validate_readiness_registry.py -g "*.py" -g "*.jsx" -g "*.js" -g "*.ts" -g "*.tsx"
rg -n "NOT_ACCEPTED|READY_FOR_CONTROLLED_PAPER_RUN|DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY|BLOCKED" frontend/trader-terminal/public frontend_data -g "*.json" -g "*.csv" -g "*.md"
```

### Registry-Backed Consumption

| Area | Evidence | Classification |
|---|---|---|
| Research task catalog | `src/reporting/research_task_catalog.py` reads `tasks/task_registry.csv` through `load_task_registry` | registry-backed |
| Paper runtime common | `src/app/paper_runtime_common.py` has `append_registry_rows` for task registration | registry writer |
| Governance validation | `scripts/task_registry_validate.py`, `scripts/governance_completion_audit.py` validate registry and readiness registry | registry/readiness validation |
| Readiness validation | `validate_readiness_registry.py` reads `docs/ownership/readiness_registry.yaml` | readiness-backed validation |
| Project governance tests | `tests/test_project_governance.py` validates `tasks/task_registry.csv` | registry-backed test |

### Hardcoded Or Re-Derived Status Usage

| Area | Evidence | Risk |
|---|---|---|
| Trader terminal catalog builder | `scripts/build_trader_terminal_catalog.py` emits `READY_FOR_CONTROLLED_PAPER_RUN`, `PAPER_READY_BLOCKED`, and derives blocked state from scorecard statuses | readiness can drift from canonical `readiness_registry.yaml` |
| Frontend app | `frontend/trader-terminal/src/App.jsx` hardcodes `PAPER_READY_BLOCKED` copy and checks `paperReadinessStatus === "BLOCKED"` | UI may show a readiness state not directly sourced from registry |
| Generated frontend catalogs | `frontend_data/catalog/*.json` and `frontend/trader-terminal/public/catalog/*.json` contain readiness/status literals | generated data can become stale and look authoritative |
| Historical task builders | many `src/backtest/build_task*.py` files write task-specific acceptance/status strings | acceptable for historical reports, but not a current program source of truth |

### Interpretation

The project now has a canonical readiness registry, but runtime/frontend consumption is not fully registry-backed yet.

This is not a failure of T600/T601/T602 design work. It is a governance and integration gap:

- Registry exists.
- Readiness registry exists.
- Validators read them.
- Some catalog tooling reads `tasks/task_registry.csv`.
- The frontend readiness surface still depends on generated catalog fields and local UI strings.

Therefore the next implementation should expose readiness registry state through a generated canonical payload, then make the catalog/frontend consume that payload.

### Required Follow-On

Recommended follow-on task:

```text
T603-1 Registry-Backed Readiness Consumption
```

Minimum scope:

- build `frontend_data/catalog/readiness_registry.json` from `docs/ownership/readiness_registry.yaml`
- update `scripts/build_trader_terminal_catalog.py` to include that payload
- update frontend to display paper/strategy/deployment status from the canonical payload
- keep generated catalog warnings, but do not let them redefine readiness

## No-Background Decision-Maker Report

필수에게 보고합니다.

registry는 존재하고 검증도 됩니다. 하지만 UI와 catalog는 아직 완전히 registry를 기준으로 상태를 읽는 구조가 아닙니다.

현재 가장 중요한 위험은 이것입니다.

`readiness_registry.yaml`에는 `NOT_ACCEPTED`라고 되어 있는데, frontend나 generated catalog가 별도로 `READY`, `BLOCKED`, `PAPER_READY_BLOCKED` 같은 값을 만들어 보여줄 수 있습니다. 그러면 또 “공식 상태가 어디냐” 문제가 생깁니다.

오늘 결론은 명확합니다. T603은 현재 상태를 감사했고, 다음 구현은 registry-backed readiness payload를 만들어 frontend/catalog가 그것을 읽도록 해야 합니다.

## Artifact Manifest

See `artifact_manifest.csv`.
