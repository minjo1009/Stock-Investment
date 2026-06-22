import type { ChainDetailReadModel } from "./common";

// Scaffold-only wrapper derived from src/mocks/fixtures/chain-detail.json.
// NOT_AUTHORITY: not lineage authority, source truth, trading permission,
// deployment readiness, paper/live permission, or real-capital permission.
export const chainDetailFixture = {
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
    missingCount: 1,
    unknownCount: 1,
    strictGateOpenCount: 0,
  },
  blockers: [
    {
      blockerId: "chain-layer-missing",
      severity: "P1",
      label: "Layer missing",
      reason: "Missing layers remain visible in the chain fixture.",
      sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      detectedAt: null,
    },
  ],
  disabledActions: [
    {
      actionId: "submit",
      label: "Submit disabled",
      actionState: "disabled",
      disabledReason: "Chain detail is read-only.",
      requiredGovernanceChange: [
        "brokerMutationPermitted must become true in authority documents",
      ],
    },
  ],
  chainId: "fixture-chain",
  layers: [
    {
      layer: "L0_RAW",
      status: "PRESENT",
      artifactRefs: ["apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json"],
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: null,
    },
    {
      layer: "L2_MEANING",
      status: "STALE",
      artifactRefs: [],
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: "Scaffold meaning layer is stale.",
    },
    {
      layer: "L6_RUNTIME",
      status: "MISSING",
      artifactRefs: [],
      provenanceRefs: [],
      blockerReason: "No runtime authority fixture is attached.",
    },
    {
      layer: "L7_FRONTEND",
      status: "UNKNOWN",
      artifactRefs: ["apps/ios-trader-brain/src/mocks/fixtures/chain-detail.json"],
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: "Frontend fixture is not source authority.",
    },
  ],
} satisfies ChainDetailReadModel;
