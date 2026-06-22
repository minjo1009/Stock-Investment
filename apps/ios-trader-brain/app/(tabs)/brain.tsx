import { Link, type Href } from "expo-router";
import { View } from "react-native";

import { DisabledActionBar } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import {
  BlockerList,
  MetricCard,
  SourceFreshnessBadge,
  StatusRow,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { brainFixture } from "../../src/read-models/brainFixture";
import { spacing } from "../../src/theme/tokens";

export default function BrainRoute() {
  const brain = brainFixture;
  const reviewOnlyCount = brain.candidates.filter(
    (candidate) => candidate.lifecycleState === "REVIEW_ONLY"
  ).length;
  const blockedCount = brain.candidates.filter(
    (candidate) => candidate.lifecycleState === "BLOCKED"
  ).length;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="BRAIN v0" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">BRAIN</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Candidate rows are review surfaces,
          not source truth or trading permission.
        </AppText>
      </View>

      <SectionContainer title="Scaffold Boundary" description="The BRAIN tab uses fixture data only.">
        <StatusRow
          label="Strategy"
          value={`Strategy ${brain.governance.strategyAcceptance}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${brain.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={brain.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${brain.governance.realCapital}`}
          state="blocked"
          sourceRef={brain.governance.controlStateSource}
        />
        <BlockerList blockers={brain.blockers} />
      </SectionContainer>

      <SectionContainer title="Brain Decision Snapshot" description="Fresh counts do not open any trading gate.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Candidates" value={brain.candidates.length} state="readOnly" />
          <MetricCard label="Review-only" value={reviewOnlyCount} state="readOnly" />
          <MetricCard label="Blocked" value={blockedCount} state="blocked" />
          <MetricCard label="Strict gate open" value={brain.sourceSummary.strictGateOpenCount} state="blocked" />
        </View>
      </SectionContainer>

      <SectionContainer title="Candidate Ideas" description="Rows are read-only and fixture-backed.">
        <View style={{ gap: spacing.sm }}>
          {brain.candidates.map((candidate) => (
            <CardContainer key={candidate.candidateId}>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                <Badge label={candidate.lifecycleState} tone={candidate.lifecycleState === "BLOCKED" ? "blocked" : "readOnly"} />
                <Badge label={candidate.decisionState} tone={candidate.decisionState === "BLOCKED" ? "blocked" : "readOnly"} />
                <Badge label={candidate.validationState} tone={candidate.validationState === "BLOCKED" ? "blocked" : "unknown"} />
              </View>
              <AppText variant="title">{candidate.symbol}</AppText>
              <AppText>{candidate.displayName}</AppText>
              <AppText variant="caption">{candidate.thesisSummary ?? "UNKNOWN"}</AppText>
              <AppText variant="caption">{candidate.reasonSummary ?? "UNKNOWN"}</AppText>
              <AppText variant="caption">Detail hint: {candidate.route}</AppText>
              <Link href={candidate.route as Href}>
                <AppText variant="caption">Open read-only candidate detail</AppText>
              </Link>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {candidate.sourceStates.map((sourceState) => (
                  <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
                ))}
              </View>
              <BlockerList blockers={candidate.blockers} emptyLabel="No blocker rows supplied for this fixture candidate" />
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <SectionContainer title="Risk Gate" description="Forbidden filters cannot enter assignment logic.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Fresh" value={brain.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="Stale" value={brain.sourceSummary.staleCount} state="stale" />
          <MetricCard label="Missing" value={brain.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown" value={brain.sourceSummary.unknownCount} state="unknown" />
        </View>
        <CardContainer>
          <Badge label="Forbidden filters" tone="blocked" />
          {brain.filters.forbiddenFilterKeys.map((filterKey) => (
            <AppText key={filterKey} variant="caption">
              {filterKey}
            </AppText>
          ))}
        </CardContainer>
      </SectionContainer>

      <SectionContainer title="Disabled Actions" description="Review controls do not mutate strategy or broker state.">
        <DisabledActionBar actions={brain.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}
