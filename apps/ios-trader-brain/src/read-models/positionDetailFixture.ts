import type { PositionDetailReadModel } from "./common";

// Scaffold-only wrapper derived from src/mocks/fixtures/position-detail.json.
// NOT_AUTHORITY: not broker truth, position truth, trading permission,
// deployment readiness, paper/live permission, or real-capital permission.
export const positionDetailFixture = {
  generatedAt: "2026-06-22T00:00:00Z",
  contractVersion: "frontend-read-model-v1",
  readPath: "json_catalog",
  governance: {
    strategyAcceptance: "NOT_ACCEPTED",
    deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    realCapital: "FORBIDDEN",
    brokerMutationPermitted: false,
    paperPermission: false,
    livePermission: false,
    killSwitchActive: true,
    controlStateSource: "docs/operating_system/project_operating_state.md",
    authorityReportPath:
      "docs/reports/task_frontend_read_model_fixtures_domain_contracts/task_frontend_read_model_fixtures_domain_contracts.md",
  },
  sourceSummary: {
    freshCount: 0,
    staleCount: 1,
    missingCount: 1,
    unknownCount: 1,
    strictGateOpenCount: 0,
  },
  blockers: [
    {
      blockerId: "position-detail-reconciliation-blocked",
      severity: "P0",
      label: "Reconciliation blocked",
      reason: "No broker truth source is attached to this scaffold fixture.",
      sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      detectedAt: "2026-06-22T00:00:00Z",
    },
  ],
  disabledActions: [
    {
      actionId: "cancel",
      label: "Cancel disabled",
      actionState: "disabled",
      disabledReason: "Position detail is read-only and cannot mutate broker state.",
      requiredGovernanceChange: [
        "brokerMutationPermitted must become true in authority documents",
      ],
    },
  ],
  positionId: "fixture-position-unknown",
  symbol: "FIXA",
  sections: {
    decisionSummary: {
      decisionState: "UNKNOWN",
      authority: "NOT_AUTHORITY scaffold fixture",
      generatedAt: "2026-06-22T00:00:00Z",
      disabledActions: [
        {
          actionId: "cancel",
          label: "Cancel disabled",
          actionState: "disabled",
          disabledReason: "No broker mutation permission.",
          requiredGovernanceChange: [
            "brokerMutationPermitted must become true in authority documents",
          ],
        },
      ],
    },
    thesisLogic: {
      thesis: null,
      reason: "Position fixture does not attach a source-backed thesis.",
      economicMeaningRefs: [],
      relationRefs: [],
    },
    validationReadiness: {
      splitOosStatus: "UNKNOWN",
      leakageStatus: "UNKNOWN",
      costSlippageStatus: "UNKNOWN",
      sourceGateStatus: "BLOCKED",
      readinessSummary: "Position detail fixture has no authority evidence.",
    },
    evidence: [
      {
        evidenceId: "position-evidence-missing",
        label: "Missing broker truth evidence",
        value: null,
        sourceId: "fixture-portfolio-source-missing",
        provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
        freshnessStatus: "MISSING",
      },
    ],
    risk: {
      blockers: [
        {
          blockerId: "position-source-missing",
          severity: "P0",
          label: "Source missing",
          reason: "Broker truth source is missing.",
          sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
          detectedAt: null,
        },
      ],
      sourceStates: [
        {
          sourceId: "fixture-position-source-unknown",
          sourceLabel: "Position unknown source",
          freshnessStatus: "UNKNOWN",
          observedAt: null,
          generatedAt: null,
          sourceCount: null,
          strictGateAllowed: false,
          proxyAllowed: false,
          provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
          blockerReason: "Position source unknown.",
        },
      ],
      chartStates: [
        {
          chartId: "position-chart-source-not-attached",
          status: "SOURCE_NOT_ATTACHED",
          sourceIds: [],
          blockerReason: "No chart source attached.",
        },
      ],
    },
    nextAction: {
      allowedReadOnlyActions: ["Open Evidence", "View Risk"],
      disabledTradingActions: [
        {
          actionId: "broker_sync",
          label: "Broker sync disabled",
          actionState: "disabled",
          disabledReason: "Broker mutation is forbidden.",
          requiredGovernanceChange: [
            "brokerMutationPermitted must become true in authority documents",
          ],
        },
      ],
      nextEngineeringAction: "Attach read-only broker truth catalog before product screen work.",
    },
    reconciliation: {
      localRecordState: "UNKNOWN",
      brokerTruthState: "BLOCKED",
      latestReconciliationAt: null,
      blockerReason: "Broker truth source is not attached to scaffold fixture.",
    },
  },
} satisfies PositionDetailReadModel;
