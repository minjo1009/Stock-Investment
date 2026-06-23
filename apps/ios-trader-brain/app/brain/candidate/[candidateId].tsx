import { Link } from "expo-router";
import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import {
  DecisionHeader,
  DisabledActionBar,
  EvidenceList,
  RiskGate,
  ScreenSummary,
  TimelineList,
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
          <Badge label="Candidate Detail v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">{candidate.symbol}</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Route params do not select authoritative data.
        </AppText>
      </View>

      <ScreenSummary
        badges={[
          { label: candidate.sections.decisionSummary.decisionState, tone: "readOnly" },
          { label: candidate.sections.validationReadiness.sourceGateStatus, tone: "blocked" },
          { label: candidate.governance.strategyAcceptance, tone: "blocked" },
        ]}
        description="Read-only candidate detail hierarchy for reviewing decision summary, evidence, validation, risk, and next engineering action."
        footer="Route params are display hints only and do not select authoritative backend rows."
        links={[
          {
            href: "/brain",
            label: "Back to review queue",
            helperText: "Return to scaffold-only candidate rows.",
          },
          {
            href: "/brain/chain/fixture-chain",
            label: "Open evidence chain",
            helperText: "Trace fixture evidence and provenance layers.",
          },
        ]}
        metrics={[
          { label: "Evidence rows", value: candidate.sections.evidence.length, state: "readOnly" },
          { label: "Risk blockers", value: candidate.sections.risk.blockers.length, state: "blocked" },
          { label: "Source states", value: candidate.sections.risk.sourceStates.length, state: "unknown" },
          { label: "Disabled actions", value: candidate.disabledActions.length, state: "blocked" },
        ]}
        title={`${candidate.symbol} detail review`}
      />

      <TimelineList
        items={[
          {
            label: "Decision",
            value: candidate.sections.decisionSummary.authority,
            state: "readOnly",
          },
          {
            label: "Validation",
            value: candidate.sections.validationReadiness.readinessSummary,
            state: "blocked",
          },
          {
            label: "Next action",
            value: candidate.sections.nextAction.nextEngineeringAction ?? "UNKNOWN",
            state: "unknown",
          },
        ]}
      />

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

      <SectionContainer title="Evidence" description="Unknown evidence remains unknown, not negative evidence.">
        <EvidenceList evidence={candidate.sections.evidence} />
      </SectionContainer>

      <SectionContainer title="Evidence Chain" description="Read-only scaffold link to the fixture chain view.">
        <Link href="/brain/chain/fixture-chain">
          <AppText variant="caption">Open read-only chain detail</AppText>
        </Link>
      </SectionContainer>

      <SectionContainer title="Validation Status" description="Validation status is not acceptance.">
        <ValidationReadinessPanel
          validationReadiness={candidate.sections.validationReadiness}
        />
      </SectionContainer>

      <RiskGate
        blockers={candidate.sections.risk.blockers}
        sourceStates={candidate.sections.risk.sourceStates}
        chartStates={candidate.sections.risk.chartStates}
      />

      <SectionContainer title="Review Actions" description="Read-only actions only; trading mutation remains disabled.">
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
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
