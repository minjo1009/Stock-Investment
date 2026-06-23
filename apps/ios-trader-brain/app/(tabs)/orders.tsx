import { View } from "react-native";

import {
  DisabledActionBar,
  OrderStateSummary,
  ReviewCard,
  ScreenSummary,
  TimelineList,
} from "../../src/components/domain";
import { AppText, Badge } from "../../src/components/foundation";
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

      <ScreenSummary
        badges={[
          { label: "fixture-backed", tone: "readOnly" },
          { label: "mutation blocked", tone: "blocked" },
          { label: orders.governance.deploymentReadiness, tone: "blocked" },
        ]}
        description="Read-only lifecycle monitor for local and broker-truth blockers. It does not expose an order mutation path."
        footer="Broker truth remains separate from local display records."
        links={[
          {
            href: "/orders/fixture-order-blocked",
            label: "Open sample order detail",
            helperText: "Inspect blocked local and broker-truth states.",
          },
          {
            href: "/system",
            label: "Open operating state",
            helperText: "Check kill switch and governance hard state.",
          },
        ]}
        metrics={[
          { label: "Rows", value: orders.orderRows.length, state: "readOnly" },
          { label: "Blocked", value: blockedCount, state: "blocked" },
          { label: "Stale", value: orders.sourceSummary.staleCount, state: "stale" },
          { label: "Unknown", value: orders.sourceSummary.unknownCount, state: "unknown" },
        ]}
        title="Order lifecycle review"
      />

      <TimelineList
        items={[
          {
            label: "Local record",
            value: "Fixture rows are display records only.",
            state: "unknown",
          },
          {
            label: "Broker truth",
            value: "Broker truth is blocked until an authority path proves reconciliation.",
            state: "blocked",
          },
          {
            label: "Mutation permission",
            value: orders.governance.brokerMutationPermitted ? "permitted" : "false",
            state: "blocked",
          },
        ]}
      />

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
            <View key={order.orderId} style={{ gap: spacing.sm }}>
              <ReviewCard
                badges={[
                  { label: order.localState, tone: "blocked" },
                  { label: order.brokerTruthState, tone: "blocked" },
                  { label: order.mutationPermitted ? "mutation true" : "mutation false", tone: "blocked" },
                ]}
                body={`Side: ${order.side}`}
                href={order.route}
                hrefLabel="Open read-only order detail"
                metrics={[
                  { label: "Symbol", value: order.symbol ?? "UNKNOWN", state: "unknown" },
                  { label: "Quantity", value: order.quantity ?? "UNKNOWN", state: "unknown" },
                  { label: "Disabled actions", value: order.disabledActions.length, state: "blocked" },
                ]}
                sourceRefs={order.sourceStates.flatMap((sourceState) => sourceState.provenanceRefs)}
                title={order.orderId}
              />
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: spacing.sm }}>
                {order.sourceStates.map((sourceState) => (
                  <SourceFreshnessBadge key={sourceState.sourceId} sourceState={sourceState} />
                ))}
              </View>
              <BlockerList blockers={order.blockers} />
              <DisabledActionBar actions={order.disabledActions} />
            </View>
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
