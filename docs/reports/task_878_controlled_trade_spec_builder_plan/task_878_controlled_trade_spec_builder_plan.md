# Task878 Controlled Trade-Spec Builder Plan

## Decision Summary

- Verdict: executed for diagnostic controlled replay.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Purpose: plan the builder that turns dry adapter input into controlled replay rows after Task871/872/877 pass.

## Quant Expert Report

The builder must not infer trades from text. It must join:

```text
adapter_inputs.csv
-> trade_spec_authority_contract.csv
-> explicit_harness_universe_contract.csv
-> market_data_gate_promotion_result
```

If any required field is missing, output blocked rows rather than trades.

## No-Background Decision-Maker Report

This is the missing bridge from brain thesis to replay row.

Execution update:

- 22 controlled trade-spec rows were generated.
- Symbols came only from the explicit harness universe contract.
- Side was fixed to long by controlled policy.
- Entry used next daily adjusted close strictly after bundle as-of.
- Position capital was split from the `$1,000` diagnostic replay budget.

## Artifact Manifest

- Output: `data/artifacts/task_870_879_full_controlled_replay/controlled_trade_specs.csv`.
- Validation command: `python scripts/trader_brain_870_879_full_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
