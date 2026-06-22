# Candidate Detail Screen Readiness Checklist

## Purpose

Define the future readiness gate for Candidate Detail before implementation is selected.

This checklist does not implement Candidate Detail.

## Current Status

Candidate Detail implementation remains blocked. Current fixtures are `NOT_AUTHORITY`, and frontend remains read-only.

## Non-Authorization Rule

Candidate Detail readiness does not authorize Candidate Detail implementation, product screen work, trading actions, paper/live promotion, deployment readiness, broker mutation, or real-capital use.

## Candidate Detail Six-Section Contract

Future Candidate Detail must follow:

1. Decision Summary
2. Thesis / Logic
3. Validation Readiness
4. Evidence
5. Risk
6. Next Action

## Required Read-model Fields

- `candidateId`
- `symbol`
- `sections.decisionSummary.decisionState`
- `sections.decisionSummary.authority`
- `sections.decisionSummary.generatedAt`
- `sections.decisionSummary.disabledActions`
- `sections.thesisLogic.thesis`
- `sections.thesisLogic.reason`
- `sections.thesisLogic.economicMeaningRefs`
- `sections.thesisLogic.relationRefs`
- `sections.validationReadiness.splitOosStatus`
- `sections.validationReadiness.leakageStatus`
- `sections.validationReadiness.costSlippageStatus`
- `sections.validationReadiness.sourceGateStatus`
- `sections.validationReadiness.readinessSummary`
- `sections.evidence[]`
- `sections.risk.blockers`
- `sections.risk.sourceStates`
- `sections.risk.chartStates`
- `sections.nextAction.allowedReadOnlyActions`
- `sections.nextAction.disabledTradingActions`
- `sections.nextAction.nextEngineeringAction`

## Required Component Coverage

Candidate Detail depends on `DecisionHeader`, `EvidenceList`, `ValidationReadinessPanel`, `RiskGate`, `DisabledActionBar`, `ChartWithSourceState`, `SourceFreshnessBadge`, and `BlockerList`.

## Required Storybook Coverage

Required states: fresh source, stale source, missing source, unknown source, blocked state, disabled action state, chart missing, source not attached, read-only boundary, safety boundary.

## Disabled Action Evidence

Candidate Detail must not create a Candidate -> BUY path. Next Action must be read-only and separate `allowedReadOnlyActions`, `disabledTradingActions`, and `nextEngineeringAction`.

Disabled trading actions must display `actionState = disabled`, `disabledReason`, `requiredGovernanceChange`, and current hard boundary.

## Implementation Gate

Candidate Detail implementation remains blocked unless fixture authority boundary audit is complete, domain story gap audit is complete, read-model fields are sufficient, required components are Storybook-covered, disabled trading actions remain disabled, source freshness/blockers/chart states are visible, screenshot QA preflight exists, Maestro preflight exists, and a future implementation loop explicitly selects Candidate Detail.

## Forbidden Inferences

Candidate Detail readiness does not prove product screen readiness, backend truth, source truth, broker truth, strategy acceptance, deployment readiness, paper readiness, live readiness, order execution permission, real-capital permission, candidate lifecycle truth, economic interpretation correctness, or production read-path authority.

## Acceptance Criteria

This checklist passes if the six-section contract, required fields, components, Storybook states, disabled action evidence, implementation gate, blockers, and forbidden inferences are documented without editing screens, routes, components, stories, fixtures, validators, or package scripts.

## Failure Criteria

This checklist fails if Candidate Detail implementation begins, Candidate -> BUY is introduced, fixture data is treated as authority, missing/stale/unknown is treated as negative evidence, or readiness is used to claim trading/deployment/paper/live/real-capital permission.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, Candidate Detail implementation, DB/runtime connection, component edit, story edit, fixture edit, validator edit, or package edit is authorized.
