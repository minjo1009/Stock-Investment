export type GovernanceStatus = {
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

export type FreshnessStatus =
  | "FRESH"
  | "STALE"
  | "MISSING"
  | "UNKNOWN"
  | "NOT_APPLICABLE";

export type SourceState = {
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

export type BlockerState = {
  blockerId: string;
  severity: "P0" | "P1" | "P2" | "P3";
  label: string;
  reason: string;
  sourceRefs: string[];
  detectedAt: string | null;
};

export type DisabledAction = {
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

export type EvidenceItem = {
  evidenceId: string;
  label: string;
  value: string | number | boolean | null;
  unit?: string;
  sourceId: string;
  provenanceRefs: string[];
  freshnessStatus: FreshnessStatus;
};

export type ChartSourceState = {
  chartId: string;
  status: "READY" | "CHART_MISSING" | "SOURCE_NOT_ATTACHED" | "STALE" | "UNKNOWN";
  sourceIds: string[];
  blockerReason: string | null;
};

export type ComponentState =
  | "fresh"
  | "stale"
  | "missing"
  | "unknown"
  | "blocked"
  | "readOnly"
  | "disabled";

export type AppShellReadModel = {
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

export type ValidationReadiness = {
  splitOosStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
  leakageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
  costSlippageStatus: "PASS" | "FAIL" | "BLOCKED" | "UNKNOWN" | "NOT_APPLICABLE";
  sourceGateStatus: "OPEN" | "CLOSED" | "BLOCKED" | "UNKNOWN";
  readinessSummary: string;
};

export type DecisionSummary = {
  decisionState: "NO_TRADE" | "BLOCKED" | "UNKNOWN" | "REVIEW_ONLY";
  authority: string;
  generatedAt: string;
  disabledActions: DisabledAction[];
};

export type DetailSections = {
  decisionSummary: DecisionSummary;
  thesisLogic: {
    thesis: string | null;
    reason: string | null;
    economicMeaningRefs: string[];
    relationRefs: string[];
  };
  validationReadiness: ValidationReadiness;
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

export type HomeReadModel = AppShellReadModel & {
  portfolioSnapshot: {
    accountValue: number | null;
    cash: number | null;
    investedCash: number | null;
    openPnl: number | null;
    realizedPnl: number | null;
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

export type BrainReadModel = AppShellReadModel & {
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

export type CandidateDetailReadModel = AppShellReadModel & {
  candidateId: string;
  symbol: string;
  sections: DetailSections;
};

export type ChainDetailReadModel = AppShellReadModel & {
  chainId: string;
  layers: Array<{
    layer:
      | "L0_RAW"
      | "L1_FACT"
      | "L2_MEANING"
      | "L3_RELATION"
      | "L4_THESIS"
      | "L5_POLICY"
      | "L6_RUNTIME"
      | "L7_FRONTEND";
    status: "PRESENT" | "MISSING" | "STALE" | "BLOCKED" | "UNKNOWN";
    artifactRefs: string[];
    provenanceRefs: string[];
    blockerReason: string | null;
  }>;
};

export type PortfolioReadModel = AppShellReadModel & {
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

export type PositionDetailReadModel = AppShellReadModel & {
  positionId: string;
  symbol: string;
  sections: DetailSections & {
    reconciliation: {
      localRecordState: "PRESENT" | "MISSING" | "UNKNOWN";
      brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED";
      latestReconciliationAt: string | null;
      blockerReason: string | null;
    };
  };
};

export type OrdersReadModel = AppShellReadModel & {
  orderRows: Array<{
    orderId: string;
    symbol: string | null;
    side: "BUY" | "SELL" | "NONE" | "UNKNOWN";
    quantity: number | null;
    localState:
      | "NONE"
      | "CREATED"
      | "SUBMITTING"
      | "SUBMITTED_LOCAL_RECORDED"
      | "UNKNOWN"
      | "RECONCILED"
      | "BLOCKED";
    brokerTruthState: "MATCHED" | "MISMATCH" | "MISSING" | "UNKNOWN" | "BLOCKED" | "NOT_APPLICABLE";
    mutationPermitted: false;
    disabledActions: DisabledAction[];
    sourceStates: SourceState[];
    blockers: BlockerState[];
    route: string;
  }>;
};

export type OrderDetailReadModel = AppShellReadModel & {
  orderId: string;
  sections: {
    decisionSummary: DecisionSummary;
    thesisLogic: DetailSections["thesisLogic"];
    validationReadiness: ValidationReadiness;
    evidence: EvidenceItem[];
    risk: DetailSections["risk"];
    nextAction: DetailSections["nextAction"];
    orderState: {
      localState: OrdersReadModel["orderRows"][number]["localState"];
      brokerTruthState: OrdersReadModel["orderRows"][number]["brokerTruthState"];
      submittedAt: string | null;
      reconciledAt: string | null;
      unknownAgeSeconds: number | null;
    };
  };
};

export type SystemReadModel = AppShellReadModel & {
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
