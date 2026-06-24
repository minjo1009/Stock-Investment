// READ_ONLY_SELECTED_BACKTEST_SNAPSHOT.
// NOT_AUTHORITY: not account truth, broker truth, paper truth, deployment
// readiness, strategy acceptance, or real-capital permission.

export type BacktestSnapshotReadModel = {
  contractVersion: "frontend-backtest-snapshot-v1";
  snapshotType: "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT";
  authority: "NOT_AUTHORITY";
  displayState: "DIAGNOSTIC_ONLY";
  selectedTaskId: "Task3903";
  selectedReportPath: string;
  sourceArtifacts: string[];
  generatedAt: string;
  governance: {
    strategyAcceptance: "NOT_ACCEPTED";
    deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY";
    realCapital: "FORBIDDEN";
    brokerMutationPermitted: false;
    paperPermission: false;
    livePermission: false;
  };
  selectedPolicy: {
    policyId: "exit_chain_repaired_soft_boost_cap_top2_v1";
    universeRows: number;
    secAttachedRows: number;
    neutralGapRows: number;
    sameExperimentParityPass: boolean;
  };
  metrics: {
    finalEquity: number;
    cagr: number;
    maxDrawdown: number;
    trades: number;
  };
  chartSource: {
    status: "SOURCE_NOT_ATTACHED";
    reason: string;
  };
  forbiddenInterpretations: string[];
};

export const backtestSnapshotFixture = {
  contractVersion: "frontend-backtest-snapshot-v1",
  snapshotType: "READ_ONLY_SELECTED_BACKTEST_SNAPSHOT",
  authority: "NOT_AUTHORITY",
  displayState: "DIAGNOSTIC_ONLY",
  selectedTaskId: "Task3903",
  selectedReportPath:
    "docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/stage1_sec_neutral_attach_same_experiment_replay_report.md",
  sourceArtifacts: [
    "docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/artifact_manifest.csv",
    "docs/reports/task_3903_stage1_sec_neutral_attach_same_experiment_replay/task_3903_decision.csv",
  ],
  generatedAt: "2026-06-24T00:00:00Z",
  governance: {
    strategyAcceptance: "NOT_ACCEPTED",
    deploymentReadiness: "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
    realCapital: "FORBIDDEN",
    brokerMutationPermitted: false,
    paperPermission: false,
    livePermission: false,
  },
  selectedPolicy: {
    policyId: "exit_chain_repaired_soft_boost_cap_top2_v1",
    universeRows: 3100,
    secAttachedRows: 267,
    neutralGapRows: 2833,
    sameExperimentParityPass: true,
  },
  metrics: {
    finalEquity: 6537.58,
    cagr: 0.4388,
    maxDrawdown: -0.282109,
    trades: 124,
  },
  chartSource: {
    status: "SOURCE_NOT_ATTACHED",
    reason:
      "Frontend display has selected summary metrics only; equity curve and benchmark chart sources are not attached yet.",
  },
  forbiddenInterpretations: [
    "strategy acceptance",
    "deployment readiness",
    "paper permission",
    "live permission",
    "broker truth",
    "real-capital permission",
    "account valuation",
  ],
} satisfies BacktestSnapshotReadModel;
