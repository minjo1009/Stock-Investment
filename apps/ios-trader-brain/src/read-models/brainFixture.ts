import type { BrainReadModel } from "./common";

// Scaffold-only wrapper derived from src/mocks/fixtures/brain.json.
// NOT_AUTHORITY: not backend truth, source truth, trading permission,
// deployment readiness, paper/live permission, or real-capital permission.
export const brainFixture = {
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
    freshCount: 1,
    staleCount: 1,
    missingCount: 0,
    unknownCount: 1,
    strictGateOpenCount: 0,
  },
  blockers: [
    {
      blockerId: "brain-runtime-unknown",
      severity: "P1",
      label: "Runtime decision source unknown",
      reason: "Fixture does not connect to backend runtime.",
      sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      detectedAt: null,
    },
  ],
  disabledActions: [
    {
      actionId: "approve",
      label: "Approve disabled",
      actionState: "disabled",
      disabledReason: "Strategy acceptance remains NOT_ACCEPTED.",
      requiredGovernanceChange: ["strategyAcceptance must change from NOT_ACCEPTED"],
    },
  ],
  candidates: [
    {
      candidateId: "fixture-candidate-review",
      symbol: "FIXA",
      displayName: "Fixture Candidate A",
      lifecycleState: "REVIEW_ONLY",
      decisionState: "REVIEW_ONLY",
      thesisSummary: "Scaffold-only thesis summary from contract fixture.",
      reasonSummary: "Used to verify read-only candidate row props.",
      validationState: "PARTIAL",
      evidenceStrength: "PARTIAL",
      sourceStates: [
        {
          sourceId: "fixture-candidate-source-fresh",
          sourceLabel: "Candidate fixture fresh source",
          freshnessStatus: "FRESH",
          observedAt: "2026-06-22T00:00:00Z",
          generatedAt: "2026-06-22T00:00:00Z",
          sourceCount: 1,
          strictGateAllowed: false,
          proxyAllowed: false,
          provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
          blockerReason: null,
        },
      ],
      blockers: [],
      route: "/brain/candidate/fixture-candidate-review",
    },
    {
      candidateId: "fixture-candidate-blocked",
      symbol: "FIXB",
      displayName: "Fixture Candidate B",
      lifecycleState: "BLOCKED",
      decisionState: "BLOCKED",
      thesisSummary: null,
      reasonSummary: "Missing source blocks interpretation.",
      validationState: "BLOCKED",
      evidenceStrength: "NONE",
      sourceStates: [
        {
          sourceId: "fixture-candidate-source-unknown",
          sourceLabel: "Candidate fixture unknown source",
          freshnessStatus: "UNKNOWN",
          observedAt: null,
          generatedAt: null,
          sourceCount: null,
          strictGateAllowed: false,
          proxyAllowed: false,
          provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
          blockerReason: "Source state cannot be proven.",
        },
      ],
      blockers: [
        {
          blockerId: "candidate-source-unknown",
          severity: "P1",
          label: "Source unknown",
          reason: "Unknown source cannot be treated as negative evidence.",
          sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
          detectedAt: null,
        },
      ],
      route: "/brain/candidate/fixture-candidate-blocked",
    },
  ],
  filters: {
    allowedFilterKeys: [
      "lifecycleState",
      "decisionState",
      "validationState",
      "evidenceStrength",
    ],
    forbiddenFilterKeys: ["future_outcome", "realized_label", "post_event_return"],
  },
} satisfies BrainReadModel;
