export const allowedDisabledActionFixture = {
  label: "BUY",
  actionState: "disabled",
  disabledReason: "Strategy acceptance is NOT_ACCEPTED.",
  requiredGovernanceChange: ["strategy_acceptance", "paper_permission"],
  mutationPermitted: false,
};

export const allowedBlockedActionFixture = {
  label: "LIVE DEPLOY",
  actionState: "disabled",
  disabledReason: "Deployment readiness is DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.",
  requiredGovernanceChange: ["deployment_readiness"],
  mutationPermitted: false,
};
