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
} from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { BlockerList, StatusRow } from "../../src/components/generic";
import { NavigationContextBar, ProductDetailHeader, ProductDetailSection, ScreenContainer, SectionContainer } from "../../src/components/layout";
import { orderDetailFixture } from "../../src/read-models/orderDetailFixture";

export default function OrderDetailRoute() {
  const params = useLocalSearchParams<{ orderId?: string }>();
  const order = orderDetailFixture;
  const routeOrderId = Array.isArray(params.orderId) ? params.orderId[0] : params.orderId;
  const routeMismatch = routeOrderId !== undefined && routeOrderId !== order.orderId;

  return (
    <ScreenContainer>
      <ProductDetailHeader
        badges={[
          { label: "Order Detail v1", tone: "readOnly" },
          { label: "Read-only", tone: "readOnly" },
          { label: "NOT_AUTHORITY", tone: "blocked" },
        ]}
        description="Scaffold-only fixture-backed view. Route params do not select broker or order truth."
        title={order.orderId}
      />

      <NavigationContextBar
        crumbs={[
          { href: "/", label: "HOME" },
          { href: "/orders", label: "ORDERS" },
          { label: "Order Detail" },
        ]}
        note="Order context is observation-only and has no submit, cancel, or broker mutation handler."
      />

      <ProductDetailSection sectionId="overview" title="Overview" description="Read local and broker truth state before evidence.">
        <MobileV1StatusRail
          items={[
            { label: "Local", value: order.sections.orderState.localState, tone: "blocked" },
            { label: "Broker", value: order.sections.orderState.brokerTruthState, tone: "blocked" },
            { label: "Actions", value: order.disabledActions.length, tone: "blocked" },
          ]}
          subtitle="Product Detail v1"
          title="Order lifecycle is observation-only"
        />
        <ScreenSummary
          badges={[
            { label: order.sections.orderState.localState, tone: "blocked" },
            { label: order.sections.orderState.brokerTruthState, tone: "blocked" },
            { label: order.governance.deploymentReadiness, tone: "blocked" },
          ]}
          description="Read-only order detail for local state, broker-truth state, evidence, validation, and disabled actions."
          footer="Route params are display hints only and do not select broker or order truth."
          links={[
            {
              href: "/orders",
              label: "Back to order rows",
              helperText: "Return to read-only lifecycle review.",
            },
            {
              href: "/system",
              label: "Open operating state",
              helperText: "Check hard-state and mutation boundary.",
            },
          ]}
          metrics={[
            { label: "Evidence rows", value: order.sections.evidence.length, state: "readOnly" },
            { label: "Risk blockers", value: order.sections.risk.blockers.length, state: "blocked" },
            { label: "Disabled actions", value: order.disabledActions.length, state: "blocked" },
            { label: "Unknown age", value: order.sections.orderState.unknownAgeSeconds ?? "UNKNOWN", state: "unknown" },
          ]}
          title="Order detail review"
        />

        <TimelineList
          items={[
            {
              label: "Local state",
              value: order.sections.orderState.localState,
              state: "blocked",
            },
            {
              label: "Broker truth",
              value: order.sections.orderState.brokerTruthState,
              state: "blocked",
            },
            {
              label: "Reconciled",
              value: order.sections.orderState.reconciledAt ?? "UNKNOWN",
              state: "unknown",
            },
          ]}
        />

        <SectionContainer title="Order State" description="No local or broker state is mutation-ready.">
          <StatusRow label="Local state" value={order.sections.orderState.localState} state="blocked" />
          <StatusRow label="Broker truth" value={order.sections.orderState.brokerTruthState} state="blocked" />
          <StatusRow
            label="Submitted"
            value={order.sections.orderState.submittedAt ?? "UNKNOWN"}
            state="unknown"
          />
          <StatusRow
            label="Reconciled"
            value={order.sections.orderState.reconciledAt ?? "UNKNOWN"}
            state="unknown"
          />
          <StatusRow
            label="Unknown age"
            value={order.sections.orderState.unknownAgeSeconds === null ? "UNKNOWN" : String(order.sections.orderState.unknownAgeSeconds)}
            state="unknown"
          />
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="evidence" title="Evidence" description="Stale evidence remains visible.">
        <SectionContainer title="Thesis / Logic" description="Order fixture has no execution authority.">
          <CardContainer>
            <AppText>{order.sections.thesisLogic.thesis ?? "UNKNOWN"}</AppText>
            <AppText variant="caption">{order.sections.thesisLogic.reason ?? "UNKNOWN"}</AppText>
            <AppText variant="caption">
              Economic meaning refs: {joinOrUnknown(order.sections.thesisLogic.economicMeaningRefs)}
            </AppText>
            <AppText variant="caption">
              Relation refs: {joinOrUnknown(order.sections.thesisLogic.relationRefs)}
            </AppText>
          </CardContainer>
        </SectionContainer>

        <SectionContainer title="Evidence" description="Fixture-backed evidence rows only.">
          <EvidenceList evidence={order.sections.evidence} />
        </SectionContainer>
      </ProductDetailSection>

      <ProductDetailSection sectionId="source" title="Source" description="Order state source is separate from broker truth.">
        <SourceAttributionCard
          authority="Fixture order lifecycle review; broker truth not attached"
          sourceStates={order.sections.risk.sourceStates}
          status={order.sections.orderState.brokerTruthState === "BLOCKED" ? "BLOCKER" : "UNKNOWN"}
          timestamp={order.generatedAt}
          title="Order source attribution"
        />
      </ProductDetailSection>

      <ProductDetailSection sectionId="risk" title="Risk" description="Order risk blockers stay visible before validation.">
        <RiskGate
          blockers={order.sections.risk.blockers}
          sourceStates={order.sections.risk.sourceStates}
          chartStates={order.sections.risk.chartStates}
        />
      </ProductDetailSection>

      <ProductDetailSection sectionId="validation" title="Validation" description="Validation status is not order acceptance.">
        <SectionContainer title="Validation Status" description="Validation status is not order acceptance.">
          <ValidationReadinessPanel validationReadiness={order.sections.validationReadiness} />
        </SectionContainer>

        <SectionContainer title="Scaffold Boundary" description="Order detail has no mutation authority.">
          <StatusRow label="Route orderId" value={routeOrderId ?? "UNKNOWN"} state={routeMismatch ? "blocked" : "readOnly"} />
          <StatusRow label="Fixture orderId" value={order.orderId} state="readOnly" />
          {routeMismatch ? (
            <AppText variant="caption">
              Fixture-backed demo only. Route param does not select authoritative data.
            </AppText>
          ) : null}
          <StatusRow
            label="Broker mutation"
            value={order.governance.brokerMutationPermitted ? "permitted" : "false"}
            state="blocked"
            sourceRef={order.governance.controlStateSource}
          />
          <StatusRow
            label="Real capital"
            value={`Real capital ${order.governance.realCapital}`}
            state="blocked"
            sourceRef={order.governance.controlStateSource}
          />
          <BlockerList blockers={order.blockers} />
        </SectionContainer>

        <SectionContainer title="Review Actions" description="Only read-only actions are listed.">
          <CardContainer>
            <Badge label="Review only" tone="readOnly" />
            {order.sections.nextAction.allowedReadOnlyActions.map((action) => (
              <AppText key={action}>{action}</AppText>
            ))}
            <AppText variant="caption">
              {order.sections.nextAction.nextEngineeringAction ?? "UNKNOWN"}
            </AppText>
          </CardContainer>
          <DisabledActionBar actions={order.sections.nextAction.disabledTradingActions} />
          <DisabledActionBar actions={order.disabledActions} />
        </SectionContainer>
      </ProductDetailSection>
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
