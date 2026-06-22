# Task666 GPT Review Response

- captured_via: Chrome ChatGPT
- tab: 1. 코딩/투자
- captured_at_kst: 2026-06-08 15:27:50 +09:00
- source_type: external_model_interpretation
- use_rule: Review only. Local backtest and artifact gates decide acceptance.

## Summary

GPT framed Task666 as a priority allocation risk-control test, not a new alpha test.

The central question should be:

> Can we reduce dangerous same-timestamp concentration while preserving the Task664 return gain?

## Main Feedback

Promotion-eligible caps:

- Theme concentration cap.
- Relation-state concentration cap.
- Theme x relation concentration cap.

Diagnostic-only caps:

- High-volatility theme cap.
- Aerospace cap.
- Cybersecurity cap.
- Data-devops cap.
- Any rule based on PLTR, FTNT, OKTA, CEG, or observed losing trades.

Reason:

- Promotion-eligible caps can be defined without future returns or labels.
- Diagnostic caps based on Task665 losers are return-tuned and cannot promote.

## Required Gates

- Task639 final capital must improve.
- Task664 MDD should improve.
- Validation and recent OOS should not break.
- QQQ comparison should remain favorable.
- Added/removed trade audit should show whether winner displacement improved.
- No symbol blacklist, no theme blacklist, no return-derived cap, no label-derived cap.

## Required Artifacts

- `task666_capacity_allocation_panel.csv`
- `task666_theme_concentration_audit.csv`
- `task666_relation_concentration_audit.csv`
- `task666_displacement_pairs.csv`
- `task666_mdd_contribution_report.csv`
- `task666_promotion_blockers.md`

## Implementation Decision

Task666 implemented promotion-eligible theme, relation-state, and theme x relation caps. It also implemented diagnostic-only high-volatility and MDD-bad-theme caps. Strategy promotion still depends only on local backtest gates.

