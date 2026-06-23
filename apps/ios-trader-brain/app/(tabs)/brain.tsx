import { View } from "react-native";

import {
  DisabledActionBar,
  MobileScanListItem,
  MobileV1StatusRail,
  ScreenSummary,
} from "../../src/components/domain";
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
          <Badge label="BRAIN v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">BRAIN</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Candidate rows are review surfaces,
          not source truth or trading permission.
        </AppText>
      </View>

      <MobileV1StatusRail
        items={[
          { label: "Queue", value: brain.candidates.length, tone: "readOnly" },
          { label: "Blocked", value: blockedCount, tone: "blocked" },
          { label: "Gate", value: "closed", tone: "blocked" },
        ]}
        subtitle="Phone-first v1"
        title="Candidate queue is review-only"
      />

      <ScreenSummary
        badges={[
          { label: "fixture-backed", tone: "readOnly" },
          { label: brain.governance.strategyAcceptance, tone: "blocked" },
          { label: "review queue", tone: "readOnly" },
        ]}
        description="Candidate scanning surface for read-only review. Candidate rows are not assignment, acceptance, or trading instructions."
        footer="Future outcomes, realized labels, and post-event returns remain excluded from filtering."
        links={[
          {
            href: "/brain/candidate/fixture-candidate-review",
            label: "Open sample candidate detail",
            helperText: "Review the current detail hierarchy with fixture evidence.",
          },
          {
            href: "/brain/chain/fixture-chain",
            label: "Open evidence chain",
            helperText: "Inspect read-only source and provenance layers.",
          },
        ]}
        metrics={[
          { label: "Candidates", value: brain.candidates.length, state: "readOnly" },
          { label: "Review-only", value: reviewOnlyCount, state: "readOnly" },
          { label: "Blocked", value: blockedCount, state: "blocked" },
          { label: "Strict gate open", value: brain.sourceSummary.strictGateOpenCount, state: "blocked" },
        ]}
        title="Candidate review queue"
      />

      <SectionContainer title="Review Queue" description="Rows are read-only and fixture-backed.">
        <View style={{ gap: spacing.sm }}>
          {brain.candidates.map((candidate) => (
            <MobileScanListItem
              key={candidate.candidateId}
              badges={[
                {
                  label: candidate.lifecycleState,
                  tone: candidate.lifecycleState === "BLOCKED" ? "blocked" : "readOnly",
                },
                {
                  label: candidate.decisionState,
                  tone: candidate.decisionState === "BLOCKED" ? "blocked" : "readOnly",
                },
                {
                  label: candidate.validationState,
                  tone: candidate.validationState === "BLOCKED" ? "blocked" : "unknown",
                },
              ]}
              body={candidate.reasonSummary ?? "UNKNOWN"}
              href={candidate.route}
              hrefLabel="Open read-only candidate detail"
              metrics={[
                { label: "Evidence", value: candidate.evidenceStrength, state: "unknown" },
                { label: "Sources", value: candidate.sourceStates.length, state: "readOnly" },
                { label: "Blockers", value: candidate.blockers.length, state: candidate.blockers.length > 0 ? "blocked" : "readOnly" },
              ]}
              sourceRefs={candidate.sourceStates.flatMap((sourceState) => sourceState.provenanceRefs)}
              subtitle={candidate.displayName}
              title={candidate.symbol}
            />
          ))}
          {brain.candidates.map((candidate) => (
            <CardContainer key={`${candidate.candidateId}-source-state`}>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                <Badge label={candidate.symbol} tone="readOnly" />
                <Badge
                  label={candidate.blockers.length > 0 ? "blocked source state" : "source state"}
                  tone={candidate.blockers.length > 0 ? "blocked" : "unknown"}
                />
              </View>
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

      <SectionContainer title="Blocked / Missing Evidence" description="Forbidden filters cannot enter assignment logic.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Missing" value={brain.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown" value={brain.sourceSummary.unknownCount} state="unknown" />
          <MetricCard label="Strict gate open" value={brain.sourceSummary.strictGateOpenCount} state="blocked" />
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Fresh" value={brain.sourceSummary.freshCount} state="fresh" />
          <MetricCard label="Stale" value={brain.sourceSummary.staleCount} state="stale" />
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

      <SectionContainer title="Disabled Actions" description="Review controls do not mutate strategy or broker state.">
        <DisabledActionBar actions={brain.disabledActions} />
      </SectionContainer>
    </ScreenContainer>
  );
}
