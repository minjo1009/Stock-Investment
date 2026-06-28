# Professional Quant Trading Team Charter

Last updated: 2026-06-06

## Purpose

This repository is managed as a professional quant trading research and execution monorepo. The core rule is simple: every result must be traceable to exact data, exact lifecycle identity, and a named owner team.

For current paper-trading operations, read `docs/ownership/current_operating_model.md` first. Older task reports and Graphify outputs are historical unless that file names them as current sources.

## Teams

| Team | Primary Ownership | Review Focus |
|---|---|---|
| Data & Market Microstructure | Raw market data, Alpaca/SIP streams, quotes, status/LULD, depth contracts | Source availability, receive timestamps, no fake microstructure |
| Regime Research | Multi-day market and theme regime models | Forward-live regime detectability, train/OOS separation |
| Intraday Continuation Research | Intraday continuation archetypes, ADD/SCALE/REDUCE state analysis | Entry-safe factors, continuation false positives |
| Backtest & Simulation Infra | Canonical lifecycle engine, grid backtests, cost/slippage simulation | Determinism, split integrity, reproducible metrics |
| Execution & Risk | Order lifecycle, risk gates, live readiness | Trading constraints, status handling, deployment blockers |
| Research Governance | Task registry, report standard, artifact policy, review discipline | Acceptance status, archival, no untracked decisions |

## Named Leads

| Lead | Module | Canonical Team | Primary Responsibility |
|---|---|---|---|
| 필수 (=Regime) | Strategy: Regime / Overall Strategy Lead | Regime Research | Overall strategy direction, multi-day market/theme regime gates, theme universe contracts, regime feature readiness |
| 성원 | Strategy: Intraday | Intraday Continuation Research | Intraday continuation archetypes, VWAP/entry-safe state, false-positive decomposition |
| 종찬 | Strategy: Chart | Intraday Continuation Research | Chart-derived strategy evidence, OHLC/VWAP entry context, indicator/regime/intraday visualization contract |
| 중훈 | Project Discipline | Research Governance | Folder discipline, task registry, artifact manifests, report standard, archive/migration rules |
| 서연 | Slack Reporting | Research Governance | Slack trade notifications, EOD report delivery, duplicate-send guards, supervisor failure alerts |
| 동승 | Backtest Management | Backtest & Simulation Infra | Deterministic replay, walk-forward/OOS, cost/slippage, portfolio simulation and reproducible metrics |
| 윤헌 | Data Management | Data & Market Microstructure | Raw/live data contracts, market calendar, microstructure capture, source provenance and freshness |
| 규승 | Frontend/UI | Research Governance | Trader terminal UI, mobile-first paper trading views, frontend catalog contract |
| 주은 | Execution & Risk | Execution & Risk | Exit/trim/stop lifecycle, broker-truth reconciliation, exposure limits, kill-switch and risk reporting |

The current paper-week operating board is maintained in `docs/ownership/current_operating_model.md`. The detailed file and artifact map for these leads is maintained in `docs/ownership/module_ownership_map.md`.

## Current Paper-Ops Standing

| Decision Surface | Current State |
|---|---|
| Canonical acceptance program | Task599 / `docs/ownership/readiness_registry.yaml` |
| Canonical operating board | `docs/ownership/current_operating_model.md` |
| Current feedback remediation board | Task604 / `docs/reports/task_604_three_day_feedback_remediation_plan/` |
| Paper operation | `READY_FOR_CONTROLLED_PAPER_RUN` |
| Strategy acceptance | `NOT_ACCEPTED` |
| Strategy target gate | `ACCEPTANCE_REVIEW` |
| Deployment readiness | `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` |
| First blocker | Buy-only lifecycle: exit/trim/stop evidence missing |
| First owner | 주은 / Execution & Risk |
| Overall gate owner | 필수 |

## Non-Negotiable Rules

- No inferred lifecycle matching.
- No symbol/date/price/time proximity fallback.
- Missing labels are never negatives.
- Missing raw sources are reported, not approximated.
- Strategy claims require split/OOS, leakage, and cost/slippage evidence.
- Deployment claims require live-source readiness, not only historical diagnostics.

## Review Model

Every task has one owner team and at least one reviewer team. Data-source changes require Data & Market Microstructure review. Strategy metric changes require Research Governance review. Execution readiness changes require Execution & Risk review.

## Daily Feedback Remediation

The current daily-feedback remediation board is Task604. Team leads must use `docs/reports/task_604_three_day_feedback_remediation_plan/team_remediation_board.csv` before claiming progress from daily feedback.

Daily feedback is complete only when each open blocker is either changed with artifact and validation evidence or explicitly unchanged with reason, blocker age, and next validation run. Slack delivery, UI polish, concentration improvement, or paper runtime freshness does not change strategy acceptance by itself.

## Current Canonical Research Path

| Layer | Current Canonical Task |
|---|---|
| Multi-day market/theme regime | Task489 |
| Intraday continuation OHLCV/VWAP grid | Task491 |
| Historical microstructure quote layer | Task492 |
| Microstructure-enhanced continuation grid | Task493 |
| Live microstructure source readiness | Task495 |

## Graphify Use

Graphify outputs are discovery aids only. The current Graphify context packs were generated on 2026-04-25 and do not include the latest paper-ops governance work. Do not use Graphify to infer current ownership, active blockers, or readiness until it is regenerated.
