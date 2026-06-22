# Component Catalog

## Required Component Families

| Component | Purpose |
| --- | --- |
| `DecisionHeader` | decision state, authority, timestamp, gate status |
| `SourceFreshnessBadge` | fresh/stale/missing/source-not-attached display |
| `BlockerList` | blockers and unknown states |
| `EvidenceList` | source-backed observations with provenance |
| `ValidationReadinessPanel` | split/OOS, leakage, cost/slippage, source gate state |
| `RiskPanel` | exposure, stale source, kill-switch, control-state evidence |
| `DisabledActionBar` | disabled approve/reject/cancel/execute affordances with governance reason |
| `ProvenanceLink` | source or artifact pointer |
| `ChartWithSourceState` | chart plus source attachment/freshness status |
| `LifecycleStatePill` | candidate/paper/live/shadow lifecycle display only |

## Storybook Minimum

Each component must have stories for:

- fresh source
- stale source
- missing source
- blocked state
- unknown state
- disabled action state

