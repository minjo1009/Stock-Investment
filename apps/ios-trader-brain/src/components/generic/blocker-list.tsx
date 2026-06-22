import { View, type ViewProps } from "react-native";

import { AppText, Badge, CardContainer } from "../foundation";
import type { BlockerState } from "../../read-models/common";
import { spacing } from "../../theme/tokens";

type BlockerListProps = ViewProps & {
  blockers: BlockerState[];
  emptyLabel?: string;
};

export function BlockerList({
  blockers,
  emptyLabel = "No blocker rows supplied by current read model",
  ...props
}: BlockerListProps) {
  if (blockers.length === 0) {
    return (
      <CardContainer {...props}>
        <Badge label="Unknown" tone="unknown" />
        <AppText>{emptyLabel}</AppText>
      </CardContainer>
    );
  }

  return (
    <View {...props} style={{ gap: spacing.sm }}>
      {blockers.map((blocker) => (
        <CardContainer key={blocker.blockerId}>
          <View style={{ gap: spacing.xs }}>
            <Badge label={blocker.severity} tone="blocked" />
            <AppText>{blocker.label}</AppText>
            <AppText variant="caption">{blocker.reason}</AppText>
            {blocker.sourceRefs.map((sourceRef) => (
              <AppText key={sourceRef} variant="caption">
                {sourceRef}
              </AppText>
            ))}
          </View>
        </CardContainer>
      ))}
    </View>
  );
}
