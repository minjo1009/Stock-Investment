# Quant Context Map

This map converts external quant resources into project governance requirements.

## Context Sources

- **QuantStart Free Quantitative Finance Resources** / Data quality / source discipline: Free/back-adjusted data must be source-audited before production claims. Gap: Historical OHLCV exists, but receive_ts/status/LULD/full-depth coverage is incomplete.
- **awesome-quant** / Research libraries: Use pandas/statsmodels/sklearn/vectorized discovery as research tools, not deployment proof. Gap: Formal factor premium layer and multiple-testing audit are not yet canonical.
- **Backtest dashboard / tearsheet references** / Dashboard/reporting UX: Expose task registry, decision state, artifacts, blockers, and reports in a cockpit. Gap: Streamlit UI has manual report catalog and misses latest task lineage.
- **Tidy Finance / Fama-MacBeth references** / Factor premium/statistical validation: Validate whether entry-safe factors earn cross-sectional premium out-of-sample. Gap: No Fama-French adjustment or Fama-MacBeth panel currently exists.

## Missing Capability Matrix

- `receive_timestamp_native_replay`: missing_for_historical blocks `live_equivalent_backtest`
- `broker_truth_fills`: missing blocks `execution_grade_validation`
- `Fama_French_factor_data`: missing blocks `risk_adjusted_alpha_claim`
- `Fama_MacBeth_cross_section_panel`: missing blocks `factor_premium_claim`
- `automatic_research_cockpit`: partial blocks `investor_grade_visibility`
