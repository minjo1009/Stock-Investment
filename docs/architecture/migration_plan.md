# Migration Plan

## Principle
Do not perform large file moves immediately. Migration proceeds by documented stages with validation and rollback at each step.

## Stage 1 - Inventory and Classification Only

- files affected: `docs/architecture/repository_inventory.*`, architecture docs
- risk: low
- validation command: parse inventory JSON and verify required keys
- rollback plan: remove generated documentation only
- status: current task

## Stage 2 - Move Obvious External References and Obsolete Task Artifacts

- files affected: `docs/archive/external_context/참고 Context/`, obvious obsolete task reports/scripts after approval
- risk: medium for references, high for task scripts imported by workflows
- validation command: run import tests and Graphify production graph before/after
- rollback plan: move files back using old-to-new relocation manifest

## Stage 3 - Extract App-Level Business Logic into Canonical Layers

- files affected: selected `src/app/*.py`, future layer modules
- risk: high
- validation command: unit tests, paper dry-run tests, no broker/API calls
- rollback plan: revert extraction commit and restore previous imports

## Stage 4 - Add Architecture Boundary Tests

- files affected: `tests/test_architecture_boundaries.py` after approval
- risk: low to medium; tests may expose existing violations
- validation command: `python -m unittest tests.test_architecture_boundaries`
- rollback plan: remove or relax new boundary tests with decision record

## Stage 5 - Regenerate Graphify and Compare Before/After

- files affected: `docs/graphify/raw`, `docs/graphify/clean`, `docs/graphify/reports`, `docs/graphify/context_packs`
- risk: low
- validation command: Graphify generation plus god-node/community comparison
- rollback plan: keep previous graph artifacts and mark new graph rejected

## Stop Conditions

- Any move breaks imports or report paths.
- Any refactor changes trading behavior without an explicit task.
- Any Graphify cleanup hides safety-critical runtime code.
- Any migration step lacks rollback instructions.

