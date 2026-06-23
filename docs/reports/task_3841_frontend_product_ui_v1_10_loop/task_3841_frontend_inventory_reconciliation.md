# Task3841 Frontend Inventory Reconciliation

## Purpose

Loop 2 reconciles GPT's GitHub-prioritized next-work list with the current local repository state.

## Findings

- Chain Detail route already exists at `apps/ios-trader-brain/app/brain/chain/[chainId].tsx`.
- Position Detail route already exists at `apps/ios-trader-brain/app/portfolio/position/[positionId].tsx`.
- Order Detail route already exists at `apps/ios-trader-brain/app/orders/[orderId].tsx`.
- The safe implementation direction is therefore not to add duplicate routes.

## Adjusted Loop Plan

1. GPT prioritization.
2. Inventory reconciliation.
3. Chain Detail v1 hierarchy.
4. Position Detail v1 hierarchy.
5. Order Detail v1 hierarchy.
6. Detail v1 route validator.
7. Expanded Storybook coverage validator.
8. Screenshot target/route evidence hardening.
9. Screenshot recapture.
10. Closeout report and registry.

## Boundary

This reconciliation does not grant product readiness, backend source authority, broker truth, paper/live permission, deployment readiness, or real-capital permission.
