# Frontend Read Model Contract

## Contract Goal

Frontend props must be mapped from backend/read-model authority.
The frontend must not invent strategy state, source freshness, order permission, or broker truth.

## Minimum Fields

```ts
type GovernanceStatus = {
  strategyAcceptance: "NOT_ACCEPTED";
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
  realCapital: "FORBIDDEN";
  brokerMutationPermitted: false;
  paperPermission?: false;
  killSwitchActive?: boolean;
  controlStateSource?: string;
};

type SourceState = {
  sourceId: string;
  freshness: "FRESH" | "STALE" | "MISSING" | "UNKNOWN";
  strictGateAllowed: boolean;
  proxyAllowed: boolean;
  observedAt?: string;
  evidencePath?: string;
  blockerReason?: string;
};

type ReadOnlyDecision = {
  id: string;
  decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
  thesis?: string;
  reason?: string;
  evidence: Array<{ label: string; sourceId: string; provenance?: string }>;
  sources: SourceState[];
  blockers: string[];
  lifecycleState?: string;
  permissions: GovernanceStatus;
};
```

## Mapping Rules

Missing or stale data is `UNKNOWN` or `BLOCKER`.
It is never negative evidence.

Labels and outcomes must not enter assignment logic.

The frontend may filter and sort visible rows, but it must not infer lifecycle matching or source readiness from symbol/date/price/time proximity.

