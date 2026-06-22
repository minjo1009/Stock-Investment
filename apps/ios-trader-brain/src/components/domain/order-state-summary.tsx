import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { DisabledActionBar } from "./disabled-action-bar";
import type { OrderDetailReadModel, OrdersReadModel } from "../../read-models";
import { spacing } from "../../theme/tokens";

type OrderStateSummaryProps = ViewProps & {
  orders?: OrdersReadModel;
  orderDetail?: OrderDetailReadModel;
};

export function OrderStateSummary({
  orderDetail,
  orders,
  ...props
}: OrderStateSummaryProps) {
  const firstOrder = orders?.orderRows[0];
  const orderState = orderDetail?.sections.orderState;

  return (
    <CardContainer {...props}>
      <Badge label="read-only" tone="readOnly" />
      <AppText variant="title">Order State</AppText>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="caption">
          local: {orderState?.localState ?? firstOrder?.localState ?? "UNKNOWN"}
        </AppText>
        <AppText variant="caption">
          broker truth: {orderState?.brokerTruthState ?? firstOrder?.brokerTruthState ?? "UNKNOWN"}
        </AppText>
        <AppText variant="caption">
          mutation permitted: {firstOrder?.mutationPermitted === false ? "false" : "unknown"}
        </AppText>
      </View>
      <DisabledActionBar actions={firstOrder?.disabledActions ?? orderDetail?.disabledActions ?? []} />
    </CardContainer>
  );
}
