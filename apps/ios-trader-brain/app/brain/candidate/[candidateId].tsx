import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import {
  DecisionHeader,
  DisabledActionBar,
  EvidenceList,
  RiskGate,
  ValidationReadinessPanel,
} from "../../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../../src/components/foundation";
import { BlockerList, StatusRow } from "../../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { candidateDetailFixture } from "../../../src/read-models/candidateDetailFixture";
import { spacing } from "../../../src/theme/tokens";

export default function CandidateDetailRoute() {
  const params = useLocalSearchParams<{ candidateId?: string }>();
  const candidate = candidateDetailFixture;
  const routeCandidateId = Array.isArray(params.candidateId)
    ? params.candidateId[0]
    : params.candidateId;
  const routeMismatch =
    routeCandidateId !== undefined && routeCandidateId !== candidate.candidateId;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="Candidate Detail v0" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">{candidate.symbol}</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Route params do not select authoritative data.
        </AppText>
      </View>

      <SectionContainer title="Scaffold Boundary" description="This detail route is a fixture-backed assembly only.">
        <StatusRow
          label="Route candidateId"
          value={routeCandidateId ?? "UNKNOWN"}
          state={routeMismatch ? "blocked" : "readOnly"}
        />
        <StatusRow label="Fixture candidateId" value={candidate.candidateId} state="readOnly" />
        {routeMismatch ? (
          <AppText variant="caption">
            Fixture-backed demo only. Route param does not select authoritative data.
          </AppText>
        ) : null}
        <StatusRow
          label="Strategy"
          value={`Strategy ${candidate.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={candidate.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${candidate.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={candidate.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${candidate.governance.realCapital}`}
          state="blocked"
          sourceRef={candidate.governance.controlStateSource}
        />
        <BlockerList blockers={candidate.blockers} />
      </SectionContainer>

      <DecisionHeader
        decisionSummary={candidate.sections.decisionSummary}
        governance={candidate.governance}
      />

      <SectionContainer title="Thesis / Logic" description="Read-only fixture text for display wiring.">
        <CardContainer>
          <AppText>{candidate.sections.thesisLogic.thesis ?? "UNKNOWN"}</AppText>
          <AppText variant="caption">{candidate.sections.thesisLogic.reason ?? "UNKNOWN"}</AppText>
          <AppText variant="caption">
            Economic meaning refs: {joinOrUnknown(candidate.sections.thesisLogic.economicMeaningRefs)}
          </AppText>
          <AppText variant="caption">
            Relation refs: {joinOrUnknown(candidate.sections.thesisLogic.relationRefs)}
          </AppText>
        </CardContainer>
      </SectionContainer>

      <ValidationReadinessPanel
        validationReadiness={candidate.sections.validationReadiness}
      />

      <SectionContainer title="Evidence" description="Unknown evidence remains unknown, not negative evidence.">
        <EvidenceList evidence={candidate.sections.evidence} />
      </SectionContainer>

      <RiskGate
        blockers={candidate.sections.risk.blockers}
        sourceStates={candidate.sections.risk.sourceStates}
        chartStates={candidate.sections.risk.chartStates}
      />

      <SectionContainer title="Next Action" description="Read-only actions only; trading mutation remains disabled.">
        <CardContainer>
          <Badge label="Review only" tone="readOnly" />
          {candidate.sections.nextAction.allowedReadOnlyActions.map((action) => (
            <AppText key={action}>{action}</AppText>
          ))}
          <AppText variant="caption">
            {candidate.sections.nextAction.nextEngineeringAction ?? "UNKNOWN"}
          </AppText>
        </CardContainer>
        <DisabledActionBar actions={candidate.sections.nextAction.disabledTradingActions} />
        <DisabledActionBar actions={candidate.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
