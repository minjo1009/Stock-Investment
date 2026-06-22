# Task1378-1387 Trader Expert Context Development

## Decision Summary

- Verdict: `expert_context_packet_ready_for_review_and_next_implementation`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: prepared a source-backed expert review packet for the next Trader Brain development pass.
- Next action: convert the review packet into implementation tasks for expectation gap, materiality denominator, market absorption, payoff rank, and dynamic exit.

Current diagnostic baseline from Task1358-1377:

| Policy | Final | CAGR | MDD | QQQ Beat | 30pct CAGR |
| --- | ---: | ---: | ---: | ---: | ---: |
| `payoff_core_top5_v1` | 1930.9623 | 13.5987pct | -34.9072pct | yes | no |
| `payoff_core_top10_v1` | 1660.2374 | 10.3219pct | -25.8405pct | no | no |
| `payoff_hurdle_top10_v1` | 1501.3395 | 8.1921pct | -28.7977pct | no | no |

Failure diagnosis:

1. `fresh_expectation_change_proxy` exists on only 112 of 3,100 candidates.
2. `high_payoff_candidate` exists on zero candidates.
3. Source independence is mostly `issuer_plus_market_only`, not analyst/customer/regulator confirmation.
4. `revenue_validation_market_confirmed` is too broad at 2,020 of 3,100 candidates.
5. L5 dynamic exit fired on only 6 of 1,550 replay trades.

## Quant Expert Report

### Expert Panel Roles

Review-only GPT roles to use:

1. Goldman Sachs event-driven PM reviewer.
2. Morgan Stanley single-name fundamental analyst reviewer.
3. JPMorgan quant factor reviewer.
4. BofA earnings revision and estimate reviewer.
5. Citi macro-policy transmission reviewer.
6. UBS risk and drawdown reviewer.
7. Barclays sector strategist reviewer.
8. Deutsche Bank liquidity and crowding reviewer.
9. Citadel tactical trader reviewer.
10. Two Sigma research engineering reviewer.
11. Semiconductor specialist.
12. AI infrastructure specialist.
13. Space/defense specialist.
14. Policy/politics specialist.
15. Macro economist.
16. Backend validation engineer.

GPT/Chrome and subagents are review-only for this packet. They cannot certify raw source truth, PnL validity, strategy acceptance, deployment readiness, or real-capital permission.

### Source Context Gathered

See `source_catalog.csv`.

Primary implementation lessons:

1. Materiality must be denominator-based, not text-presence based.
2. Event impact must be abnormal-return/event-window based, not news-positive based.
3. Surprise must compare actual information to prior expectation.
4. Momentum/market acceptance must use pre-decision and post-event windows with clear timing separation.
5. Macro inputs must use vintage data.
6. Issuer and analyst/guidance information must respect public-disclosure timing.

### Expert Review Questions

Ask each expert to answer:

1. Which current L2 primitive is too broad to trade?
2. Which current bucket should be split first?
3. What exact denominator proves materiality?
4. What exact source proves expectation gap?
5. What market reaction window proves absorption or rejection?
6. What post-entry source receipt should trigger hold, reduce, or exit?
7. What rule would prevent throwing away existing winners?
8. What rule would prevent adding narrative-only traps?
9. What evidence must remain a gap rather than a negative?
10. Which validation invariant catches leakage or overfit?

### Subagent / GPT Expert Audit Summary

Three read-only subagent audit packets were completed.

Trading expert audit:

- Main finding: current L2-L5 is still proxy-based, not a real expectation-change and position-management engine.
- Critical facts: all 3,100 L2 rows are still analyst-gap proxy; 2,850 rows are issuer-plus-market only; dynamic exit fired only 6 times.
- Requirement: add PIT expectation, customer/demand confirmation, policy affected-entity mapping, payoff convexity, and source-receipt exit logic.

Source/data audit:

- Main finding: PIT analyst/estimate data is priority one.
- Required fields: estimate timestamp, consensus snapshot, revision delta, guidance value, contract value, counterparty, policy affected entity, relative-volume and relative-return windows.
- Rule: missing analyst/customer/policy data must remain `source_gap`, never negative evidence.

Backend/quant implementation audit:

- Main finding: build sidecar panels first, not a new model.
- Required artifacts: PIT expectation panel, materiality denominator panel, market absorption panel, L3 absorption mechanism edges, dynamic exit receipt panel, invariant ledger, overfit/leakage guard.
- Rule: denominator gaps cannot increase score; market absorption must be timestamp-separated; OOS remains score-only.

### Proposed Task1378-1387 Program

Task1378: Expert context and source packet.

- Output: expert roles, source catalog, review questions.
- Status: this report.

Task1379: Expectation gap schema.

- Add fields: `prior_expectation_type`, `prior_expectation_value`, `new_information_value`, `expectation_delta`, `expectation_gap_state`, `expectation_source_family`, `expectation_available_to_brain_ts`.
- Rule: no estimate/guidance/consensus proxy can enter without as-of timestamp.

Task1380: Estimate/guidance proxy extractor.

- Start with public, project-available sources: SEC 8-K/10-Q/10-K guidance language, press release exhibits, earnings presentation exhibits.
- Keep licensed analyst PIT feed as explicit gap if unavailable.

Task1381: Materiality denominator schema.

- Add fields: `event_value`, `revenue_denominator`, `market_cap_denominator`, `backlog_denominator`, `cash_flow_denominator`, `materiality_ratio`, `materiality_denominator_quality`.
- Rule: text-only materiality is capped.

Task1382: Contract/order/customer confirmation splitter.

- Split issuer claim, customer confirmed, regulator confirmed, analyst confirmed, and market confirmed.
- Rule: issuer claim plus price existence is not independent confirmation.

Task1383: Market absorption panel.

- Add event-window fields: 1d, 5d, 20d relative return versus QQQ and sector proxy; volume spike; gap retention; drawdown after event.
- Rule: post-event price can inform absorption/exit but cannot rank before event receipt.

Task1384: L3 mechanism upgrade.

- Replace generic supports edges with causal primitives:
  - `expectation_gap_creates_repricing_room`
  - `material_contract_scales_revenue_base`
  - `market_absorption_confirms_underreaction`
  - `price_rejection_invalidates_catalyst`
  - `issuer_only_claim_caps_conviction`

Task1385: L4 payoff ranker redesign.

- Rank formula must separate:
  - upside magnitude
  - expectation gap
  - source independence
  - market absorption
  - downside invalidation
  - winner preservation hurdle
- Rule: no future return, PnL, or outcome-derived labels in assignment.

Task1386: L5 dynamic exit expansion.

- Exit receipts:
  - guidance cut
  - earnings disappointment
  - market rejection after event
  - dilution/offering
  - delisting/going-concern
  - catalyst expiry
  - thesis confirmation for hold extension

Task1387: Controlled replay and audit gate.

- Replay only pre-registered policy variants.
- Required outputs: trades, equity, metrics, replacement pair audit, OOS split table, overfit ledger, acceptance gate.
- Gate remains diagnostic unless 30pct CAGR, MDD near -30pct, QQQ beat, split/OOS, cost/slippage, source audit, and no leakage all pass.

## No-Background Decision-Maker Report

The next upgrade is not "add more news."

The next upgrade is to make the brain ask:

1. Was the information actually new versus expectation?
2. Was it big enough versus company size?
3. Did the market accept it or reject it?
4. Should the position be held, cut, or extended after new source receipts?

This packet is ready for GPT/expert critique and then implementation.

## Artifact Manifest

Inputs:

- `docs/operating_system/project_operating_state.md`
- `docs/reports/task_1358_1377_trader_judgment_core_recovery/task_1358_1377_trader_judgment_core_recovery.md`
- `data/artifacts/task_1358_1377_trader_judgment_core_recovery/task1370_replay_metrics.csv`
- external source catalog in `source_catalog.csv`

Outputs:

- `docs/reports/task_1378_1387_trader_expert_context_development/task_1378_1387_trader_expert_context_development.md`
- `docs/reports/task_1378_1387_trader_expert_context_development/source_catalog.csv`

Validation commands:

- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
