import { Link, type Href } from "expo-router";
import { View } from "react-native";

import { DisabledActionBar, OrderStateSummary } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import {
  BlockerList,
  MetricCard,
  SourceFreshnessBadge,
  StatusRow,
} from "../../src/components/generic";
import { ScreenContainer, SectionContainer } from "../../src/components/layout";
import { ordersFixture } from "../../src/read-models/ordersFixture";
import { spacing } from "../../src/theme/tokens";

export default function OrdersRoute() {
  const orders = ordersFixture;
  const blockedCount = orders.orderRows.filter(
    (order) => order.localState === "BLOCKED" || order.brokerTruthState === "BLOCKED"
  ).length;

  return (
    <ScreenContainer>
      <View style={{ gap: spacing.sm }}>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <Badge label="ORDERS v1" tone="readOnly" />
          <Badge label="Read-only" tone="readOnly" />
          <Badge label="NOT_AUTHORITY" tone="blocked" />
        </View>
        <AppText variant="title">ORDERS</AppText>
        <AppText variant="caption">
          Scaffold-only fixture-backed lifecycle monitor. No order mutation path is present.
        </AppText>
      </View>

      <SectionContainer title="Order State Snapshot" description="Blocked lifecycle states stay visible.">
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
          <MetricCard label="Rows" value={orders.orderRows.length} state="readOnly" />
          <MetricCard label="Blocked" value={blockedCount} state="blocked" />
          <MetricCard label="Stale sources" value={orders.sourceSummary.staleCount} state="stale" />
          <MetricCard label="Missing sources" value={orders.sourceSummary.missingCount} state="missing" />
          <MetricCard label="Unknown sources" value={orders.sourceSummary.unknownCount} state="unknown" />
        </View>
      </SectionContainer>

      <SectionContainer title="Order Rows" description="Routes are read-only scaffold links.">
        <View style={{ gap: spacing.sm }}>
          {orders.orderRows.map((order) => (
            <CardContainer key={order.orderId}>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                <Badge label={order.localState} tone="blocked" />
                <Badge label={order.brokerTruthState} tone="blocked" />
                <Badge label={order.mutationPermitted ? "mutation true" : "mutation false"} tone="blocked" />
              </View>
              <AppText variant="title">{order.orderId}</AppText>
              <AppText variant="caption">Symbol: {order.symbol ?? "UNKNOWN"}</AppText>
              <AppText variant="caption">Side: {order.side}</AppText>
              <AppText variant="caption">Quantity: {order.quantity ?? "UNKNOWN"}</AppText>
              <AppText variant="caption">Detail hint: {order.route}</AppText>
              <Link href={order.route as Href}>
                <AppText variant="caption">Open read-only order detail</AppText>
              </Link>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {order.sourceStates.map((sourceState) => (
                  <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
                ))}
              </View>
              <BlockerList blockers={order.blockers} />
              <DisabledActionBar actions={order.disabledActions} />
            </CardContainer>
          ))}
        </View>
      </SectionContainer>

      <OrderStateSummary orders={orders} />

      <SectionContainer title="Disabled Actions" description="Submit remains disabled and has no handler.">
        <DisabledActionBar actions={orders.disabledActions} />
      </SectionContainer>

      <SectionContainer title="Governance Boundary" description="Order mutation remains blocked.">
        <StatusRow
          label="Broker mutation"
          value={orders.governance.brokerMutationPermitted ? "permitted" : "false"}
          state="blocked"
          sourceRef={orders.governance.controlStateSource}
        />
        <StatusRow
          label="Deployment"
          value={`Deployment ${orders.governance.deploymentReadiness}`}
          state="blocked"
          sourceRef={orders.governance.authorityReportPath}
        />
        <StatusRow
          label="Real capital"
          value={`Real capital ${orders.governance.realCapital}`}
          state="blocked"
          sourceRef={orders.governance.controlStateSource}
        />
        <BlockerList blockers={orders.blockers} />
      </SectionContainer>
    </ScreenContainer>
  );
}
