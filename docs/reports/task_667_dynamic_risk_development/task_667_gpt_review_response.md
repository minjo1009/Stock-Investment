# Task667 GPT Review Response

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- source_type: external_model_interpretation
- use_rule: Review only. Local backtest and artifact gates decide acceptance.

## Summary

GPT agreed that active relation cap3 is promising but unsafe because it improves return while worsening MDD versus Task639.

## Promotion-Eligible

- Dynamic relation cap using entry-time macro/market/mechanism fields.
- Slot admission hurdle using relation state, catalyst tier, price acceptance, support count, and pressure count.
- Contextual sizing only when risk proxy combines with weaker relation quality.

## Diagnostic Only

- Account drawdown cap or account drawdown-based sizing.
- Forced slot eviction or early liquidation.
- Any rule based on observed losing symbols or losing themes.

## Important Implementation Feedback

- Account drawdown is an external path-control overlay and should not be a promotion-eligible signal-improvement rule.
- Volatility sizing should not cut all high-risk names blindly. High volatility plus strong reinforcing state may deserve normal size.
- Slot hurdle should not use average realized returns.
- Hostile macro should not automatically mean skip. It should adjust cap or require better confirmation.

## Required Artifacts

- capacity decision panel
- slot displacement or allocation audit
- relation cap audit
- volatility or risk-proxy sizing audit
- promotion blocker report

