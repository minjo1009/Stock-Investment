# Module Ownership Map

Last updated: 2026-06-03

## Purpose

This document maps named project leads to the current repository assets they must know, maintain, or review. It does not move files. It is the first-pass ownership index for future task routing, review assignment, and cleanup.

## Lead Roster

| Lead | Area | Existing Canonical Team | Scope |
|---|---|---|---|
| 필수 (=Regime) | Strategy: Regime / Overall Strategy Lead | Regime Research | Overall strategy direction, multi-day market/theme regime, theme universe, regime gate quality |
| 성원 | Strategy: Intraday | Intraday Continuation Research | Intraday continuation states, entry-safe factors, VWAP/continuation archetypes |
| 종찬 | Strategy: Chart | Intraday Continuation Research | Chart evidence used by strategy review: OHLC windows, entry/exit markers, indicator overlays |
| 중훈 | Project folder/storage/discipline | Research Governance | Registry, report standard, artifact policy, architecture inventory, migration/archival rules |
| 서연 | Slack reporting | Research Governance | Trade alert delivery, EOD report delivery, duplicate-send guard, supervisor failure alert path |
| 동승 | Backtest management | Backtest & Simulation Infra | Deterministic replay, cost/slippage, walk-forward/OOS, portfolio simulation |
| 윤헌 | Data management | Data & Market Microstructure | Raw/live market data, microstructure, calendar, source provenance, freshness validation |
| 규승 | Frontend/UI | Research Governance | Trader terminal mobile UI, catalog-backed rendering, paper trading account/trade pages |
| 주은 | Execution & Risk | Execution & Risk | Exit/trim/stop lifecycle, broker-truth reconciliation, exposure limits, kill-switch and risk reporting |

## Current Operating Source

Use `docs/ownership/current_operating_model.md` as the current paper-ops operating source. Task598 supersedes Task595 and Task596 for paper-week diagnosis when they conflict.

## Sublead Hiring Plan

These names are subleads under the existing leads. They do not replace the lead. Each sublead owns a narrower asset surface and must hand results back to the lead for acceptance.

| Lead | Sublead | Role | Why This Role Exists | First Read Scope | First Assignment |
|---|---|---|---|---|---|
| 필수 | 민재 | Strategy Acceptance Gate | Prevents promising diagnostics from being described as approved strategy. | `tasks/task_registry.csv`, `docs/report_standard.md`, `docs/reports/task_512_backtest_correctness_overfit_audit/` | Define promotion checklist from diagnostic-only to promotion-ready. |
| 필수 | 하린 | Regime Feature QA | Confirms regime features are forward-live computable and not outcome-derived. | `docs/reports/task_489_broad_regime_cell_portfolio/`, `docs/reports/task_496_multi_day_regime_v4/`, `docs/reports/task_567_capital_flow_regime_v6/` | Audit regime fields for runtime availability and leakage risk. |
| 필수 | 태오 | Strategy Decision Log | Keeps why/why-not decisions readable after many task iterations. | `docs/operating_system/goal_operating_cycle.md`, `tasks/task_registry.csv`, `docs/reports/task_500_goal_loop_synthesis/` | Maintain strategy decision ledger for current canonical candidate. |
| 성원 | 지훈 | VWAP / Bandwalk Specialist | VWAP acceptance and bandwalk states are now too large for one intraday owner. | `docs/reports/task_550_anchored_vwap_band_walk_continuation/`, `docs/reports/task_557_vwap_acceptance_ontology_rebuild/` | Extract current VWAP/bandwalk definitions and blockers. |
| 성원 | 예준 | False Positive Analyst | Entry failures, entry_reduce, and whipsaws need dedicated failure taxonomy. | `docs/reports/task_498_entry_reduce_failure_decomposition/`, `docs/reports/task_510_entry_reduce_failure_decomposition/` | Build failure-mode checklist for every new intraday cell. |
| 성원 | 도윤 | Intraday State Taxonomy | Keeps state labels stable across backtest, runtime, and frontend. | `docs/reports/task_497_intraday_continuation_structure/`, `docs/reports/task_491_intraday_continuation_grid_development/` | Publish canonical intraday state dictionary draft. |
| 종찬 | 현우 | OHLC Entry Evidence | Entry/exit markers must be exact, auditable, and visually reviewable. | `frontend/trader-terminal/src/ChartBlocks.jsx`, `docs/reports/task_590_runtime_market_data_source_unification/` | Verify paper trade chart windows use runtime source lineage. |
| 종찬 | 서준 | Indicator Overlay Contract | Indicators shown on chart must match captured decision-time facts. | `scripts/build_trader_terminal_catalog.py`, `docs/frontend_data_contract.md` | List required indicator fields for runtime snapshots. |
| 종찬 | 민서 | Trade Review Evidence UX | Professional trade review needs a consistent evidence order. | `frontend/trader-terminal/src/App.jsx`, `docs/reports/task_589_nasdaq_paper_ops_hardening/` | Draft trade-detail evidence order: PnL, chart, reason, lineage. |
| 중훈 | 재윤 | Task Registry Manager | Registry state drives canonical/active/superseded decisions. | `tasks/task_registry.csv`, `scripts/task_registry_validate.py` | Identify rows missing validation or stale canonical status. |
| 중훈 | 수빈 | Artifact Librarian | Prevents reports and large artifacts from drifting without manifests. | `docs/artifact_policy.md`, `docs/contracts/artifact_manifest_v2_contract.md`, `scripts/bulk_artifact_manifest.py` | Audit recent task folders for missing `artifact_manifest.csv`. |
| 중훈 | 건우 | Architecture Boundary Reviewer | Stops strategy, data, runtime, and frontend responsibilities from blending. | `docs/architecture/canonical_architecture.md`, `docs/architecture/boundary_test_plan.md` | Mark current mixed-responsibility modules for later refactor. |
| 중훈 | 은채 | Validation Command Keeper | Ensures every task has a command that can be rerun. | `docs/operating_system/goal_operating_cycle.md`, `tasks/task_registry.csv` | Fill or flag missing `validation_command` values. |
| 서연 | 지아 | EOD Report Designer | End-of-day Slack report needs consistent infographic and plain-language flow. | `src/app/task_589_paper_eod_slack_report.py`, `docs/reports/task_589_nasdaq_paper_ops_hardening/` | Define EOD report sections and required charts. |
| 서연 | 나은 | Slack Delivery Safety | Webhook, duplicate guard, and secret leakage need separate safety ownership. | `src/integration/slack_client.py`, `tests/test_slack_client_safety.py` | Verify duplicate/secret guards before every Slack automation change. |
| 서연 | 유진 | Trading Team Feedback Writer | Converts trade evidence into actionable professional trading feedback. | `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-20.md` | Standardize feedback bullets into action, evidence, risk, next test. |
| 동승 | 준호 | Deterministic Replay Engineer | Backtest promotion needs identical outputs from identical inputs. | `src/backtest/source_truth_continuation_identity.py`, `src/backtest/source_truth_lineage.py` | Define deterministic replay invariants. |
| 동승 | 태민 | Walk-forward / OOS Analyst | Strong historical PnL must survive temporal validation. | `docs/reports/task_509_walk_forward_oos_validation/`, `docs/reports/task_512_backtest_correctness_overfit_audit/` | Summarize current OOS degradation blockers. |
| 동승 | 유찬 | Cost & Slippage Analyst | Limit-fill, spread, fee, and slippage realism can erase diagnostic edge. | `docs/reports/task_508_cost_stress_validation/`, `src/backtest/analysis_cost_sensitivity.py` | Build cost/slippage stress requirements for strategy promotion. |
| 동승 | 다온 | Portfolio Risk Simulator | Capacity, concentration, drawdown, and position caps require separate modeling. | `docs/reports/task_553_portfolio_realism_simulator/`, `docs/reports/task_505_two_year_pnl_grid/` | Define portfolio realism acceptance thresholds. |
| 윤헌 | 시우 | Runtime Data Engineer | Runtime DB tables must become the paper/live source of truth. | `trading.db`, `src/app/task_089_market_data_signal_refresh.py`, `docs/reports/task_590_runtime_market_data_source_unification/` | Map runtime tables and required missing fields. |
| 윤헌 | 하준 | Market Calendar / Session Guard | NASDAQ holiday, early close, ET session, and scheduler guards need one owner. | `src/app/nasdaq_market_calendar.py`, `scripts/install_task588_nasdaq_paper_loop_task.ps1` | Verify session guard behavior for holidays and early closes. |
| 윤헌 | 지완 | Microstructure Source Owner | NBBO, quote, spread, depth, status, and LULD are the live-readiness bottleneck. | `src/data/alpaca_historical_microstructure_export.py`, `src/data/full_depth_book_archive.py`, `docs/reports/task_495_microstructure_live_source_readiness/` | List missing sources blocking firm-grade microstructure. |
| 윤헌 | 채원 | Data Quality Auditor | Timestamp alignment, duplicate rows, freshness, and schema drift need constant audit. | `tests/test_data_quality.py`, `tests/test_task590_runtime_market_data_source_unification.py` | Create data quality checklist for runtime source refresh. |
| 규승 | 도하 | Mobile App UX | iPhone-first navigation and account/trade flow need constant product review. | `frontend/trader-terminal/src/App.jsx`, `frontend/trader-terminal/src/styles.css` | Keep mobile home screen aligned to investment-app conventions. |
| 규승 | 주원 | Trade Detail UI | Trade detail is the core paper-trading review surface. | `frontend/trader-terminal/src/App.jsx`, `frontend/trader-terminal/src/ChartBlocks.jsx` | Improve trade detail with chart, PnL, reason, and lineage order. |
| 규승 | 연우 | Frontend Data Contract | React must not bypass catalog provenance. | `docs/frontend_data_contract.md`, `scripts/build_trader_terminal_catalog.py`, `tests/test_trader_terminal_catalog.py` | Maintain frontend catalog-only read contract. |
| 규승 | 가온 | Visual QA | Mobile overflow, Korean encoding, and chart rendering need separate review. | `frontend/trader-terminal/src/styles.css`, `tests/test_task586_frontend_paper_ops_integration.py` | Run mobile layout and mojibake checks after UI changes. |
| 주은 | 민규 | Exit Lifecycle QA | Paper operation cannot be strategy-accepted while lifecycle is buy-only. | `docs/reports/task_598_paper_week_feedback_operating_plan/`, `src/app/task_589_paper_eod_slack_report.py` | Define exit/trim/stop proof requirements for paper mode. |
| 주은 | 지민 | Risk Budget Monitor | Open exposure, concentration, scale-in depth, and kill-switch state need daily evidence. | `docs/reports/task_589_nasdaq_paper_ops_hardening/`, `tests/test_task589_nasdaq_paper_ops_hardening.py` | Add daily exposure and kill-switch checks to the risk gate. |

## Current Asset Map

### 필수 (=Regime) - Strategy: Regime / Overall Strategy Lead

| Asset Type | Current Locations | Notes |
|---|---|---|
| Canonical registry rows | `tasks/task_registry.csv` rows owned by `Regime Research` | Current canonical row includes Task489; active rows include Task496, Task548, Task549, Task559, Task561, Task567. 필수 is the strategy lead over 종찬 and 성원. |
| Core code | `src/backtest/analysis_structural_breakout_task489_broad_regime_cell_portfolio.py`, `src/backtest/analysis_structural_breakout_task496_multi_day_regime_v4.py`, `src/backtest/analysis_structural_breakout_task548_market_theme_regime_feature_expansion.py`, `src/backtest/analysis_structural_breakout_task567_capital_flow_regime_v6.py` | Regime logic currently lives in task-scoped backtest/research modules, not a dedicated `src/strategy/regime` package. |
| Reports | `docs/reports/task_489_broad_regime_cell_portfolio/`, `docs/reports/task_496_multi_day_regime_v4/`, `docs/reports/task_548_market_theme_regime_feature_expansion/`, `docs/reports/task_549_theme_universe_leadership_contract/`, `docs/reports/task_567_capital_flow_regime_v6/` | These are the first places Regime should inspect before changing strategy gates. |
| Tests | `tests/test_task489_broad_regime_cell_portfolio.py`, `tests/test_task496_multi_day_regime_v4.py`, `tests/test_task483_firm_grade_market_theme_regime_upgrade.py`, `tests/test_analysis_regime_rebuild_511.py` | Regression safety for regime behavior. |

### 성원 - Strategy: Intraday

| Asset Type | Current Locations | Notes |
|---|---|---|
| Canonical registry rows | `tasks/task_registry.csv` rows owned by `Intraday Continuation Research` | Current canonical row includes Task493; active rows include Task491, Task497, Task498, Task503, Task510, Task516, Task524, Task529, Task550, Task557 and related continuation tasks. |
| Core code | `src/backtest/analysis_structural_breakout_task491_intraday_continuation_grid_development.py`, `src/backtest/analysis_structural_breakout_task493_microstructure_enhanced_continuation_grid.py`, `src/backtest/analysis_structural_breakout_task497_intraday_continuation_structure.py`, `src/backtest/build_multi_archetype_continuation_portfolio_discovery_403.py`, `src/backtest/build_refined_archetype_portfolio_rebuild_405.py` | Intraday work is distributed across task-specific research modules and builder modules. |
| Reports | `docs/reports/task_491_intraday_continuation_grid_development/`, `docs/reports/task_493_microstructure_enhanced_continuation_grid/`, `docs/reports/task_497_intraday_continuation_structure/`, `docs/reports/task_550_anchored_vwap_band_walk_continuation/`, `docs/reports/task_557_vwap_acceptance_ontology_rebuild/` | Use these as the current intraday research ledger. |
| Tests | `tests/test_task491_intraday_continuation_grid_development.py`, `tests/test_task493_microstructure_enhanced_continuation_grid.py`, `tests/test_task497_intraday_continuation_structure.py`, `tests/test_task499_regime_intraday_continuation_grid.py` | Must pass before intraday claims are promoted. |

### 종찬 - Strategy: Chart

| Asset Type | Current Locations | Notes |
|---|---|---|
| Frontend chart code | `frontend/trader-terminal/src/ChartBlocks.jsx`, `frontend/trader-terminal/src/App.jsx`, `frontend/trader-terminal/src/styles.css` | Chart UI currently renders backtest evidence and paper-trading OHLC entry context from catalog payloads. |
| Chart data contract | `docs/frontend_data_contract.md`, `docs/reports/task_586_frontend_paper_ops_integration/frontend_paper_ops_contract_v2.md`, `scripts/build_trader_terminal_catalog.py` | 종찬 owns what chart evidence must mean; 규승 owns final UI execution. |
| Reports/artifacts | `docs/reports/task_586_frontend_paper_ops_integration/`, `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_infographic_2026-05-20.html`, `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_indicator_snapshot_evidence.csv` | Current evidence visualization and EOD infographic references. |
| Tests | `tests/test_frontend_continuity_contract.py`, `tests/test_task586_frontend_paper_ops_integration.py`, `tests/test_trader_terminal_catalog.py` | Chart contract must remain catalog-backed; no raw task CSV reads from React. |

### 중훈 - Project Folder, Storage, and Discipline

| Asset Type | Current Locations | Notes |
|---|---|---|
| Operating rules | `AGENTS.md`, `docs/operating_system/goal_operating_cycle.md`, `docs/report_standard.md`, `docs/artifact_policy.md`, `docs/operating_system/artifact_storage_rules.md` | 중훈 is the keeper of how work is accepted, reported, and archived. |
| Registry | `tasks/task_registry.csv`, `tasks/archive_candidate_registry.csv`, `docs/architecture/repository_inventory.md`, `docs/architecture/repository_inventory.json` | Registry changes must be deliberate and validated. |
| Scripts | `scripts/task_registry_validate.py`, `scripts/codeowners_coverage_validate.py`, `scripts/governance_completion_audit.py`, `scripts/bulk_artifact_manifest.py`, `scripts/artifact_migration_plan.py`, `scripts/artifact_migrate_safe.py` | These are the discipline toolchain. |
| Tests | `tests/test_project_governance.py`, `tests/test_artifact_migration.py`, `tests/test_experiment_registry.py` | Governance changes require these checks. |

### 서연 - Slack Reporting

| Asset Type | Current Locations | Notes |
|---|---|---|
| Core code | `src/integration/slack_client.py`, `src/app/task_587_slack_trading_report_integration.py`, `src/app/task_589_paper_eod_slack_report.py`, `src/app/supervisor_slack_alert.py` | 서연 owns delivery safety and reporting shape, not trade decision generation. |
| Reports/artifacts | `docs/reports/task_587_slack_trading_report_integration/`, `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_slack_audit.csv`, `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback.csv`, `docs/reports/task_589_nasdaq_paper_ops_hardening/paper_eod_trading_team_feedback_2026-05-20.md` | Current Slack and EOD report evidence. |
| Tests | `tests/test_slack_client_safety.py`, `tests/test_task587_slack_trading_report_integration.py`, `tests/test_task589_nasdaq_paper_ops_hardening.py` | Slack writes must remain guarded and duplicate-safe. |
| Skill | `C:/Users/minjo/.codex/skills/seoyeon-slack-reporter/SKILL.md` | Use this when operationalizing Slack delivery. |

### 동승 - Backtest Management

| Asset Type | Current Locations | Notes |
|---|---|---|
| Canonical registry rows | `tasks/task_registry.csv` rows owned by `Backtest & Simulation Infra` | Current active rows include Task499, Task501, Task504, Task505, Task508, Task509, Task513, Task517, Task521, Task523, Task553, Task556. |
| Core package | `src/backtest/` | Backtest code is heavily task-scoped. 동승 should avoid mixing research one-offs with reusable replay/cost/simulation contracts. |
| Key modules | `src/backtest/source_truth_continuation_identity.py`, `src/backtest/source_truth_lineage.py`, `src/backtest/build_portfolio_path_equity_curve_simulation_398.py`, `src/backtest/analysis_benchmark_gate_512.py`, `src/backtest/analysis_cost_sensitivity.py` | Core concerns: exact lifecycle identity, deterministic replay, cost/slippage, OOS and overfit checks. |
| Reports | `docs/reports/task_499_regime_intraday_continuation_grid/`, `docs/reports/task_505_two_year_pnl_grid/`, `docs/reports/task_508_cost_stress_validation/`, `docs/reports/task_509_walk_forward_oos_validation/`, `docs/reports/task_512_backtest_correctness_overfit_audit/`, `docs/reports/task_553_portfolio_realism_simulator/` | Current backtest decision trail. |
| Tests | `tests/test_task499_regime_intraday_continuation_grid.py`, `tests/test_task508_511_task505_validation.py`, `tests/test_task512_backtest_correctness_overfit_audit.py`, `tests/test_regime_gated_canonical_continuation_validation_393.py` | Minimum test candidates for backtest changes. |

### 윤헌 - Data Management

| Asset Type | Current Locations | Notes |
|---|---|---|
| Canonical registry rows | `tasks/task_registry.csv` rows owned by `Data & Market Microstructure` | Current canonical row includes Task495; active rows include Task492, Task511, Task514, Task520, Task526, Task546, Task547, Task551, Task560, Task563, Task569. |
| Core package | `src/data/`, `src/market/`, `src/app/nasdaq_market_calendar.py`, `src/app/task_089_market_data_signal_refresh.py` | 윤헌 owns raw/live data readiness, not strategy fitting. |
| Key modules | `src/data/intraday_backfill.py`, `src/data/alpaca_historical_microstructure_export.py`, `src/data/alpaca_stock_stream_archive.py`, `src/data/full_depth_book_archive.py`, `src/data/paper_shadow_microstructure_capture.py` | Current ingestion/capture source modules. |
| Data roots | `data/raw/`, `data/artifacts/`, `trading.db`, `trading_continuation_capture.jsonl` | Raw and derived storage must stay separated and manifest-backed. |
| Reports | `docs/reports/task_495_microstructure_live_source_readiness/`, `docs/reports/task_514_live_source_data_contract/`, `docs/reports/task_590_runtime_market_data_source_unification/` | Current source-readiness and runtime source contracts. |
| Tests | `tests/test_data_quality.py`, `tests/test_task514_live_source_data_contract.py`, `tests/test_task590_runtime_market_data_source_unification.py`, `tests/test_task_337_historical_intraday_backfill.py` | Data changes require schema, timezone, freshness, and provenance validation. |

### 규승 - Frontend/UI

| Asset Type | Current Locations | Notes |
|---|---|---|
| App | `frontend/trader-terminal/` | Mobile-first trader terminal; paper trading is now the default landing surface. |
| Core files | `frontend/trader-terminal/src/App.jsx`, `frontend/trader-terminal/src/ChartBlocks.jsx`, `frontend/trader-terminal/src/styles.css` | 규승 owns UX, responsive layout, route/view organization, and display copy. |
| Catalog contract | `frontend/trader-terminal/public/catalog/trader_terminal_catalog.json`, `frontend/trader-terminal/public/catalog/paper_ops_runtime_catalog.json`, `scripts/build_trader_terminal_catalog.py`, `docs/frontend_data_contract.md` | React must read catalog payloads, not raw task CSVs. |
| Tests | `tests/test_frontend_continuity_contract.py`, `tests/test_task586_frontend_paper_ops_integration.py`, `tests/test_trader_terminal_catalog.py`, `scripts/frontend_continuity_validate.py` | Frontend changes must preserve catalog-backed provenance. |

### 주은 - Execution & Risk

| Asset Type | Current Locations | Notes |
|---|---|---|
| Current operating board | `docs/reports/task_598_paper_week_feedback_operating_plan/`, `docs/reports/task_597_frontend_backend_paper_ops_triage/owner_remediation_plan.csv` | Current first blocker is buy-only lifecycle: 24 BUY fills and 0 SELL fills. |
| Core paper ops reports | `docs/reports/task_585_kis_paper_order_execution/`, `docs/reports/task_588_kis_paper_market_hours_runtime_loop/`, `docs/reports/task_589_nasdaq_paper_ops_hardening/` | Broker truth, runtime loop, EOD PnL, lifecycle events, and open-position proxy evidence. |
| Core code | `src/app/task_589_paper_eod_slack_report.py`, `src/app/task_585_kis_paper_order_execution.py`, `src/app/task_588_kis_paper_market_hours_runtime_loop.py` | Execution changes must keep broker truth separate from local/proxy state. |
| Tests | `tests/test_task589_nasdaq_paper_ops_hardening.py`, `tests/test_task585_kis_paper_order_execution.py` | Minimum checks for paper execution and EOD risk reporting. |

## Dependency Rules

| From | May Depend On | Must Not Depend On |
|---|---|---|
| 필수 / Regime | 윤헌 data contracts, 동승 backtest validation, 성원 intraday evidence, 종찬 chart evidence | Future outcome labels, intraday execution fills, frontend-only fields |
| Intraday | Regime gates, 윤헌 intraday/microstructure sources, 동승 replay | Missing labels as negatives, proximity lifecycle matching |
| Chart | Catalog contracts, strategy evidence tables, frontend UI | Raw task CSV reads from React, chart-only strategy decisions |
| Slack | Report artifacts, runtime audit tables, supervisor status | Slack message success as trade success, LLM-only trading claims |
| Backtest | Exact lifecycle/event data, strategy rules, cost/slippage contracts | Live execution state as backtest truth, same-bar fantasy fills |
| Data | Broker/provider APIs, raw storage rules, source contracts | Strategy target labels, inferred raw sources |
| Project Discipline | All task reports/manifests/registries | Undocumented artifact moves |
| Execution & Risk | Broker truth, market/session status, source freshness, risk limits | Proxy PnL as realized PnL, buy-only evidence as strategy acceptance |

## Operating Rule

When a new task starts, assign:

1. One named lead.
2. One existing canonical team.
3. One reviewer lead or reviewer team.
4. Output path under `docs/reports/<task_id>/`.
5. Artifact manifest if any file is produced.
6. Validation command.

If ownership is unclear, 중훈 resolves the folder/report/registry side first; the strategy or data lead does not silently create a new convention.
