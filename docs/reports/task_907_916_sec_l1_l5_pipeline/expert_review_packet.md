# Task907-916 Expert Review Packet

## Source Admission Review

Reviewer role: institutional quant and data research.

Conclusion:

- L1-L5 completion requires raw external document plus source-time proof.
- Internal lifecycle events may remain lineage context only.
- Required source corpus fields: `evidence_id`, `source_family`, `symbol`, `raw_source_uri`, `raw_storage_path`, `raw_source_hash`, `published_ts`, `received_ts`, `available_to_brain_ts`, `effective_ts`, and `revision_id`.
- Positive path must validate raw file existence, hash, source family, source span, and as-of ordering.

Applied change:

- Task907-916 uses SEC companyfacts raw JSON files for all 70 symbols.
- Task897-906 internal lifecycle rows remain blocked.

## Backend Validation Review

Reviewer role: backend and validation engineer.

Conclusion:

- Task897-906 no-go correction is valid, but it was a negative-path validator only.
- Positive path needs FK checks, hash checks, as-of checks, negative-field checks, and replay no-go separation.
- Trade spec and replay must require a separate L5/adapter gate; `diagnostic_replay_allowed` cannot bypass `trade_spec_allowed`.

Applied change:

- `scripts/trader_brain_907_916_sec_l1_l5_pipeline_validate.py` checks file hashes, FK chains, source-time order, forbidden columns, adapter ineligibility, dry decisions, and replay no-go.

## Institution And Specialist Review

Reviewer roles: Goldman Sachs, Morgan Stanley, JPMorgan, BofA, Citi, UBS, Barclays, Deutsche Bank, Citadel, Two Sigma, political risk, economist, semiconductor, AI infrastructure, and space/defense specialists.

Conclusion:

- Do not expand unlimited data ingestion.
- Use six source families first:
  - `company_filings_ir`
  - `earnings_guidance`
  - `macro_policy_official`
  - `supply_chain_customer_capex_cross_read`
  - `positioning_liquidity_volatility`
  - `sector_specialist_official_docs`
- Use nine relationship primitives:
  - `reinforces`
  - `weakens`
  - `invalidates`
  - `conditions`
  - `sequences`
  - `explains`
  - `contradicts`
  - `source_gap_for`
  - `noise_for`
- Candidate bundles must show `weakest_layer`, `contradictions`, `invalidation_conditions`, and `unresolved_gaps`.
- L5 remains dry until adapter and replay gates exist.

Applied change:

- Task907-916 implements the first source family only.
- Candidate bundles include weakest layer and unresolved gaps.
- Replay remains `not_run_l5_trade_spec_no_go`.

## Status Boundary

This packet is review input only. It is not source-of-truth, strategy acceptance, deployment readiness, or real-capital permission.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
