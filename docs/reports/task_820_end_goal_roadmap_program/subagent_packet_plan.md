# Task820-Task827 Subagent Packet Plan

Objective: Move the Trader Brain relationship graph from operational validation toward candidate bundle and controlled backtest-adapter readiness, without creating trade signals or acceptance claims.

Owner Team: Research Governance

Reviewer Team: Data and Market Microstructure + Backtest and Simulation Infra

Read Scope:

- `README.md`
- `docs/operating_system/project_operating_state.md`
- `docs/reports/task_812_gpt_expert_next8_program/`
- `docs/reports/task_813_golden_graph_fixture_pack/`
- `docs/reports/task_816_provenance_manifest_linker_contract/`
- `docs/reports/task_819_next8_closeout_handoff/`
- `docs/architecture/test_validation_canonicalization_map.md`

Write Scope:

- Task820 worker: `docs/reports/task_820_end_goal_roadmap_program/`
- Task821 worker: `docs/reports/task_821_graph_fixture_corpus_expansion/`
- Task822 worker: `docs/reports/task_822_provenance_coverage_audit/` and `scripts/trader_brain_provenance_coverage_audit.py`
- Task823 worker: `docs/reports/task_823_candidate_bundle_adapter_contract/` and `scripts/trader_brain_candidate_bundle_validate.py`
- Task824 worker: `docs/reports/task_824_contradiction_invalidation_propagation/`
- Task825 worker: `docs/reports/task_825_attention_memory_eviction_rules/`
- Task826 worker: `docs/reports/task_826_backtest_adapter_readiness_checklist/`
- Task827 worker: `docs/reports/task_827_go_no_go_closeout/`, `scripts/trader_brain_820_827_program_validate.py`, registry and operating-state updates.

Required Outputs:

- End-goal roadmap.
- Expanded graph fixture corpus.
- Provenance coverage audit.
- Candidate bundle adapter contract and validator.
- Contradiction propagation rule table.
- Attention/memory eviction policy.
- Controlled backtest adapter readiness checklist.
- Go/no-go closeout.

Forbidden Actions:

- No buy/sell output.
- No rank or global top list.
- No score or hidden alpha total.
- No actual sizing or allocation.
- No backtest execution.
- No backtest eligibility assignment.
- No runtime or broker integration.
- No symbol/date/price/time fallback matching.
- No missing-to-negative conversion.
- No strategy acceptance claim from test success.

Validation Command:

`python scripts/trader_brain_820_827_program_validate.py`

Validation Authority:

GOVERNANCE_HEALTH and RESEARCH_ONLY only. PASS does not mean strategy acceptance, deployment readiness, broker truth completion, source completeness, backtest validity, or real-capital permission.

Report Requirement:

Use `docs/report_standard.md`. Keep chat reports short and put detailed evidence in task artifacts.
