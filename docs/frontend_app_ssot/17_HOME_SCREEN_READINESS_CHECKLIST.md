# HOME Screen Readiness Checklist

## Purpose

Define the future readiness gate for HOME before implementation is selected.

This checklist does not implement HOME.

## Current Status

HOME implementation remains blocked. Current fixtures are `NOT_AUTHORITY`, and the frontend remains read-only.

## Non-Authorization Rule

HOME readiness does not authorize HOME implementation, product screen work, trading actions, paper/live promotion, deployment readiness, broker mutation, or real-capital use.

## HOME Read-model Contract

Future HOME must derive from `HomeReadModel` and `AppShellReadModel`.

Required shell fields include `generatedAt`, `contractVersion`, `readPath`, `governance`, `sourceSummary`, `blockers`, and `disabledActions`.

Rules:

- If any required source is stale or missing, HOME must show it.
- `strictGateOpenCount` does not grant permission by itself.
- A fresh source does not grant strategy acceptance.
- Disabled actions stay disabled even when data is fresh.

## Required HOME Sections

1. Portfolio Snapshot
2. Brain Snapshot
3. Attention Queue
4. Freshness Summary
5. Blocker Summary
6. Governance / Disabled Actions Boundary

## Required Read-model Fields

- `portfolioSnapshot.accountValue`
- `portfolioSnapshot.cash`
- `portfolioSnapshot.investedCash`
- `portfolioSnapshot.openPnl`
- `portfolioSnapshot.realizedPnl`
- `portfolioSnapshot.sourceState`
- `brainSnapshot.candidateCount`
- `brainSnapshot.blockedCount`
- `brainSnapshot.reviewOnlyCount`
- `brainSnapshot.latestRuntimeDecisionAt`
- `brainSnapshot.sourceState`
- `attentionQueue[].itemId`
- `attentionQueue[].kind`
- `attentionQueue[].label`
- `attentionQueue[].reason`
- `attentionQueue[].severity`
- `attentionQueue[].route`
- `attentionQueue[].sourceRefs`
- `freshnessSummary[]`
- `blockerSummary[]`
- `sourceSummary.freshCount`
- `sourceSummary.staleCount`

## Source Freshness / Blocker Visibility

HOME must not use green portfolio summaries to hide stale DB/source state. Stale/missing/unknown must remain visible as `UNKNOWN/BLOCKER`.

## Implementation Gate

HOME implementation remains blocked unless fixture authority boundary audit is complete, domain component story gap audit is complete, `HomeReadModel` fields are sufficient, required components are Storybook-covered, source freshness and blockers are visible, screenshot QA preflight exists, Maestro preflight exists, a future implementation loop explicitly selects HOME, and scope remains read-only.

## Forbidden Inferences

HOME readiness does not prove HOME implementation authorization, product screen readiness, backend truth, source truth, broker truth, strategy acceptance, deployment readiness, paper readiness, live readiness, order execution permission, real-capital permission, production read-path authority, portfolio correctness, broker/account correctness, or runtime decision correctness.

## Acceptance Criteria

This checklist passes if HOME read-model fields, required sections, source/blocker visibility, component coverage, Storybook dependencies, screenshot/Maestro dependencies, fixture boundary, and implementation gate are documented without editing screens, components, stories, fixtures, validators, or package scripts.

## Failure Criteria

This checklist fails if HOME implementation begins, green portfolio summaries are allowed to hide stale sources, fixture data is treated as truth, `strictGateOpenCount` is treated as execution permission, or readiness is used to claim trading/deployment/paper/live/real-capital permission.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, HOME implementation, DB/runtime connection, component edit, story edit, fixture edit, validator edit, or package edit is authorized.
