# Frontend Read Model Contract

## Contract Goal

Frontend implementation must start from screen-ready read models, not from invented UI props.

The frontend is a read-only L7 query surface. It displays backend/runtime state, source freshness, blockers, provenance, and disabled action reasons. It must not compute trading authority, broker truth, strategy acceptance, paper permission, live permission, deployment readiness, or real-capital permission.

## Read Path Authority

One implementation task must select exactly one primary read path before app code expands:

| Read path | Status before selection | Rule |
| --- | --- | --- |
| Generated JSON catalog | allowed | Must include fingerprint, generated timestamp, source refs, and stale/missing states. |
| Runtime API endpoint | allowed | Must be read-only and backed by the same contract fields. |
| Read-only SQLite export | allowed for diagnostics | Must not open active DB write handles from the app. |
| Direct active `trading.db` write/read from app | forbidden | The frontend must not become DB authority. |
| Broker API | forbidden | No KIS/Alpaca/broker mutation or account action from the frontend. |

## Common Types

```ts
type GovernanceStatus = {
  strategyAcceptance: "NOT_ACCEPTED";
  deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
  realCapital: "FORBIDDEN";
  brokerMutationPermitted: false;
  paperPermission: false;
  livePermission: false;
  killSwitchActive: boolean;
  controlStateSource: string;
  authorityReportPath?: string;
};

type FreshnessStatus = "FRESH" | "STALE" | "MISSING" | "UNKNOWN" | "NOT_APPLICABLE";

type SourceState = {
  sourceId: string;
  sourceLabel: string;
  freshnessStatus: FreshnessStatus;
  observedAt: string | null;
  generatedAt: string | null;
  sourceCount: number | null;
  strictGateAllowed: boolean;
  proxyAllowed: boolean;
  provenanceRefs: string[];
  blockerReason: string | null;
};

type BlockerState = {
  blockerId: string;
  severity: "P0" | "P1" | "P2" | "P3";
  label: string;
  reason: string;
  sourceRefs: string[];
  detectedAt: string | null;
};

type DisabledAction = {
  actionId:
    | "approve"
    | "reject"
    | "cancel"
    | "execute"
    | "submit"
    | "paper_promote"
    | "live_promote"
    | "broker_sync";
  label: string;
  actionState: "disabled";
  disabledReason: string;
  requiredGovernanceChange: string[];
};

type EvidenceItem = {
  evidenceId: string;
  label: string;
  value: string | number | boolean | null;
  unit?: string;
  sourceId: string;
  provenanceRefs: string[];
  freshnessStatus: FreshnessStatus;
};

type ChartSourceState = {
  chartId: string;
  status: "READY" | "CHART_MISSING" | "SOURCE_NOT_ATTACHED" | "STALE" | "UNKNOWN";
  sourceIds: string[];
  blockerReason: string | null;
};
```

## Global App Shell Read Model

Every top-level tab receives this shell object:

```ts
type AppShellReadModel = {
  generatedAt: string;
  contractVersion: "frontend-read-model-v1";
  readPath: "json_catalog" | "runtime_api" | "readonly_sqlite_export";
  governance: GovernanceStatus;
  sourceSummary: {
    freshCount: number;
    staleCount: number;
    missingCount: number;
    unknownCount: number;
    strictGateOpenCount: number;
  };
  blockers: BlockerState[];
  disabledActions: DisabledAction[];
};
```

Shell rules:

- If any required source is stale or missing, the screen must show it.
- `strictGateOpenCount` does not grant permission by itself.
- A fresh source does not grant strategy acceptance.
- Disabled actions stay disabled even when data is fresh.

## Screen Inventory

| Screen | Required read model | Primary purpose |
| --- | --- | --- |
| `HOME` | `HomeReadModel` | Portfolio/brain/system snapshot and attention queue. |
| `BRAIN` | `BrainReadModel` | Candidate scanner, thesis bundles, review-only runtime decisions. |
| `Candidate Detail` | `CandidateDetailReadModel` | Six-section detail frame V2 for one candidate. |
| `Chain Detail` | `ChainDetailReadModel` | Source-to-decision provenance chain. |
| `PORTFOLIO` | `PortfolioReadModel` | Read-only positions and broker/local reconciliation summary. |
| `Position Detail` | `PositionDetailReadModel` | Holding thesis, risk, evidence, and reconciliation. |
| `ORDERS` | `OrdersReadModel` | Read-only intents, local records, broker-truth reconciliation. |
| `Order Detail` | `OrderDetailReadModel` | Order purpose, state, evidence, and disabled action context. |
| `SYSTEM` | `SystemReadModel` | Governance, source freshness, control state, validator status. |

## HOME Read Model

```ts
type HomeReadModel = AppShellReadModel & {
  portfolioSnapshot: {
    accountValue: number | null;
    cash: number | null;
    investedCash: number | null;
    openPnl: number | null;
    realizedPnl: number | null;
    totalReturnPct: number | null;
    winRatePct: number | null;
    maxDrawdownPct: number | null;
    sourceState: SourceState;
  };
  brainSnapshot: {
    candidateCount: number;
    blockedCount: number;
    reviewOnlyCount: number;
    latestRuntimeDecisionAt: string | null;
    sourceState: SourceState;
  };
  attentionQueue: Array<{
    itemId: string;
    kind: "candidate" | "position" | "order" | "source" | "system";
    label: string;
    reason: string;
    severity: "P0" | "P1" | "P2" | "P3";
    route: string;
    sourceRefs: string[];
  }>;
  freshnessSummary: SourceState[];
  blockerSummary: BlockerState[];
};
```

HOME first-screen priority is product/account comprehension: invested cash, account state, return state, win-rate state, and MDD must appear before governance/source detail. HOME must not hide stale DB/source state behind a green portfolio summary; source freshness and disabled permissions remain visible as secondary context.

## BRAIN Read Model

```ts
type BrainReadModel = AppShellReadModel & {
  scannerSummary: {
    candidateCount: number | null;
    reviewOnlyCount: number | null;
    blockedCount: number | null;
    weakEvidenceCount: number | null;
    latestReviewAt: string | null;
  };
  candidates: Array<{
    candidateId: string;
    symbol: string;
    displayName: string;
    lifecycleState: "REVIEW_ONLY" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
    decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
    thesisSummary: string | null;
    reasonSummary: string | null;
    validationState: "NOT_VALIDATED" | "BLOCKED" | "PARTIAL" | "UNKNOWN";
    evidenceStrength: "NONE" | "WEAK" | "PARTIAL" | "SOURCE_BACKED";
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
  filters: {
    allowedFilterKeys: string[];
    forbiddenFilterKeys: ["future_outcome", "realized_label", "post_event_return"];
  };
};
```

Forbidden rule: no `candidate_score`, `candidate_rank`, or `confidence_score` may be invented unless a backend authority explicitly provides and documents the field. BRAIN first-screen priority is candidate review comprehension: candidate count, review-only count, blocked count, and weak-evidence count must appear before governance/source detail.

## Candidate Detail Read Model

```ts
type CandidateDetailReadModel = AppShellReadModel & {
  candidateId: string;
  symbol: string;
  sections: {
    decisionSummary: {
      decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
      authority: string;
      generatedAt: string;
      disabledActions: DisabledAction[];
    };
    thesisLogic: {
      thesis: string | null;
      reason: string | null;
      economicMeaningRefs: string[];
      relationRefs: string[];
    };
    validationReadiness: {
      splitOosStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      leakageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      costSlippageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
      sourceGateStatus: "OPEN" | "CLOSED" | "BLOCKED" | "UNKNOWN";
      readinessSummary: string;
    };
    evidence: EvidenceItem[];
    risk: {
      blockers: BlockerState[];
      sourceStates: SourceState[];
      chartStates: ChartSourceState[];
    };
    nextAction: {
      allowedReadOnlyActions: string[];
      disabledTradingActions: DisabledAction[];
      nextEngineeringAction: string | null;
    };
  };
};
```

Candidate detail must render all six sections from `03_UNIVERSAL_DETAIL_FRAME_V2.md`.

## Chain Detail Read Model

```ts
type ChainDetailReadModel = AppShellReadModel & {
  chainId: string;
  layers: Array<{
    layer: "L0_RAW" | "L1_FACT" | "L2_MEANING" | "L3_RELATION" | "L4_THESIS" | "L5_POLICY" | "L6_RUNTIME" | "L7_FRONTEND";
    status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN";
    artifactRefs: string[];
    provenanceRefs: string[];
    blockerReason: string | null;
  }>;
};
```

Missing layers must be shown as blockers or unknowns. They must not be silently skipped.

## PORTFOLIO Read Model

```ts
type PortfolioReadModel = AppShellReadModel & {
  portfolioSummary: {
    investedCash: number | null;
    cash: number | null;
    totalMarketValue: number | null;
    unrealizedPnl: number | null;
    realizedPnl: number | null;
    positionCount: number | null;
    exposurePct: number | null;
    winRatePct: number | null;
    maxDrawdownPct: number | null;
  };
  positions: Array<{
    positionId: string;
    symbol: string;
    quantity: number | null;
    marketValue: number | null;
    unrealizedPnl: number | null;
    thesisState: "VALID" | "INVALIDATED" | "UNKNOWN" | "BLOCKED" | "NOT_APPLICABLE";
    brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED";
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
};
```

PORTFOLIO first-screen priority is account/position comprehension: invested cash, cash, market value, unrealized PnL, realized PnL, exposure, MDD, and win-rate state must appear before governance/source detail. Broker truth and local runtime records must be visibly separated.

## Position Detail Read Model

```ts
type PositionDetailReadModel = AppShellReadModel & {
  positionId: string;
  symbol: string;
  sections: CandidateDetailReadModel["sections"] & {
    reconciliation: {
      localRecordState: "PRESENT" | "MISSING" | "UNKNOWN";
      brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED";
      latestReconciliationAt: string | null;
      blockerReason: string | null;
    };
  };
};
```

Position detail must never imply that local records are broker truth.

## ORDERS Read Model

```ts
type OrdersReadModel = AppShellReadModel & {
  orderRows: Array<{
    orderId: string;
    symbol: string | null;
    side: "BUY" | "SELL" | "NONE" | "UNKNOWN";
    quantity: number | null;
    localState: "NONE" | "CREATED" | "SUBMITTING" | "SUBMITTED_LOCAL_RECORDED" | "UNKNOWN" | "RECONCILED" | "BLOCKED";
    brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED" | "NOT_APPLICABLE";
    mutationPermitted: false;
    disabledActions: DisabledAction[];
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
};
```

Order rows are observation rows. They are not broker mutation controls.

## Order Detail Read Model

```ts
type OrderDetailReadModel = AppShellReadModel & {
  orderId: string;
  sections: {
    decisionSummary: CandidateDetailReadModel["sections"]["decisionSummary"];
    thesisLogic: CandidateDetailReadModel["sections"]["thesisLogic"];
    validationReadiness: CandidateDetailReadModel["sections"]["validationReadiness"];
    evidence: EvidenceItem[];
    risk: CandidateDetailReadModel["sections"]["risk"];
    nextAction: CandidateDetailReadModel["sections"]["nextAction"];
    orderState: {
      localState: OrdersReadModel["orderRows"][number]["localState"];
      brokerTruthState: OrdersReadModel["orderRows"][number]["brokerTruthState"];
      submittedAt: string | null;
      reconciledAt: string | null;
      unknownAgeSeconds: number | null;
    };
  };
};
```

Cancel, amend, execute, submit, approve, reject, paper-promote, and live-promote controls must be disabled under current governance.

## SYSTEM Read Model

```ts
type SystemReadModel = AppShellReadModel & {
  controlState: {
    runMode: "DIAGNOSTIC_ONLY";
    killSwitchActive: boolean;
    emergencyCancelAllowed: false;
    sourcePath: string;
    observedAt: string | null;
  };
  sourceFreshness: SourceState[];
  validatorStatus: Array<{
    validatorId: string;
    command: string;
    latestStatus: "PASS" | "FAIL" | "UNKNOWN" | "NOT_RUN";
    latestRunAt: string | null;
    reportPath?: string;
  }>;
  artifactHealth: Array<{
    artifactId: string;
    path: string;
    status: "PRESENT" | "MISSING" | "STALE" | "UNKNOWN";
  }>;
};
```

SYSTEM is the canonical UI location for source freshness, control state, disabled-action reasons, and validator visibility.

## Empty And Error State Rules

| State | UI meaning | Forbidden interpretation |
| --- | --- | --- |
| `UNKNOWN` | source or state cannot be proven | negative trading evidence |
| `MISSING` | required input is absent | zero value or failed thesis |
| `STALE` | input exists but is not current enough | fresh permission |
| `BLOCKED` | governance or source gate prevents action | optional warning |
| `NOT_APPLICABLE` | field does not apply to this screen | hidden failure |

## Mapping Rules

Missing or stale data is `UNKNOWN` or `BLOCKER`.
It is never negative evidence.

Labels and outcomes must not enter assignment logic.

The frontend may filter and sort visible rows, but it must not infer lifecycle matching or source readiness from symbol/date/price/time proximity.

Storybook fixtures, screenshot QA states, and safety validators must be generated from this contract, not from ad hoc mock fields.
