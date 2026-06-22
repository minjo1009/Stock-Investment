---
tags:
  - frontend
  - obsidian
  - diagnostic-only
---

# Frontend App Map

Use this map to navigate frontend/app planning. It is a pointer layer only.

## Current Rule

The frontend is read-only unless future operating documents explicitly change status.

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## SSOT Pack

- LLM route: [Frontend App SSOT Pack](../../llm_wiki/frontend_app_ssot_pack.md)
- Source inputs:
  - `C:/Users/minjo/Downloads/00_PROJECT_SSOT.md.docx`
  - `C:/Users/minjo/Downloads/01_DETAIL_ARCHITECTURE.md.docx`
  - `C:/Users/minjo/Downloads/02_DESIGN_SYSTEM.md.docx`
  - `C:/Users/minjo/Downloads/03_IMPLEMENTATION_ARCHITECTURE.md.docx`

## Fixed IA

- `HOME`
- `BRAIN`
- `PORTFOLIO`
- `ORDERS`
- `SYSTEM`

Do not add Backtest, Paper, or Live as top-level tabs. Treat them as lifecycle states.

## Universal Detail Frame

- Decision / Summary
- Thesis / Logic
- Evidence
- Risk
- Action

## Current Anchors

- Operating state: [Project Operating State](../../operating_system/project_operating_state.md)
- LLM wiki index: [LLM Wiki](../../llm_wiki/README.md)
- Latest artifact index: [Task Artifact Index](../../llm_wiki/task_artifact_index.md)
- Runtime/frontend bridge: [Task3391-3400](../../reports/task_3391_3400_frontend_review_bridge/task_3391_3400_frontend_review_bridge.md)
- DB scheduler/freshness latest: [Task3761-3800](../../reports/task_3761_3800_db_source_scheduler_config_freshness_validator/task_3761_3800_db_source_scheduler_config_freshness_validator.md)

## Build Guardrails

- Show source freshness and blockers clearly.
- Preserve decision-reason-evidence-source chain.
- Keep broker mutation, paper promotion, live order, and real-capital actions disabled unless governance changes.
- Do not treat polished UI as validation.
- Use reports, manifests, registry rows, and validators as authority.
