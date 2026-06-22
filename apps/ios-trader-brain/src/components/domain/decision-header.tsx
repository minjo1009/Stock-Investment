import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import { DisabledActionBar } from "./disabled-action-bar";
import type { DecisionSummary, GovernanceStatus } from "../../read-models";
import { spacing } from "../../theme/tokens";

type DecisionHeaderProps = ViewProps & {
  decisionSummary: DecisionSummary;
  governance: GovernanceStatus;
};

export function DecisionHeader({
  decisionSummary,
  governance,
  ...props
}: DecisionHeaderProps) {
  return (
    <CardContainer {...props}>
      <View style={{ gap: spacing.sm }}>
        <Badge label={decisionSummary.decisionState} tone="readOnly" />
        <AppText variant="title">Decision Summary</AppText>
        <AppText variant="caption">{decisionSummary.authority}</AppText>
        <AppText variant="caption">{decisionSummary.generatedAt}</AppText>
      </View>
      <View style={{ gap: spacing.xs }}>
        <AppText variant="caption">
          Strategy: {governance.strategyAcceptance}
        </AppText>
        <AppText variant="caption">
          Deployment: {governance.deploymentReadiness}
        </AppText>
        <AppText variant="caption">Real capital: {governance.realCapital}</AppText>
      </View>
      <DisabledActionBar actions={decisionSummary.disabledActions} />
    </CardContainer>
  );
}
