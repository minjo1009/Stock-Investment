# Task1598-1617 Expectation-Payoff-Re-risk Plan

## Decision Summary

- Verdict: `expectation_payoff_rerisk_plan_ready_for_implementation`.
- Goal: break the MDD/CAGR loop by adding a bridge from tradable surprise to payoff window to re-risk decision.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Expert review conclusions:
- `event_driven_pm`: adopt - The next bridge must start with tradable surprise, not positive news.
- `earnings_revision_analyst`: adopt_with_gap - PIT analyst/estimate revision is the correct input; proxy surprise must remain separately labeled.
- `factor_quant`: adopt - Market absorption must be abnormal return versus QQQ/theme/factor context, not raw return.
- `risk_pm`: modify - Re-risk must be staged; never jump from reduce to full size without source and absorption confirmation.
- `sector_semiconductor_expert`: adopt - Payoff window needs customer/design win/volume shipment/revenue timing fields.
- `sector_ai_software_expert`: adopt - Payoff requires ARR/RPO/paid conversion and margin context, not AI language.
- `sector_space_power_expert`: adopt - Awards and policy catalysts need obligated funding, milestone, COD/service revenue timing.
- `backend_engineer`: adopt - Schema must preserve source-time and outcome-audit boundaries before any replay.
- `validation_engineer`: adopt - Freeze one policy family and run split/OOS and cost/slippage after bridge implementation.
- `governance_reviewer`: adopt - GPT review is critique only; no acceptance, deployment, or capital status change.

Learning/source map:
- `SEC Form 8-K` -> material_event: Use event item, materiality, filing/receipt time, and exhibit context. Source: https://www.sec.gov/files/form8-k.pdf
- `MacKinlay Event Studies` -> abnormal_return: Use event-window abnormal return logic; raw price move is insufficient. Source: https://www.bu.edu/econ/files/2011/01/MacKinlay-1996-Event-Studies-in-Economics-and-Finance.pdf
- `AQR Value and Momentum Everywhere` -> momentum_factor_context: Use momentum/factor context to distinguish market acceptance from beta/factor drift. Source: https://www.aqr.com/Insights/Datasets/Value-and-Momentum-Everywhere-Factors-Monthly
- `Fama-French Data Library` -> factor_context: Use factor context for market/size/value/profitability/investment normalization. Source: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
- `ALFRED` -> macro_vintage: Macro/regime data must be vintage/as-of available at decision time. Source: https://alfred.stlouisfed.org/
- `Task1578-1597 Audit` -> local_gap_source: Current local evidence: analyst PIT 0/3100, true surprise 77/3100, sustained absorption 190/3100. Source: data/artifacts/task_1578_1597_l0_l5_professional_logic_audit
- `Task1468-1487 Complete Contract` -> local_contract: Use existing criteria for source-time, event family, expectation, absorption, mechanism, thesis, validation. Source: data/artifacts/task_1468_1487_complete_implementation_contract

Implementation plan:

| Task | Title | Detail | Success Check | Guardrail |
| --- | --- | --- | --- | --- |
| Task1598 | Expert Review Packet | Create role-based critique packet | expert_review_rows_ready | No code or replay. |
| Task1599 | Learning Source Map | Map professional sources to bridge requirements | source_contract_ready | Sources guide logic; sources do not certify strategy. |
| Task1600 | Data Availability Contract | Classify each required input as available, proxy-only, licensed-gap, or blocked | no_missing_as_negative | Analyst PIT missing must not become zero surprise. |
| Task1601 | Tradable Surprise Schema | Define prior baseline, surprise direction, magnitude, quality tier, and source family | good_words_separated_from_surprise | Positive wording cannot score as true surprise. |
| Task1602 | Payoff Window Schema | Define event value, denominator, revenue timing, margin, dilution, cash runway, and window bucket | payoff_window_fields_ready | No payoff without source-time denominator. |
| Task1603 | Absorption Quality Schema | Define abnormal return, QQQ/theme/factor relative strength, volume quality, reversal, persistence | raw_return_not_absorption | Post-entry outcomes cannot feed L2/L4 assignment. |
| Task1604 | L3 Payoff Mechanism Graph | Convert semantic edges into event->payoff->expectation->absorption->risk edges | edge_has_economic_path | Generic supports/weakens is insufficient. |
| Task1605 | L4 Payoff Thesis Card | Add alpha_left, payoff_window, invalidation_trigger, rerisk_trigger, expiry | thesis_card_actionable | Rank score alone is not a thesis. |
| Task1606 | L5 Re-risk State Machine | Define reduce->watch->confirm->partial_rerisk->full_hold/add-on or exit | state_machine_ready | No direct reduce-to-full-size jump. |
| Task1607 | Re-risk Sizing Guard | Define staged allocation increments and max exposure caps by thesis quality | sizing_cap_preserved | No leverage or blanket full-size release. |
| Task1608 | Source Confirmation Gate | Require fresh source receipt or independent confirmation before re-risk | source_confirmed_rerisk_only | Price bounce alone cannot re-risk. |
| Task1609 | Absorption Recovery Gate | Require sustained relative strength and no full reversal before re-risk | absorption_recovery_required | One-day bounce is not recovery. |
| Task1610 | Payoff Still Open Gate | Block re-risk when payoff window expired or thesis already realized | expired_thesis_no_rerisk | No stale winner reentry. |
| Task1611 | Negative Fixture Suite | Build fixtures for good-words-only, price-bounce-only, expired payoff, dilution, missing analyst PIT | false_rerisk_blocked | Missing labels are not negatives. |
| Task1612 | Preregistered Replay Family | Freeze top3/top5 variants before replay: no-rerisk baseline, partial-rerisk, source+absorption rerisk | policy_hash_frozen | No post-result tuning. |
| Task1613 | Split/OOS Plan | Define in-sample/OOS windows and cost/slippage stress | validation_plan_ready | Single interval cannot accept strategy. |
| Task1614 | Implementation Worker Packet | Assign disjoint code/report/artifact scopes for implementation | worker_scopes_disjoint | Subagents cannot decide acceptance. |
| Task1615 | Bridge Validator | Validate schemas, flags, no outcome assignment, source-time, status preservation | validator_ready | PASS != acceptance. |
| Task1616 | Decision Report | Report done/failed/next with exact metrics after implementation | report_contract_ready | No deployment claim. |
| Task1617 | Closeout Gate | Decide whether bridge improved CAGR toward 30 while MDD remains within -30 vicinity | diagnostic_closeout_only | Real capital remains forbidden. |

Core schema fields:

| Table | Field | Type | Definition |
| --- | --- | --- | --- |
| tradable_surprise | `candidate_source_id` | string | join key |
| tradable_surprise | `prior_baseline_type` | enum | analyst_estimate|company_guidance|explicit_prior_source|proxy_only|missing |
| tradable_surprise | `surprise_direction` | enum | positive|negative|mixed|none|unknown |
| tradable_surprise | `surprise_quality` | enum | true_pit|explicit_guidance_change|proxy|good_words_only|gap |
| tradable_surprise | `tradable_surprise_score` | float | 0 unless true_pit or explicit guidance/proxy passes guard |
| payoff_window | `payoff_mechanism` | enum | revenue|margin|cash_runway|dilution|policy_budget|customer_validation |
| payoff_window | `payoff_window_bucket` | enum | 0_30d|31_90d|91_180d|181d_plus|expired|unknown |
| payoff_window | `denominator_quality` | enum | verified|proxy|gap |
| absorption_quality | `abnormal_return_window` | float | event-window return minus QQQ/theme/factor context |
| absorption_quality | `persistence_state` | enum | persistent|reversed|neutral|gap |
| rerisk_state | `position_state` | enum | hold|reduce|watch|partial_rerisk|full_hold|exit|no_reentry |
| rerisk_state | `rerisk_allowed` | int | 1 only if source confirmation + absorption recovery + payoff still open |

## No-Background Decision-Maker Report

1. 다음 작업은 새 필터가 아닙니다.
2. 좋은 정보가 진짜 돈 되는 기회인지 판단하는 다리를 만드는 작업입니다.
3. 핵심은 `기대 대비 충격 -> payoff 기간/크기 -> 다시 키울지`입니다.
4. 줄인 포지션을 아무 때나 다시 키우지 않습니다.
5. source 확인, 시장 흡수 회복, payoff 남음이 동시에 필요합니다.
6. 이 계획 자체는 전략 승인이 아닙니다.

## Artifact Manifest

- `task1598_expert_review_packet.csv`
- `task1599_learning_source_map.csv`
- `task1600_1606_bridge_schema.csv`
- `task1598_1617_implementation_plan.csv`
- `task1617_acceptance_gate.csv`
- `task1617_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1598_1617_expectation_payoff_rerisk_plan_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```