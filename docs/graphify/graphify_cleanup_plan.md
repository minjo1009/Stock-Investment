# Graphify Cleanup Plan

Last reviewed: 2026-06-03

## Current Validity

The current Graphify outputs were generated on 2026-04-25. They are stale for current paper-ops governance and do not include Task584/589/590/595/596/597/598/599 operating changes.

Do not use `docs/graphify/context_packs.json`, `docs/graphify/community_labels.json`, `docs/graphify/god_nodes_top20_local.json`, or `graphify-out/` as current ownership, blocker, readiness, or paper-trading state until Graphify is regenerated.

Use `docs/ownership/current_operating_model.md` for current operations.

## Diagnosis
Current Graphify output is useful but noisy. Prior audit shows external reference strategies dominate centrality, `src/ui/app.py` and task scripts appear as high-connection hubs, and contracts/reports are weakly normalized as graph concepts.

## Default Exclusions
Use `docs/graphify/graphify_exclude.yml` as the canonical exclusion profile. Default production graph excludes:

- `docs/archive/external_context/참고 Context/`
- `archive/`
- `experiments/`
- `docs/reports/`
- `**/task_*.py`
- `**/run_task_*.ps1`
- `**/__pycache__/`
- `.venv/`

## Graph Modes

### production_graph
Includes production runtime/library/app/test/config and canonical docs. Excludes reports, external references, experiments, one-off task files, and caches.

### research_graph
Includes experiments and references, but separates them into explicit groups so they do not masquerade as production architecture.

## Cleanup Steps

1. Generate production graph with default exclusions.
2. Confirm canonical nodes exist for strategy, risk, execution, broker, storage, backtest, apps, tests, docs.
3. Generate research graph separately with external references grouped.
4. Compare god nodes before/after exclusion.
5. Promote useful graph findings into `docs/architecture/migration_plan.md` or phase decisions.

Before regeneration, delete stale generated cache under `graphify-out/cache/`. Keep historical audit reports under `docs/audits/`.

## Acceptance Criteria

- External reference strategies no longer dominate production graph centrality.
- Task scripts are not first-class production nodes unless promoted.
- Contract docs and architecture manifests are visible in graph context packs.
- Graph outputs are stored as raw, clean, report, and context-pack artifacts.
