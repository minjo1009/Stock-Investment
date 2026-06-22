# Domain Component Story Coverage Gap Audit

## Purpose

Define the component/story coverage that must exist before Candidate Detail or HOME implementation is selected.

This audit does not edit component code, Storybook stories, fixtures, validators, or package scripts.

## Current Status

Task3809 installed P0 props-only domain component contracts and Storybook coverage. This audit records the coverage expectations and implementation gates; it does not claim product screen readiness.

## P0 Component Inventory

- `DecisionHeader`
- `SourceFreshnessBadge`
- `BlockerList`
- `EvidenceList`
- `ValidationReadinessPanel`
- `RiskGate`
- `DisabledActionBar`
- `ChartWithSourceState`
- `SystemHealth`
- `OrderStateSummary`

## Required Story State Matrix

| State | Required Coverage |
| --- | --- |
| `fresh_source` | `SourceState` freshness visible |
| `stale_source` | stale source not hidden |
| `missing_source` | missing source shown as blocker/unknown |
| `unknown_source` | unknown visible |
| `blocked_state` | blocker reason/source refs visible |
| `disabled_action_state` | disabled action state, reason, required governance change visible |
| `chart_missing` | `CHART_MISSING` visible |
| `source_not_attached` | `SOURCE_NOT_ATTACHED` visible |
| `read_only_boundary` | trading mutation unavailable |
| `safety_boundary` | `NOT_ACCEPTED` / `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY` / `FORBIDDEN` visible |

## Read-model Contract Mapping

| Component | Required Contract Source | Must Not Invent |
| --- | --- | --- |
| `DecisionHeader` | `AppShellReadModel`, `CandidateDetailReadModel.sections.decisionSummary` | strategy acceptance, confidence score |
| `SourceFreshnessBadge` | `SourceState` | source truth |
| `BlockerList` | `BlockerState[]` | negative evidence from missing data |
| `EvidenceList` | `EvidenceItem[]` | unsourced evidence |
| `ValidationReadinessPanel` | validation readiness section | acceptance upgrade |
| `RiskGate` | `BlockerState[]`, `SourceState[]`, `ChartSourceState[]` | trading permission |
| `DisabledActionBar` | `DisabledAction[]` | active mutation handler |
| `ChartWithSourceState` | `ChartSourceState` | synthetic source-free fallback |
| `SystemHealth` | `SystemReadModel` | deployment readiness |
| `OrderStateSummary` | `OrdersReadModel`, `OrderDetailReadModel` | order execution permission |

## Gap Classification

Future audits should classify each component/state pair as `covered`, `gap`, `blocked`, or `not_applicable`. A covered story is health evidence only and never trading acceptance.

## Candidate Detail Readiness Gate

Candidate Detail remains blocked until fixture authority boundaries are acknowledged, required story states are covered or explicitly blocked, disabled actions stay disabled, chart/source blocker states are visible, and an explicit future implementation loop selects Candidate Detail.

## HOME Readiness Gate

HOME remains blocked until the same fixture/story/source-freshness gates are complete and an explicit future implementation loop selects HOME.

## Story Args Authority Rules

Story args may come from scaffold fixtures or typed builders only as `NOT_AUTHORITY`. They must not be treated as backend truth, broker truth, source truth, strategy acceptance, paper/live permission, deployment readiness, or real-capital permission.

## Acceptance Criteria

This audit passes if component inventory, required states, contract mapping, gap classification, Candidate Detail gate, HOME gate, and story-args authority rules are documented without editing components, stories, fixtures, validators, or package scripts.

## Failure Criteria

The audit fails if Storybook coverage is treated as product readiness, strategy acceptance, source truth, backend truth, broker truth, Candidate Detail authorization, HOME authorization, or if missing/stale/unknown is treated as negative evidence.

## Safety Boundaries

Strategy remains `NOT_ACCEPTED`. Deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`. Real capital remains `FORBIDDEN`. No broker mutation, live order, paper promotion, product screen implementation, component edit, story edit, fixture edit, or validator edit is authorized.
