import type { SystemReadModel } from "./common";

// Scaffold-only wrapper derived from src/mocks/fixtures/system-health.json.
// NOT_AUTHORITY: not runtime truth, deployment readiness, paper/live permission,
// broker truth, or real-capital permission.
export const systemHealthFixture = {
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
      blockerId: "system-fixture-not-authority",
      severity: "P0",
      label: "System fixture not authority",
      reason: "System health fixture is scaffold-only.",
      sourceRefs: ["apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json"],
      detectedAt: "2026-06-22T00:00:00Z",
    },
  ],
  disabledActions: [
    {
      actionId: "live_promote",
      label: "Live promotion disabled",
      actionState: "disabled",
      disabledReason: "Deployment readiness is diagnostic-only.",
      requiredGovernanceChange: [
        "deploymentReadiness must change from DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
      ],
    },
  ],
  controlState: {
    runMode: "DIAGNOSTIC_ONLY",
    killSwitchActive: true,
    emergencyCancelAllowed: false,
    sourcePath: "docs/operating_system/project_operating_state.md",
    observedAt: "2026-06-22T00:00:00Z",
  },
  sourceFreshness: [
    {
      sourceId: "system-source-fresh",
      sourceLabel: "System fresh fixture",
      freshnessStatus: "FRESH",
      observedAt: "2026-06-22T00:00:00Z",
      generatedAt: "2026-06-22T00:00:00Z",
      sourceCount: 1,
      strictGateAllowed: false,
      proxyAllowed: false,
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: null,
    },
    {
      sourceId: "system-source-stale",
      sourceLabel: "System stale fixture",
      freshnessStatus: "STALE",
      observedAt: "2026-06-01T00:00:00Z",
      generatedAt: "2026-06-22T00:00:00Z",
      sourceCount: 1,
      strictGateAllowed: false,
      proxyAllowed: false,
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: "Stale source must remain visible.",
    },
    {
      sourceId: "system-source-missing",
      sourceLabel: "System missing fixture",
      freshnessStatus: "MISSING",
      observedAt: null,
      generatedAt: null,
      sourceCount: null,
      strictGateAllowed: false,
      proxyAllowed: false,
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: "Missing source must remain visible.",
    },
    {
      sourceId: "system-source-unknown",
      sourceLabel: "System unknown fixture",
      freshnessStatus: "UNKNOWN",
      observedAt: null,
      generatedAt: null,
      sourceCount: null,
      strictGateAllowed: false,
      proxyAllowed: false,
      provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      blockerReason: "Unknown source must not be interpreted.",
    },
  ],
  validatorStatus: [
    {
      validatorId: "frontend-fixture-validator",
      command: "npm run validate:fixtures",
      latestStatus: "UNKNOWN",
      latestRunAt: null,
      reportPath:
        "docs/reports/task_frontend_read_model_fixtures_domain_contracts/task_frontend_read_model_fixtures_domain_contracts.md",
    },
  ],
  artifactHealth: [
    {
      artifactId: "catalog-manifest",
      path: "apps/ios-trader-brain/src/mocks/fixtures/catalog-manifest.json",
      status: "PRESENT",
    },
    {
      artifactId: "backend-authority-catalog",
      path: "NOT_SELECTED",
      status: "UNKNOWN",
    },
  ],
} satisfies SystemReadModel;
