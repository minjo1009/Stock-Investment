import { useLocalSearchParams } from "expo-router";

import {
  DecisionHeader,
  DisabledActionBar,
  EvidenceList,
  MobileV1StatusRail,
  RiskGate,
  ScreenSummary,
  TimelineList,
  ValidationReadinessPanel,
} from "../../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../../src/components/foundation";
import { BlockerList, StatusRow } from "../../../src/components/generic";
import { ProductDetailHeader, ProductDetailSection, ScreenContainer, SectionContainer } from "../../../src/components/layout";
import { positionDetailFixture } from "../../../src/read-models/positionDetailFixture";

export default function PositionDetailRoute() {
  const params = useLocalSearchParams<{ positionId?: string }>();
  const position = positionDetailFixture;
  const routePositionId = Array.isArray(params.positionId) ? params.positionId[0] : params.positionId;
  const routeMismatch = routePositionId !== undefined && routePositionId !== position.positionId;

  return (
    <ScreenContainer>
      <ProductDetailHeader
        badges={[
          { label: "Position Detail v1", tone: "readOnly" },
          { label: "Read-only", tone: "readOnly" },
          { label: "NOT_AUTHORITY", tone: "blocked" },
        ]}
        description="Scaffold-only fixture-backed view. Route params do not select broker truth."
        title={position.symbol}
      />

      <ProductDetailSection sectionId="overview" title="Overview" description="Read local record state before source and broker blockers.">
        <MobileV1StatusRail
          items={[
            { label: "Local", value: position.sections.reconciliation.localRecordState, tone: "unknown" },
            { label: "Broker", value: position.sections.reconciliation.brokerTruthState, tone: "blocked" },
            { label: "Actions", value: position.disabledActions.length, tone: "blocked" },
          ]}
          subtitle="Product Detail v1"
          title={`${position.symbol} position is read-only`}
        />
        <ScreenSummary
          badges={[
            { label: position.sections.reconciliation.localRecordState, tone: "unknown" },
            { label: position.sections.reconciliation.brokerTruthState, tone: "blocked" },
            { label: position.governance.strategyAcceptance, tone: "blocked" },
          ]}
          description="Read-only position detail for thesis, evidence, validation, risk, and reconciliation blockers."
          footer="Route params are display hints only and do not select broker account truth."
          links={[
            {
              href: "/portfolio",
              label: "Back to positions",
              helperText: "Return to read-only portfolio rows.",
            },
            {
              href: "/orders",
              label: "Review order boundary",
              helperText: "Compare position reconciliation with order lifecycle.",
            },
          ]}
          metrics={[
            { label: "Evidence rows", value: position.sections.evidence.length, state: "readOnly" },
            { label: "Risk blockers", value: position.sections.risk.blockers.length, state: "blocked" },
            { label: "Source states", value: position.sections.risk.sourceStates.length, state: "unknown" },
            { label: "Disabled actions", value: position.disabledActions.length, state: "blocked" },
          ]}
          title={`${position.symbol} position review`}
        />

        <TimelineList
          items={[
            {
              label: "Local record",
              value: position.sections.reconciliation.localRecordState,
              state: "unknown",
            },
            {
              label: "Broker truth",
              value: position.sections.reconciliation.brokerTruthState,
              state: "blocked",
            },
            {
              label: "Latest reconciliation",
              value: position.sections.reconciliation.latestReconciliationAt ?? "UNKNOWN",
              state: "unknown",
              helperText: position.sections.reconciliation.blockerReason,
            },
          ]}
        />

        <DecisionHeader decisionSummary={position.sections.decisionSummary} governance={position.governance} />

        <SectionContainer title="Thesis / Logic" description="Missing thesis remains UNKNOWN, not negative evidence.">
          <CardContainer>
            <AppText>{position.sections.thesisLogic.thesis ?? "UNKNOWN"}</AppText>
            <AppText variant="caption">{position.sections.thesisLogic.reason ?? "UNKNOWN"}</AppText>
            <AppText variant="caption">
              Economic meaning refs: {joinOrUnknown(position.sections.thesisLogic.economicMeaningRefs)}
            </AppText>
            <AppText variant="caption">
              Relation refs: {joinOrUnknown(position.sections.thesisLogic.relationRefs)}
            </AppText>
          </CardContainer>
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="evidence" title="Evidence" description="Broker truth evidence is missing in this fixture.">
        <SectionContainer title="Evidence" description="Fixture-backed evidence rows only.">
          <EvidenceList evidence={position.sections.evidence} />
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="risk" title="Risk" description="Risk and reconciliation blockers stay ahead of validation.">
        <RiskGate
          blockers={position.sections.risk.blockers}
          sourceStates={position.sections.risk.sourceStates}
          chartStates={position.sections.risk.chartStates}
        />

        <SectionContainer title="Reconciliation" description="Local and broker truth states are not reconciled.">
          <StatusRow
            label="Local record"
            value={position.sections.reconciliation.localRecordState}
            state="unknown"
          />
          <StatusRow
            label="Broker truth"
            value={position.sections.reconciliation.brokerTruthState}
            state="blocked"
          />
          <StatusRow
            label="Latest reconciliation"
            value={position.sections.reconciliation.latestReconciliationAt ?? "UNKNOWN"}
            state="unknown"
          />
          <AppText variant="caption">{position.sections.reconciliation.blockerReason ?? "UNKNOWN"}</AppText>
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="validation" title="Validation" description="Validation is health evidence only, not account truth.">
        <SectionContainer title="Validation Status" description="Validation status is not account or broker truth.">
          <ValidationReadinessPanel validationReadiness={position.sections.validationReadiness} />
        </SectionContainer>

        <SectionContainer title="Review Actions" description="Read-only actions only; broker sync remains disabled.">
          <CardContainer>
            <Badge label="Review only" tone="readOnly" />
            {position.sections.nextAction.allowedReadOnlyActions.map((action) => (
              <AppText key={action}>{action}</AppText>
            ))}
            <AppText variant="caption">
              {position.sections.nextAction.nextEngineeringAction ?? "UNKNOWN"}
            </AppText>
          </CardContainer>
          <DisabledActionBar actions={position.sections.nextAction.disabledTradingActions} />
          <DisabledActionBar actions={position.disabledActions} />
        </SectionContainer>

        <SectionContainer title="Scaffold Boundary" description="Position detail is not account truth.">
          <StatusRow
            label="Route positionId"
            value={routePositionId ?? "UNKNOWN"}
            state={routeMismatch ? "blocked" : "readOnly"}
          />
          <StatusRow label="Fixture positionId" value={position.positionId} state="readOnly" />
          {routeMismatch ? (
            <AppText variant="caption">
              Fixture-backed demo only. Route param does not select authoritative data.
            </AppText>
          ) : null}
          <StatusRow
            label="Strategy"
            value={`Strategy ${position.governance.strategyAcceptance}`}
            state="blocked"
            sourceRef={position.governance.controlStateSource}
          />
          <StatusRow
            label="Real capital"
            value={`Real capital ${position.governance.realCapital}`}
            state="blocked"
            sourceRef={position.governance.controlStateSource}
          />
          <BlockerList blockers={position.blockers} />
        </SectionContainer>
      </ProductDetailSection>
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
