# Task1021-1030 L1-L4 Institutional Upgrade

## Decision Summary

Verdict:

`l1_l4_institutional_upgrade_contracts_complete_no_replay`

This task upgrades Task1011-1020 from diagnosis into concrete L1-L4 institutional contracts.

Key result:

- Institutional source catalog rows: 46
- Downloaded source rows: 33
- Source families covered: 8
- Official or official-standard rows: 43
- L1 source family contract rows: 5
- L2 primitive schema rows: 7
- L3 relation mechanism rows: 8
- L4 thesis-card fields: 10
- Theme exposure-chain templates: 5
- Next task backlog: 10
- Replay executed: 0

Standing status:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

Next action:

Implement Task1031-1040: actual L1-L4 validators, extractors, and a small golden source-to-thesis set before another replay.

## Quant Expert Report

### Source Coverage

The source catalog now covers:

- macro_economic: 14
- policy_geopolitics: 8
- semiconductor_theme: 5
- ai_theme: 4
- energy_power_theme: 4
- space_theme: 3
- cybersecurity_theme: 4
- relation_ontology: 4

Authority tiers:

- official: 39
- official_standard: 4
- industry_or_academic_reference: 3

Downloaded rows: 33 / 46.

Failed rows: 13. These are recorded, not approximated. Failures are mostly HTTP 403, timeout, or 404.

### Important Sources

- BEA developer docs: https://www.bea.gov/resources/for-developers
- BLS API docs: https://www.bls.gov/bls/api_features.htm
- Census API datasets: https://www.census.gov/data/developers/data-sets.html
- EIA API docs: https://www.eia.gov/opendata/documentation.php
- Treasury FiscalData API: https://fiscaldata.treasury.gov/api-documentation/
- Federal Register API: https://www.federalregister.gov/developers/documentation/api/v1
- Congress API: https://api.congress.gov/
- BIS semiconductor export controls: https://www.bis.gov/press-release/bis-updated-public-information-page-export-controls-imposed-advanced-computing-semiconductor
- OFAC data schemas: https://ofac.treasury.gov/specially-designated-nationals-list-data-formats-data-schemas
- SIA semiconductor report: https://www.semiconductors.org/wp-content/uploads/2025/07/SIA-State-of-the-Industry-Report-2025.pdf
- OECD semiconductor value chain: https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/06/mapping-the-semiconductor-value-chain_5ba52971/4154cdbf-en.pdf
- NIST AI RMF: https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf
- Stanford AI Index 2025: https://hai-production.s3.amazonaws.com/files/hai_ai_index_report_2025.pdf
- EIA data center energy: https://www.eia.gov/todayinenergy/detail.php?id=67704
- DOE data center electricity demand: https://www.energy.gov/articles/doe-releases-new-report-evaluating-increase-electricity-demand-data-centers
- NASA economic impact: https://www.nasa.gov/wp-content/uploads/2025/04/nasa-fy23-economicimpactreport-brochure-508-fm-tagged.pdf?emrc=04dfc7
- CISA KEV: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
- NVD API docs: https://nvd.nist.gov/developers/vulnerabilities
- W3C PROV: https://www.w3.org/TR/prov-overview/
- W3C Time Ontology: https://www.w3.org/TR/owl-time/

### L1 Contract

The L1 source contracts now require source-family-specific fields.

Examples:

- macro: release timestamp, vintage timestamp, metric, period, unit, revision flag
- policy: lifecycle state, effective window, jurisdiction, affected entities
- filings: CIK, accession, filed timestamp, form type, symbol
- theme reports: domain node, value-chain node, denominator
- ontology: provenance model and valid-time model

This prevents raw source rows from becoming vague context.

### L2 Primitive Schema

Seven L2 primitive families were defined:

- macro_release
- policy_lifecycle
- semiconductor_value_chain
- ai_infrastructure
- energy_power
- cybersecurity
- space

Each primitive explicitly forbids future return, PnL, or outcome rank.

### L3 Mechanism Schema

Eight mechanism modifiers were defined on top of the nine primitive relation catalog:

- discount_rate
- demand_pull
- supply_constraint
- market_access
- capex_cycle
- cost_pressure
- security_risk
- contradiction

This is the key improvement. L3 can stop saying only "reinforces" or "weakens" and start encoding how the effect travels.

### L4 Thesis Card

L4 must now require:

- thesis_id
- variant_view
- consensus_view
- economic_driver
- denominator
- exposure_chain
- catalyst_window
- invalidation_path
- uncertainty_state
- outcome_used_for_assignment_flag

This turns L4 from evidence aggregation into a trader-readable thesis card contract.

### Theme Exposure Chains

Five exposure-chain templates were created:

- AI demand to semis/power/data-center exposure
- export controls to semiconductor market access
- rate path to high-duration growth exposure
- CISA KEV to security-spend pressure
- space budget/activity to launch and supplier exposure

## No-Background Decision-Maker Report

This is a real upgrade over the previous step.

Task1011 said:

```text
L1-L4 are weak.
```

Task1021 now says:

```text
Here is the institutional contract structure L1-L4 must obey.
```

But it is still not enough to replay.

Why:

- We have schemas and contracts.
- We do not yet have working extractors for all of them.
- We do not yet have 20 hand-reviewed golden examples.
- We do not yet have validators blocking bad L1-L4 rows from becoming candidates.

So the next work is implementation, not another backtest.

## Artifact Manifest

Inputs:

- `data/raw/research/l1_l4_context_curriculum/download_manifest.csv`
- official and institutional source URLs listed in `task1021_institutional_source_catalog.csv`

Outputs:

- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1021_institutional_source_catalog.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1022_source_authority_tier_contract.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1023_l1_source_family_contracts.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1024_l2_primitive_schema.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1025_l3_relation_mechanism_schema.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1026_l4_thesis_card_schema.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1027_theme_exposure_chain_templates.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1028_l1_l4_validator_contracts.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1029_next_task_backlog.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/task1030_no_replay_closeout.csv`
- `data/artifacts/task_1021_1030_l1_l4_institutional_upgrade/artifact_manifest.csv`

Validation commands:

```text
python scripts/trader_brain_1021_1030_l1_l4_institutional_upgrade.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1021_1030_l1_l4_institutional_upgrade
python scripts/trader_brain_1021_1030_l1_l4_institutional_upgrade_validate.py
python -m unittest tests.test_trader_brain_1021_1030_l1_l4_institutional_upgrade
```

Validation authority:

- `RESEARCH_ONLY_L1_L4_INSTITUTIONAL_UPGRADE_NO_REPLAY`

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
