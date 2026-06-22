# Pull Request Checklist

## Decision Summary

- Task ID:
- Owner team:
- Change type: research / data / infra / execution / governance
- Strategy acceptance impact: none / diagnostic / candidate / deployment-readiness

## Required Integrity Checks

- [ ] Exact lifecycle or decision key joins only; no symbol/date/price/time fallback.
- [ ] Missing labels are not treated as negatives.
- [ ] Raw source availability is reported for every new factor.
- [ ] No unavailable source is approximated as if exact.
- [ ] Leakage audit is generated or explicitly unchanged.
- [ ] Validation and recent OOS are reported where strategy metrics changed.
- [ ] Cost/slippage stress is reported where PnL changed.
- [ ] Artifact manifest or task registry entry is updated.

## Validation

Commands run:

```text

```

Residual risk:

```text

```
