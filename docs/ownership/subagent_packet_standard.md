# Subagent Packet Standard

Every delegated subagent task must be issued as a bounded packet. This prevents duplicate exploration, write conflicts, and undocumented assumptions.

## Packet Fields

```text
Objective:
Owner Team:
Reviewer Team:
Read Scope:
Write Scope:
Inputs:
Required Outputs:
Forbidden Actions:
Validation Command:
Validation Authority:
Report Requirement:
```

## Rules

- A worker can edit only its write scope.
- An explorer must not edit files.
- Two workers must not share the same write scope in parallel.
- Every worker must list changed files.
- Every worker must report commands run and commands not run.
- Every data or strategy task must state whether inferred matching was used.
- Every validation command must state its authority lane from `docs/architecture/test_validation_canonicalization_map.md`.
- A passing test must not be described as strategy acceptance, deployment readiness, broker truth completion, or real-capital permission unless the corresponding acceptance contract and registry row explicitly say so.

## Required Forbidden Actions For Quant Research

```text
Forbidden Actions:
- No symbol/date/price/time fallback matching.
- No unlabeled row to negative conversion.
- No unavailable raw source approximation.
- No deployment claim from diagnostic-only evidence.
- No strategy acceptance claim from test success.
- No broker-truth claim from synthetic, simulated, shadow, or runtime fallback rows.
```

## Recommended Team Mapping

| Team | Suggested Subagent Role |
|---|---|
| Data & Market Microstructure | raw source explorer/worker |
| Regime Research | regime feature explorer |
| Intraday Continuation Research | archetype/grid worker |
| Backtest & Simulation Infra | deterministic replay/grid worker |
| Execution & Risk | live readiness/reconciliation reviewer |
| Research Governance | registry/report/artifact reviewer |
