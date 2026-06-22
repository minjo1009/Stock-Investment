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
