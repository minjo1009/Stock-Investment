import { useLocalSearchParams } from "expo-router";
import { View } from "react-native";

import {
  DecisionHeader,
  DisabledActionBar,
  EvidenceList,
  RiskGate,
  ValidationReadinessPanel,
} from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { BlockerList, StatusRow } from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { orderDetailFixture } from "../../src/read-models/orderDetailFixture";
import { spacing } from "../../src/theme/tokens";

export default function OrderDetailRoute() {
  const params = useLocalSearchParams<{ orderId?: string }>();
  const order = orderDetailFixture;
  const routeOrderId = Array.isArray(params.orderId) ? params.orderId[0] : params.orderId;
  const routeMismatch = routeOrderId !== undefined && routeOrderId !== order.orderId;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="Order Detail v0" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">{order.orderId}</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed view. Route params do not select broker or order truth.
        </AppText>
      </View>

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

      <DecisionHeader decisionSummary={order.sections.decisionSummary} governance={order.governance} />

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

      <ValidationReadinessPanel validationReadiness={order.sections.validationReadiness} />

      <SectionContainer title="Evidence" description="Stale evidence remains visible.">
        <EvidenceList evidence={order.sections.evidence} />
      </SectionContainer>

      <RiskGate
        blockers={order.sections.risk.blockers}
        sourceStates={order.sections.risk.sourceStates}
        chartStates={order.sections.risk.chartStates}
      />

      <SectionContainer title="Next Action" description="Only read-only actions are listed.">
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
    </ScreenContainer>
  );
}

function joinOrUnknown(values: string[]) {
  return values.length > 0 ? values.join(", ") : "UNKNOWN";
}
