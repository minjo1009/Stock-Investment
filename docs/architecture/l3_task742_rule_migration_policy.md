# L3 Task742 Rule Migration Policy

## Decision

Task742 economic interpretation rules are migrated into `src/brain/l3` as
diagnostic-only recovered rules. They are not trade rules.

## Source

The local workspace did not contain:

```text
src/backtest/pragmatic_economic_meaning_layer.py
src/backtest/build_task742_pragmatic_economic_meaning_layer.py
```

The rule source was recovered from the project GitHub `main` branch and
migrated into:

```text
src/brain/l3/task742_rules.py
src/brain/l3/adapters/task742_rule_adapter.py
```

Source provenance is recorded in:

```text
docs/reports/task_l3_calibration_rule_migration/source_provenance.csv
```

## Migrated Rule Families

- `form4_insider_behavior`
- `ownership_float_structure`
- `activist_control`
- `credit_financing`
- `financial_results_guidance`
- `generic_8k_classifier`

## Preserved Boundaries

The migrated rules preserve the original Task742 boundaries:

- review-only interpretation
- static confidence bands only
- no trade output
- no score output
- no backtest eligibility
- no outcome assignment
- no BUY/SELL
- no rank
- no sizing
- no order intent

## Runtime Context

Task742 recovered inputs are historical research inputs. The adapter emits:

```text
runtime_context = HISTORICAL_RESEARCH
source_time_certified = false
authority_class = uncertified_source
```

This prevents recovered historical rows from being confused with live canonical
L2 primitive facts.

## Calibration Boundary

Task742 migrated rules can create L3 diagnostic meanings. They cannot create
calibrated probabilities unless a separate explicit outcome bridge exists and
passes the L3 calibration outcome contract.
