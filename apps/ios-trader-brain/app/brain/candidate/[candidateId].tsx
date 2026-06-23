import { Link } from "expo-router";
import { useLocalSearchParams } from "expo-router";

import {
  DisabledActionBar,
  EvidenceList,
  MobileV1StatusRail,
  RiskGate,
  ScreenSummary,
  SourceAttributionCard,
  TimelineList,
  ValidationReadinessPanel,
} from "../../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../../src/components/foundation";
import { BlockerList, StatusRow } from "../../../src/components/generic";
import { NavigationContextBar, ProductDetailHeader, ProductDetailSection, ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { candidateDetailFixture } from "../../../src/read-models/candidateDetailFixture";

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
      <ProductDetailHeader
        badges={[
          { label: "Candidate Detail v1", tone: "readOnly" },
          { label: "Read-only", tone: "readOnly" },
          { label: "NOT_AUTHORITY", tone: "blocked" },
        ]}
        description="Scaffold-only fixture-backed view. Route params do not select authoritative data."
        title={candidate.symbol}
      />

      <NavigationContextBar
        crumbs={[
          { href: "/", label: "HOME" },
          { href: "/brain", label: "BRAIN" },
          { label: "Candidate Detail" },
        ]}
        note="Route context is read-only and does not select authoritative backend rows."
      />

      <ProductDetailSection sectionId="overview" title="Overview" description="Read the status first, then scan evidence, risk, and validation.">
        <MobileV1StatusRail
          items={[
            { label: "Decision", value: candidate.sections.decisionSummary.decisionState, tone: "readOnly" },
            { label: "Gate", value: candidate.sections.validationReadiness.sourceGateStatus, tone: "blocked" },
            { label: "Actions", value: candidate.disabledActions.length, tone: "blocked" },
          ]}
          subtitle="Product Detail v1"
          title={`${candidate.symbol} overview is read-only`}
        />
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

      </ProductDetailSection>

      <ProductDetailSection sectionId="evidence" title="Evidence" description="Unknown evidence remains unknown, not negative evidence.">
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

        <SectionContainer title="Evidence" description="Fixture-backed evidence rows only.">
          <EvidenceList evidence={candidate.sections.evidence} />
        </SectionContainer>

        <SectionContainer title="Evidence Chain" description="Read-only scaffold link to the fixture chain view.">
          <Link href="/brain/chain/fixture-chain">
            <AppText variant="caption">Open read-only chain detail</AppText>
          </Link>
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="source" title="Source" description="Source state remains visible before risk interpretation.">
        <SourceAttributionCard
          authority={candidate.sections.decisionSummary.authority}
          sourceStates={candidate.sections.risk.sourceStates}
          status={candidate.sections.risk.blockers.length > 0 ? "BLOCKER" : "UNKNOWN"}
          timestamp={candidate.generatedAt}
          title="Candidate source attribution"
        />
      </ProductDetailSection>

      <ProductDetailSection sectionId="risk" title="Risk" description="Blockers and source states stay visible before validation.">
        <RiskGate
          blockers={candidate.sections.risk.blockers}
          sourceStates={candidate.sections.risk.sourceStates}
          chartStates={candidate.sections.risk.chartStates}
        />
      </ProductDetailSection>

      <ProductDetailSection sectionId="validation" title="Validation" description="Validation is health evidence only, not acceptance.">
        <SectionContainer title="Validation Status" description="Validation status is not acceptance.">
          <ValidationReadinessPanel
            validationReadiness={candidate.sections.validationReadiness}
          />
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
      </ProductDetailSection>
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
