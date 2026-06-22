import type { BlockerState, DisabledAction, SourceState } from "../../read-models/common";

export const fixtureSourceStates = {
  fresh: {
    sourceId: "fixture-source-fresh",
    sourceLabel: "Fixture source fresh",
    freshnessStatus: "FRESH",
    observedAt: "2026-06-22T00:00:00Z",
    generatedAt: "2026-06-22T00:00:00Z",
    sourceCount: 3,
    strictGateAllowed: false,
    proxyAllowed: false,
    provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
    blockerReason: null,
  },
  stale: {
    sourceId: "fixture-source-stale",
    sourceLabel: "Fixture source stale",
    freshnessStatus: "STALE",
    observedAt: "2026-06-01T00:00:00Z",
    generatedAt: "2026-06-01T00:00:00Z",
    sourceCount: 1,
    strictGateAllowed: false,
    proxyAllowed: false,
    provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
    blockerReason: "source freshness is stale",
  },
  missing: {
    sourceId: "fixture-source-missing",
    sourceLabel: "Fixture source missing",
    freshnessStatus: "MISSING",
    observedAt: null,
    generatedAt: null,
    sourceCount: null,
    strictGateAllowed: false,
    proxyAllowed: false,
    provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
    blockerReason: "required source is missing",
  },
  unknown: {
    sourceId: "fixture-source-unknown",
    sourceLabel: "Fixture source unknown",
    freshnessStatus: "UNKNOWN",
    observedAt: null,
    generatedAt: null,
    sourceCount: null,
    strictGateAllowed: false,
    proxyAllowed: false,
    provenanceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
    blockerReason: "source state cannot be proven",
  },
} satisfies Record<string, SourceState>;

export const fixtureBlockers = {
  blocked: [
    {
      blockerId: "fixture-blocker-governance",
      severity: "P0",
      label: "Governance blocked",
      reason:
        "Strategy acceptance is NOT_ACCEPTED and deployment readiness is DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
      sourceRefs: ["docs/operating_system/project_operating_state.md"],
      detectedAt: "2026-06-22T00:00:00Z",
    },
  ],
  missing: [
    {
      blockerId: "fixture-blocker-missing-source",
      severity: "P1",
      label: "Source missing",
      reason: "Required source is missing and must stay UNKNOWN/BLOCKER.",
      sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      detectedAt: null,
    },
  ],
  unknown: [
    {
      blockerId: "fixture-blocker-unknown-source",
      severity: "P2",
      label: "Unknown source state",
      reason: "Source state cannot be proven from the current fixture.",
      sourceRefs: ["docs/frontend_app_ssot/08_FRONTEND_READ_MODEL_CONTRACT.md"],
      detectedAt: null,
    },
  ],
} satisfies Record<string, BlockerState[]>;

export const fixtureDisabledActions = [
  {
    actionId: "execute",
    label: "Review action disabled",
    actionState: "disabled",
    disabledReason:
      "No broker mutation, paper promotion, live permission, or real-capital permission is allowed.",
    requiredGovernanceChange: [
      "strategyAcceptance must change from NOT_ACCEPTED",
      "deploymentReadiness must change from DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
      "realCapital must change from FORBIDDEN",
    ],
  },
] satisfies DisabledAction[];
