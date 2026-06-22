# Task687 Information Ontology Logic Audit

## Decision Summary

- Verdict: INFORMATION_ONTOLOGY_LOGIC_AUDIT_COMPLETE_NOT_FIRM_GRADE_YET.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: information groups 9, high-severity logic gaps 5, macro status `diagnostic_only`, relation status `partial_not_full_context_graph`.
- What changed: no trading rule changed; this task audits what information exists, where it overlaps, and why current usage is not firm-grade relational logic yet.
- Next action: Build explicit evidence-object -> economic-interpretation -> state-graph-edge contracts before another allocation rule.

## Quant Expert Report

### Data source and source readiness

The project has usable chart, theme, market, company-source, content-interpretation, catalyst, relation, and portfolio-slot fields. Macro is available but diagnostic-only. Microstructure raw data exists separately but is not used in this stack.

| information_group | plain_name | assignment_status | quality_grade | configured_column_count | present_column_count | row_count | all_required_present_row_count | any_present_row_count | coverage_rate_pct | main_gap | example_columns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chart_price_volume | chart_price_volume | assignment_certified | A- | 21 | 21 | 1621 | 1621 | 1621 | 100.0000 | Chart is quantified, but price acceptance is still rule-threshold based rather than microstructure-confirmed. | open\|high\|low\|close\|volume\|vwap\|ret_5d_prev_x\|ret_20d_prev_x\|ma20_prev\|ma50_prev\|high20_prev\|high60_prev |
| theme_market_leadership | theme_market_leadership | assignment_certified | B+ | 15 | 15 | 1621 | 1621 | 1621 | 100.0000 | Leadership is mostly static state; rotation path and capital-flow transition are shallow. | theme_id\|theme_ret20_prev\|theme_breadth20_prev\|theme_volume_ratio_prev\|theme_rank_prev\|theme_regime_state_v4\|broad_market_score\|broad_market_stress\|breadth_20d\|market_ret_20d\|liquidity_ratio\|multi_day_market_state_v4 |
| company_source_event_presence | company_news_event_presence | company_source_certified | B | 12 | 12 | 1621 | 1621 | 1621 | 100.0000 | Presence and certification are good, but direct economic linkage quality still varies. | political_statement_pre7d_count\|geopolitical_event_pre7d_count\|institution_ownership_pre30d_count\|activist_13d_pre30d_flag\|passive_13g_pre30d_flag\|insider_form4_or_144_pre30d_flag\|ceo_ir_proxy_pre14d_count\|linked_event_count\|source_text_certified_event_count\|content_prediction_certified_event_count\|temporal_source_event_density\|temporal_source_time_gap_count |
| content_positive_negative_interpretation | positive_negative_content_interpretation | content_prediction_certified | B- | 22 | 22 | 1621 | 1621 | 1621 | 100.0000 | Interpretation is richer than presence, but still mostly keyword/count taxonomy, not full economic magnitude/counterparty/expectations analysis. | content_direct_bullish_count\|content_direct_bearish_count\|content_contract_revenue_count\|content_guidance_margin_count\|content_supply_demand_count\|content_regulatory_policy_count\|content_insider_buy_count\|content_insider_sell_count\|negative_dilution_financing_count\|negative_regulation_sanction_tariff_count\|negative_ceo_ir_disappointment_count\|negative_insider_sell_count |
| company_catalyst_quality | company_catalyst_quality | derived_from_certified_content | B- | 14 | 14 | 1621 | 1621 | 1621 | 100.0000 | Catalyst quality reuses content interpretation; it does not yet estimate dollar magnitude, margin bridge, backlog conversion, or expectation surprise robustly. | catalyst_quality_score\|catalyst_quality_tier\|company_catalyst_state\|catalyst_path_type\|catalyst_economic_quality\|catalyst_durability\|catalyst_directness\|catalyst_surprise_proxy\|catalyst_negative_overhang\|catalyst_signal_density\|catalyst_priced_in_state\|catalyst_absorption_state |
| macro_context | macro_context | diagnostic_only | C | 14 | 14 | 1621 | 1621 | 1621 | 100.0000 | Macro is fetched and attached, but latest-vintage/repaired release timing blocks assignment use. | macro_series_available_count\|macro_employment_state\|macro_inflation_state\|macro_rates_state\|macro_dollar_state\|macro_oil_state\|macro_credit_state\|macro_liquidity_state\|macro_overall_state\|macro_action_modifier\|macro_release_timestamp_repaired_flag\|macro_asof_provisional_for_diagnostic_flag |
| relation_engine | relation_engine | partial_assignment_certified | C+ | 17 | 17 | 1621 | 1621 | 1621 | 100.0000 | This is still a handcrafted transmission template, not a full state graph across chart/theme/company/macro/news. | rates_exposure\|oil_exposure\|dollar_exposure\|credit_exposure\|liquidity_exposure\|capital_intensity\|funding_sensitivity\|duration_sensitivity\|energy_sensitivity\|capex_demand_sensitivity\|policy_sensitivity\|liquidity_sensitivity |
| portfolio_slot_capacity | portfolio_slot_capacity | assignment_certified | B- | 11 | 4 | 1621 | 1621 | 1621 | 100.0000 | Capacity is cohort-aware, but replacement value and opportunity cost are not yet firm-grade. | same_entry_candidate_count\|same_entry_theme_count\|same_entry_relation_count\|portfolio_capacity_state |
| microstructure | microstructure | not_used_pending_raw_feature_builder | raw_pending | 3 | 3 | 1621 | 1621 | 1621 | 100.0000 | Raw quote/trade folders exist, but current five-engine stack does not use them. | microstructure_state\|microstructure_state_v4\|microstructure_used_in_assignment |

### Exact join keys

- Current candidate-level surfaces are keyed by `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`.
- This audit creates no new inferred lifecycle match.

### Leakage audit

- No return, label, or future price is used to define the audit categories.
- The audit is diagnostic only.

### Overlap audit

| overlap_id | overlapping_groups | what_overlaps | risk | needed_fix |
| --- | --- | --- | --- | --- |
| content_to_catalyst | content_positive_negative_interpretation -> company_catalyst_quality | Contract, backlog, guidance, margin, supply-demand counts are reused as catalyst score/path/quality. | Same evidence can be double-counted as both news quality and catalyst quality. | Separate raw evidence, interpreted economic content, and derived catalyst state with explicit dependency lineage. |
| catalyst_to_relation | company_catalyst_quality -> relation_engine | Catalyst quality and price acceptance feed mechanism_relation_state. | Relation engine can appear multi-dimensional while mostly repackaging catalyst/price states. | Relation state must expose which edges are company-only, macro-dependent, or price-confirmed. |
| theme_to_leadership_to_slot | theme_market_leadership -> portfolio_slot_capacity | Theme rank/breadth and same-entry theme counts both affect selection pressure. | A strong theme can be rewarded by leadership and penalized by concentration without a capital-flow explanation. | Add flow-regime interpretation: leadership expansion, crowding, rotation-out, defensive rotation. |
| macro_to_market_to_relation | macro_context -> theme_market_leadership -> relation_engine | Macro states, broad market score, liquidity ratio, and relation pressure/support all describe regime. | Macro is diagnostic-only but still appears semantically inside relation labels. | Keep macro-derived relation edges blocked unless macro certification or macro-excluded relation path is explicit. |
| price_to_catalyst_absorption | chart_price_volume -> company_catalyst_quality | Price acceptance is used to infer catalyst absorption. | Good price action can be mistaken for good fundamental interpretation. | Separate 'market accepted the story' from 'story has high economic value'. |

### Logic gap audit

| logic_layer | current_state | firm_grade_gap | severity | result_leakage_risk |
| --- | --- | --- | --- | --- |
| raw_source_layer | company/content/theme-price certified rows=1621/1621; macro certified=0 | Raw source certification is improved, but original text evidence and economic extraction are not fully lineage-separated in the final stack. | medium | low |
| content_interpretation_layer | positive_contract_customer_count_nonzero=736; positive_guidance_up_count_nonzero=123; negative_dilution_financing_count_nonzero=92; negative_earnings_margin_damage_count_nonzero=12 | Interpretation buckets lack contract size, customer quality, recurring revenue, margin bridge, expectation delta, and priced-in analysis. | high | low |
| catalyst_quality_layer | low=987; high=606; medium=28 | Catalyst quality is a derivative of content counts; it is not a full economic materiality model. | high | low |
| relation_engine_layer | company_positive_confirmation_needed=560; relation_reinforcing=463; company_price_confirmed_macro_secondary=400; relation_sparse_research_only=156; relation_offsetting=42 | Relation engine is not yet a graph of conditional edges across macro, theme, company, price, and portfolio; it is mostly rule labels. | high | low |
| interaction_layer | price_led_continuation_context=847; catalyst_repricing_context=382; relation_led_continuation_context=247; late_extension_context=73; theme_rotation_context=35; true_unclear_or_low_clarity_context=14; theme_led_continuation_context=12; conflicted_but_alive_context=11 | Interaction exists, but still ranks predefined labels rather than resolving causal conflicts and prerequisites. | high | medium_if_retuned_by_outcome |
| slot_allocation_layer | guarded challenger accepted count remains 0 after source repair | Slot logic lacks ex-ante replacement value, opportunity cost, and incumbent vulnerability model. | high | medium_if_tuned_on_winners |

### Relation engine scope audit

| relation_component | current_inputs | current_method | coverage | firm_grade_gap |
| --- | --- | --- | --- | --- |
| industry_exposure_template | capital_intensity\|funding_sensitivity\|duration_sensitivity\|energy_sensitivity\|capex_demand_sensitivity\|policy_sensitivity\|liquidity_sensitivity | manual template by theme_id | rows=1621 | Static template; not updated by company business mix, balance sheet, or changing macro regime. |
| macro_driver_pressure_support | rates\|oil\|dollar\|credit\|liquidity states and exposures | support_count vs pressure_count | macro_certified=0; macro_used=0 | Macro is diagnostic-only, so macro-driven relation authority is correctly blocked but economically incomplete. |
| company_price_confirmed_path | catalyst_quality_tier\|price_acceptance_state\|mechanism_support_count | rule-based mechanism_relation_state | relation_certified=1024/1621 | This path is usable, but it blends price confirmation with economic causality. |
| full_context_graph | chart\|theme\|market\|company\|event\|macro\|portfolio | not implemented as graph; partially represented by interaction_context_packet | not_available | Missing prerequisite/blocker/offsetting/reinforcing edge graph with confidence and authority scope. |

### Firm-grade target ontology

| target_layer | purpose | must_contain | current_status |
| --- | --- | --- | --- |
| evidence_object | Store raw event/source facts without trading interpretation. | source_id\|event_ts\|available_at_ts\|symbol_link\|theme_link\|text_span\|source_quality | partial |
| economic_interpretation_object | Translate event into revenue/margin/cash-flow/backlog/regulatory/funding impact. | direction\|magnitude_proxy\|duration\|directness\|surprise\|priced_in_risk\|confidence | shallow |
| state_graph_edge | Represent how chart/theme/market/company/macro/portfolio affect each other. | edge_type reinforcing\|offsetting\|prerequisite\|blocker\|sizing_modifier; authority_scope; confidence | not_firm_grade |
| candidate_context_bundle | Bundle ex-ante facts for each lifecycle before allocation. | evidence_objects\|interpretation_objects\|state_edges\|missing_evidence\|forbidden_flags | partial |
| slot_decision_explanation | Explain why one candidate deserves a finite portfolio slot versus peers. | incumbent_comparison\|opportunity_cost\|replacement_hurdle\|do_not_trade_reason | weak |

### Split/OOS metrics

Not applicable. This task does not test a new trading rule.

### Failure decomposition

- The information layer is broad, but not cleanly separated into evidence, interpretation, relation edge, and slot decision objects.
- Several downstream labels repackage the same content evidence.
- The relation engine is not yet a full graph of interactions and authority scopes.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Economic interpretation quality needs contract size, customer quality, recurrence, margin bridge, expectation surprise, and priced-in analysis.
- Relation logic needs explicit edge types: reinforcing, offsetting, prerequisite, blocker, and sizing modifier.
- Allocation needs context bundles and replacement-hurdle explanations before another backtest.

## No-Background Decision-Maker Report

- What happened: we listed the information and found the weak point.
- Why it matters: the project has many data fields, but it does not yet reason like a firm-grade relational engine.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: separate raw evidence, event meaning, relationship logic, and slot decision before tuning returns.

## Artifact Manifest

- Inputs: Task684 interaction stack, Task686 source certification summary.
- Outputs: information inventory, overlap audit, logic gap audit, relation scope audit, target ontology, decision, pass/fail, manifest.
- Row counts: inventory 9, overlap 5, logic 6, relation 4, ontology 5.
- Validation commands: `python src/backtest/build_task687_information_ontology_logic_audit.py`; `python -m unittest tests.test_task687_information_ontology_logic_audit`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| information_groups_listed | PRIMARY_PASS | 1 | groups=9 | >=8 groups |
| overlap_risk_identified | PRIMARY_PASS | 1 | content/catalyst/relation/theme overlaps documented | overlaps documented |
| logic_gaps_identified | PRIMARY_PASS | 1 | high=5 | >=3 high gaps |
| relation_not_overclaimed | PRIMARY_PASS | 1 | relation partial | do not claim firm-grade |
| no_strategy_promotion | PRIMARY_PASS | 1 | audit only | NOT_ACCEPTED/FORBIDDEN |
