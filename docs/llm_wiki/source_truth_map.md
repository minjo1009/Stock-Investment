# Source Truth Map

Use this file to avoid repeating broad source acquisition.

## Current Source Families

- SEC financing/dilution: `data/artifacts/task_2541_2560_sec_financing_dilution_acquisition/`
- Liquidity/rates regime: `data/artifacts/task_2561_2580_liquidity_rates_regime_acquisition/`
- Source-integrated selector diagnostic: `data/artifacts/task_2581_2600_source_integrated_selector_diagnostic/`
- DB/data operations audit: `docs/reports/task_3571_3580_db_data_ops_audit/` and `data/artifacts/task_3571_3580_db_data_ops_audit/`
- DB governance systemization: `docs/reports/task_3581_3600_db_governance_systemization/` and `data/artifacts/task_3581_3600_db_governance_systemization/`
- Latest source reports: `docs/reports/task_2541_2560_sec_financing_dilution_acquisition/`, `docs/reports/task_2561_2580_liquidity_rates_regime_acquisition/`, `docs/reports/task_2581_2600_source_integrated_selector_diagnostic/`

## Source Rules

- Missing source is never a negative label.
- Missing raw source is reported as a gap, not approximated.
- Retrieval timestamp alone does not open a strict gate.
- Feature/proxy rows must not be described as strict raw/as-of complete.
- API keys, tokens, and request secrets must never appear in reports, logs, or artifacts.
- Frontend catalog refresh is not source freshness.
- Active runtime DB freshness must be proven through DB/source receipt evidence, not inferred from file timestamps.
- After Task3581-3600, active `trading.db` must remain fail-closed unless a future approved task explicitly changes `control_state` with governance authority.

## When To Add More Sources

Add sources only when a paper/shadow run produces a specific unexplained failure:

- MDD attribution shows a source gap.
- thesis break cannot be explained from existing source packets.
- challenger policy requires a named missing source family.
- vendor/API blocker is explicit and documented.

Do not add sources merely because performance is disappointing.

## Skill Boundary

Use `trader-brain-source-acquisition` for governed source acquisition. Do not duplicate source collection rules inside paper, MDD, policy, or docs/wiki skills.

## DB Management Program

- Current DB authority and cadence contract: `docs/reports/task_3601_3640_db_management_program/task_3601_3640_db_management_program.md`
- DB topology and scheduler contracts: `docs/db/`
- Read-only MCP DB copy: `data/readonly_mcp/trading_readonly_latest.db`
- Safety remains `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN`.

## DB Loop Contract Schema

- Task3641-3660 installed DB-resident loop contracts: `scheduler_job_registry`, `source_freshness_policy`, `reference_hashes`, `data_lineage_edges`.
- Loop registration is diagnostic-only and does not permit broker mutation, paper promotion, live orders, replay, deployment, or real capital.
- Current blockers remain source freshness, receipts, lineage, scheduler recurrence, and L6 authority evidence.

