import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { DisabledAction } from "../../read-models";
import { spacing } from "../../theme/tokens";

type DisabledActionBarProps = ViewProps & {
  actions: DisabledAction[];
};

export function DisabledActionBar({ actions, ...props }: DisabledActionBarProps) {
  if (actions.length === 0) {
    return (
      <CardContainer {...props}>
        <Badge label="Disabled" tone="disabled" />
        <AppText>No action affordance supplied.</AppText>
      </CardContainer>
    );
  }

  return (
    <View {...props} style={{ gap: spacing.sm }}>
      {actions.map((action) => (
        <CardContainer key={action.actionId}>
          <Badge label="Disabled" tone="disabled" />
          <AppText>{action.label}</AppText>
          <AppText variant="caption">{action.disabledReason}</AppText>
          {action.requiredGovernanceChange.map((change) => (
            <AppText key={change} variant="caption">
              {change}
            </AppText>
          ))}
        </CardContainer>
      ))}
    </View>
  );
}
