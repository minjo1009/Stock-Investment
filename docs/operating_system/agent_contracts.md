# Agent Contracts

## Shared Handoff Format
Every agent output must include:

- responsibility summary
- input artifacts read
- files changed or proposed
- validation performed
- risks and stop conditions
- next handoff owner

## Agent Contracts

| agent | responsibility | allowed files | forbidden files | required inputs | required outputs | validation responsibility |
|---|---|---|---|---|---|---|
| Architecture Orchestrator | Own architecture plan, task boundaries, and final gates | `docs/architecture`, `docs/operating_system`, phase/task docs | Trading behavior files unless task explicitly allows | user objective, inventory, audit reports | final plan/report/manifest | Consistency across manifests, reports, and constraints |
| Graphify Analyst | Produce graph scopes, exclusions, and graph interpretation | `docs/graphify`, graph reports | Production runtime code | graph outputs, inventory | graph cleanup plan, context pack rules | Graph modes include/exclude expected paths |
| Repository Curator | Classify files and propose moves | inventory docs, migration plans | Business logic edits | file tree, imports | repository inventory, staged movement map | Movement risk and rollback clarity |
| Domain Model Architect | Define domain boundaries and contracts | architecture docs, contracts | Broker/API execution code | domain model, contracts | layer responsibilities and invariants | No forbidden ownership overlap |
| Backtest Architect | Own backtest boundary and research separation | backtest docs, experiment plans | Live broker code | backtest engine/reports | backtest migration and reliability plan | Backtest cannot depend on live broker |
| Execution Architect | Own order lifecycle, cancel, reconciliation boundaries | execution docs/contracts | Strategy alpha code | state contract, broker lifecycle reports | execution boundary recommendations | Execution cannot compute alpha |
| Risk Architect | Own risk gate policy and approval boundary | risk docs/contracts | Broker client code | risk policies, evidence | risk approval contract | Risk remains final pre-execution gate |
| Storage Architect | Own persistence and artifact storage rules | storage docs, schema docs | Strategy logic | DB schema, report paths | storage conventions | State and artifacts are traceable |
| Test Architect | Own boundary/regression test design | test plans, proposed tests | Live broker credentials or real order commands | manifest, imports | boundary test plan | Tests are safe and non-broker-mutating |
| Documentation Steward | Own templates, index, and readability | docs, templates | Runtime code | generated artifacts | final report, index updates | Required sections and links exist |

