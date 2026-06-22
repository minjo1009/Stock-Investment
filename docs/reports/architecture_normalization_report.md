# Architecture Normalization Report

## 1. Executive Summary
This task establishes an architecture operating system for the project. It creates inventory, canonical layers, dependency rules, phase/task templates, agent contracts, storage rules, Graphify cleanup rules, migration stages, and boundary test proposals. No trading behavior, broker behavior, strategy parameter, or production code was changed.

## 2. Current Disorder Diagnosis

- Graphify communities are split because task-specific code lives beside production runtime modules.
- `src/app/task_*.py` and `src/backtest/analysis_*` mix task artifacts and experiments into production-looking namespaces.
- `docs/reports/task_*` contains valuable evidence but is not phase-owned yet.
- `참고 Context/` contains external reference material that should not shape the production graph.
- Orchestrator/sub-agent rules exist in older task docs and skills, but they are not yet canonicalized into a single operating system.

## 3. Canonical Architecture Proposal
The canonical architecture is defined in `docs/architecture/canonical_architecture.md` and `docs/architecture/architecture_manifest.yml`. Minimum layers include market_data, universe, features, strategy, risk, execution, portfolio, broker, storage, reporting, intelligence, apps, backtest, replay, tests, docs, experiments, and archive.

## 4. Phase/Task Operating System
The operating system is defined in `docs/operating_system/phase_task_system.md`, `task_template.md`, and `phase_template.md`. Each phase owns task specs, reports, and decisions. Each task declares owner agent, sub-agents, required skill, artifacts, file boundary, validation, rollback, and report path.

## 5. Agent/Orchestrator Model
The orchestrator model is defined in `docs/operating_system/orchestrator_model.md` and `agent_contracts.md`. The Architecture Orchestrator owns scope and final gates; specialized agents own Graphify, repository curation, domain boundaries, backtest, execution, risk, storage, tests, and documentation.

## 6. Storage Normalization Rules
`docs/operating_system/artifact_storage_rules.md` defines the target structure under `docs/phases`, `docs/graphify`, `experiments`, and `archive`. No file moves were performed in this task; all moves are staged recommendations.

## 7. Graphify Cleanup Rules
`docs/graphify/graphify_cleanup_plan.md` and `docs/graphify/graphify_exclude.yml` define production and research graph modes. Production graph excludes external references, experiments, task scripts, reports, caches, and virtual environments by default.

## 8. Migration Roadmap
`docs/architecture/migration_plan.md` defines five stages: inventory only, move obvious references/artifacts, extract app logic into canonical layers, add boundary tests, and regenerate/compare Graphify outputs. Each stage includes files affected, risk, validation, and rollback.

## 9. Immediate Next Tasks

1. Review `repository_inventory.json` movement candidates and approve Stage 2 scope.
2. Create phase directories beginning with `PHASE_01` and migrate only approved reports.
3. Decide which `src/app/task_*.py` modules are promoted versus moved to `experiments/task_runs`.
4. Run production Graphify using `graphify_exclude.yml` and compare god nodes.
5. Implement boundary tests as non-blocking once expected current violations are documented.

## 10. Risks and Stop Conditions

- Stop if any proposed movement would break imports, report paths, or paper evidence collection.
- Stop if a cleanup task attempts to change strategy, risk, broker, or execution behavior without explicit approval.
- Stop if external references are hidden in a way that loses research provenance.
- Stop if Graphify exclusions remove safety-critical production code from the production graph.

## Required Artifacts Created

- `docs/architecture/repository_inventory.md`
- `docs/architecture/repository_inventory.json`
- `docs/architecture/canonical_architecture.md`
- `docs/architecture/architecture_manifest.yml`
- `docs/architecture/migration_plan.md`
- `docs/architecture/boundary_test_plan.md`
- `docs/operating_system/phase_task_system.md`
- `docs/operating_system/task_template.md`
- `docs/operating_system/phase_template.md`
- `docs/operating_system/agent_contracts.md`
- `docs/operating_system/orchestrator_model.md`
- `docs/operating_system/artifact_storage_rules.md`
- `docs/graphify/graphify_cleanup_plan.md`
- `docs/graphify/graphify_exclude.yml`
- `docs/reports/architecture_normalization_report.md`

