# Task689 Interpretation and Edge Quality

## Decision Summary

- Verdict: INTERPRETATION_EDGE_QUALITY_PANELS_BUILT_NO_TRADING_PROMOTION.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidates 1621, interpretation quality rows 9726, edge quality rows 9726, sector families 6, weakest-layer states 5.
- What changed: economic interpretation quality and sector-specific edge quality are now explicit panels.
- Next action: Upgrade weakest interpretation and edge layers, then review candidate examples before allocation backtest.

## Quant Expert Report

### Data source and source readiness

Inputs are Task684 interaction stack and Task688 five-layer object contracts. This task does not add raw sources and does not infer lifecycle matches.

### Exact join keys

- `lifecycle_id` joins Task688 interpretation, edge, bundle, and slot objects to Task684 candidate context.
- `theme_id` maps candidates into sector families for sector-specific edge rules.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included in the quality outputs.
- All quality outputs set outcome/future/label flags to zero.
- This task runs no return test and promotes no trading rule.

### Economic interpretation quality

| primary_driver | interpretation_quality_tier | row_count |
| --- | --- | --- |
| company_catalyst | medium | 719 |
| company_catalyst | strong | 39 |
| company_catalyst | weak | 863 |
| macro_context | proxy_only | 1621 |
| market_context | proxy_only | 1621 |
| portfolio_capacity | proxy_only | 1621 |
| price_acceptance | proxy_only | 1621 |
| theme_leadership | medium | 1047 |
| theme_leadership | proxy_only | 574 |

### Sector edge rulebook

| sector_family | economic_transmission_priority | positive_edge_requirements | blocker_edge_conditions | sizing_modifier_conditions | current_gap |
| --- | --- | --- | --- | --- | --- |
| semis_ai_infrastructure | demand_cycle\|capex_cycle\|supply_chain\|duration_liquidity | contract_or_supply_demand plus price_acceptance plus theme_leadership | demand_fade\|duration_pressure\|liquidity_pressure\|late_extension_without_absorption | high_volatility_or_late_extension requires reduced slot claim | No order-size, backlog-conversion, hyperscaler capex revision, or inventory-cycle bridge. |
| defense_space_policy | policy_budget\|contract_visibility\|funding_risk\|duration_risk | named_customer_or_budget visibility plus price_acceptance | funding_stress\|policy_headline_fade\|contract_size_unknown\|space_financing_risk | binary_contract_or_funding_dependent names require smaller initial claim | Contract value, funded backlog, award protest risk, and dilution runway are mostly proxy-only. |
| biotech_healthcare | clinical_regulatory\|reimbursement\|cash_runway\|event_binary_risk | regulatory/clinical catalyst must be direct and price accepted | binary_event\|cash_runway_pressure\|regulatory_uncertainty\|no_follow_through | event-binary and funding-sensitive candidates need cap-limited role | Trial phase, endpoint quality, FDA calendar, and cash runway are not fully modeled. |
| financials_credit | rates_path\|credit_cycle\|curve\|deposit_beta\|capital_return | credit_support or rate_margin_support plus price_acceptance | credit_pressure\|yield_curve_conflict\|liquidity_stress\|regulatory_capital_risk | credit stress and rate conflict reduce slot claim | Curve, spread, deposit, and credit-quality details are still coarse. |
| energy_commodities | oil_price\|supply_demand\|inventory\|geopolitics\|capex_discipline | oil_support or supply_demand plus price_acceptance | oil_pressure\|demand_fade\|cost_inflation\|geopolitical_fade | commodity reversal risk requires confirmation or reduced size | Commodity curve, inventory surprise, and realized spread bridge are missing. |
| industrials_capex | capex_cycle\|backlog\|margin\|policy\|global_demand | backlog/order or capex demand support plus price_acceptance | capex_demand_pressure\|energy_input_cost\|dollar_pressure\|late_cycle_order_fade | extended price with unclear backlog conversion needs confirmation | Backlog conversion, margin bridge, and customer capex budget quality are mostly proxy-only. |
| consumer_platform | demand_elasticity\|margin\|ad_spend\|subscription_retention\|rates | guidance/margin or demand signal plus price_acceptance | demand_slowdown\|margin_pressure\|consumer_credit_pressure\|competition | weak demand or margin uncertainty limits slot priority | Unit economics, cohort retention, and spend revisions are not deeply modeled. |
| general_growth | revenue_growth\|margin\|duration\|liquidity\|theme_flow | durable catalyst plus price_acceptance plus non-hostile market context | duration_pressure\|liquidity_pressure\|no_price_acceptance\|single_weak_source | uncertain catalyst or crowded relation lowers replacement claim | Sector-specific economics are under-specified; this row is fallback only. |

### Edge quality sample summary

| sector_family | refined_edge_type | edge_quality_tier | row_count |
| --- | --- | --- | --- |
| biotech_healthcare | confirmation_required | medium | 229 |
| biotech_healthcare | confirmation_required | weak | 3 |
| biotech_healthcare | diagnostic_context | proxy_only | 100 |
| biotech_healthcare | offsetting | medium | 49 |
| biotech_healthcare | reinforcing | strong | 123 |
| biotech_healthcare | reinforcing_negative | medium | 10 |
| biotech_healthcare | sizing_modifier | strong | 86 |
| defense_space_policy | confirmation_required | medium | 526 |
| defense_space_policy | confirmation_required | weak | 8 |
| defense_space_policy | diagnostic_context | proxy_only | 213 |
| defense_space_policy | offsetting | medium | 49 |
| defense_space_policy | reinforcing | strong | 295 |
| defense_space_policy | reinforcing_negative | medium | 20 |
| defense_space_policy | sizing_modifier | strong | 167 |
| financials_credit | blocker | medium | 15 |
| financials_credit | blocker | weak | 25 |
| financials_credit | confirmation_required | medium | 332 |
| financials_credit | confirmation_required | weak | 2 |
| financials_credit | diagnostic_context | proxy_only | 143 |
| financials_credit | offsetting | medium | 29 |
| financials_credit | reinforcing | strong | 178 |
| financials_credit | reinforcing_negative | medium | 3 |
| financials_credit | sizing_modifier | strong | 131 |
| general_growth | blocker | medium | 45 |
| general_growth | blocker | weak | 215 |
| general_growth | confirmation_required | medium | 954 |
| general_growth | confirmation_required | weak | 197 |
| general_growth | diagnostic_context | proxy_only | 621 |
| general_growth | offsetting | medium | 142 |
| general_growth | offsetting | weak | 11 |
| general_growth | reinforcing | medium | 336 |
| general_growth | reinforcing | strong | 678 |
| general_growth | reinforcing_negative | medium | 20 |
| general_growth | reinforcing_negative | weak | 1 |
| general_growth | sizing_modifier | medium | 58 |
| general_growth | sizing_modifier | strong | 448 |
| industrials_capex | blocker | medium | 9 |
| industrials_capex | blocker | weak | 21 |
| industrials_capex | confirmation_required | medium | 353 |
| industrials_capex | confirmation_required | weak | 11 |
| industrials_capex | diagnostic_context | proxy_only | 196 |
| industrials_capex | offsetting | medium | 68 |
| industrials_capex | reinforcing | medium | 88 |
| industrials_capex | reinforcing | strong | 265 |
| industrials_capex | reinforcing_negative | medium | 1 |
| industrials_capex | sizing_modifier | strong | 164 |
| semis_ai_infrastructure | blocker | medium | 51 |
| semis_ai_infrastructure | blocker | weak | 59 |
| semis_ai_infrastructure | confirmation_required | medium | 657 |
| semis_ai_infrastructure | diagnostic_context | proxy_only | 348 |
| semis_ai_infrastructure | offsetting | medium | 75 |
| semis_ai_infrastructure | reinforcing | medium | 118 |
| semis_ai_infrastructure | reinforcing | strong | 444 |
| semis_ai_infrastructure | reinforcing_negative | medium | 16 |
| semis_ai_infrastructure | sizing_modifier | strong | 320 |

### Candidate weakest-layer decomposition

| weakest_layer | candidate_count |
| --- | --- |
| economic_interpretation_weak | 73 |
| economic_priced_in_gap | 51 |
| relation_edge_weak | 110 |
| sector_edge_blocker | 88 |
| slot_replacement_hurdle | 1299 |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Company catalyst interpretation is still often proxy-only where contract value, named customer quality, margin bridge, and expectation surprise are absent.
- Sector edges are now explicit, but they still depend on existing proxy fields.
- Macro remains diagnostic-only; it is not promoted into slot authority.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Add source-text extraction for contract value, customer quality, repeatability, margin impact, and expectation surprise.
- Upgrade sector-specific edge thresholds from template logic to validated candidate-review logic.
- Only after quality panels are reviewed should allocation/backtest change.

## No-Background Decision-Maker Report

- What happened: candidates are now split by where the reasoning is weak.
- Why it matters: we can fix the weak layer first instead of tuning after seeing returns.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect examples from each weak layer and improve the source interpretation or edge rule.

## Artifact Manifest

- Inputs: Task684 interaction stack, Task688 interpretation/edge/bundle/slot objects.
- Outputs: sector edge rulebook, interpretation quality panel, edge quality panel, weak-layer audit, integrity audit, decision, pass/fail, manifest.
- Row counts: rulebook 8, interpretation quality 9726, edge quality 9726, weak layer 1621.
- Validation commands: `python src/backtest/build_task689_interpretation_edge_quality.py`; `python -m unittest tests.test_task689_interpretation_edge_quality`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| quality_panels_present | PRIMARY_PASS | 1 | interpretation_quality=9726; edge_quality=9726; weak_layer=1621 | interpretation, edge, and weak-layer panels must have rows |
| weak_layer_one_row_per_candidate | PRIMARY_PASS | 1 | rows=1621; unique_lifecycle=1621 | one weak-layer audit row per lifecycle |
| sector_specific_edge_rules_present | PRIMARY_PASS | 1 | sector_families=6 | multiple sector families must be handled |
| weak_layers_are_not_all_same | PRIMARY_PASS | 1 | weakest_layer_count=5 | weakest layer should decompose candidates into multiple failure modes |
| no_outcome_columns_in_quality_outputs | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded |
| macro_still_not_promoted | PRIMARY_PASS | 1 | macro eligible edge sum=0 | macro diagnostic-only edge cannot become slot authority |
