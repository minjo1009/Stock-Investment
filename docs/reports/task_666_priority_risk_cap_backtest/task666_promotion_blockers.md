# Task666 Promotion Blockers

## Decision

`PRIORITY_RISK_CAP_TESTED_NO_PROMOTION_CANDIDATE`

## Simple Reason

Risk caps were tested, but no promotion-eligible cap improved all required gates at the same time.

## Required Checks

- symbol blacklist = 0
- theme blacklist = 0 for promotion-eligible candidates
- return-derived promoted cap = 0
- label-derived promoted cap = 0
- fixed-hold or timing override = 0

## Main Blocker

`priority_active_relation_cap3` improved full-period capital versus Task639 and reduced MDD versus Task664, but its MDD was still worse than Task639.

- Task639: $7,639.62, MDD -23.76%
- Task664 priority: $8,797.73, MDD -33.63%
- Task666 priority_active_relation_cap3: $10,887.47, MDD -30.52%

This is useful research evidence, not a tradable acceptance.

